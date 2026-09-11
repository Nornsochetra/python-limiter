import os
import time
import uuid
from functools import wraps
from math import ceil

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from models import db, User, Image, RateLimitLog
from utils import allowed_file, make_thumbnail, save_avatar, human_size

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.jinja_env.filters["human_size"] = human_size

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# in-memory rate limiter (per your earlier choice) - no default limits,
# only the specific limits attached to individual routes below apply
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[])


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def user_id_key():
    return str(current_user.id)


# the rate limited endpoints, and what each limit counts per.
# keep this in sync with the @limiter.limit decorators below.
RATE_LIMITED_ENDPOINTS = {
    "login": "ip",
    "register": "ip",
    "dashboard": "user",
    "admin_logs": "user",
}


@app.after_request
def log_rate_limited_request(response):
    """Record every request to a rate limited endpoint, whether it was allowed
    or blocked, so the log shows the attempts leading up to a block."""
    limit_type = RATE_LIMITED_ENDPOINTS.get(request.endpoint)
    if limit_type is None:
        return response

    db.session.add(
        RateLimitLog(
            ip_address=request.remote_addr or "unknown",
            user_id=current_user.id if current_user.is_authenticated else None,
            endpoint=request.endpoint,
            limit_type=limit_type,
            blocked=response.status_code == 429,
        )
    )
    db.session.commit()
    return response


@app.errorhandler(429)
def ratelimit_handler(e):
    # how many seconds are actually left in this window, so the page can count
    # down to the exact moment the user is free again
    seconds_left = max(0, ceil(limiter.current_limit.window.reset_time - time.time()))
    response = render_template(
        "rate_limited.html",
        message=str(e.description),
        seconds_left=seconds_left,
    )
    return response, 429, {"Retry-After": str(seconds_left)}


# make sure the upload folders exist
os.makedirs(app.config["ORIGINALS_FOLDER"], exist_ok=True)
os.makedirs(app.config["THUMBNAILS_FOLDER"], exist_ok=True)
os.makedirs(app.config["AVATARS_FOLDER"], exist_ok=True)

with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5/minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("That username is already taken.")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("That email is already registered.")
            return redirect(url_for("register"))

        # the very first user to register becomes an admin
        is_first_user = User.query.count() == 0

        user = User(username=username, email=email, is_admin=is_first_user)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5/minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash("Invalid username or password.")
            return redirect(url_for("login"))

        login_user(user)
        flash(f"Welcome back, {user.username}.")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/admin/dashboard")
@login_required
@limiter.limit("10/minute", key_func=user_id_key)
def dashboard():
    images = (
        Image.query.filter_by(user_id=current_user.id)
        .order_by(Image.uploaded_at.desc())
        .all()
    )
    stats = None
    if current_user.is_admin:
        stats = {
            "user_count": User.query.count(),
            "image_count": Image.query.count(),
            "breach_count": RateLimitLog.query.filter_by(blocked=True).count(),
        }
    return render_template("dashboard.html", images=images, stats=stats)


@app.route("/profile/edit", methods=["POST"])
@login_required
def edit_profile():
    next_url = request.form.get("next") or url_for("dashboard")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    avatar = request.files.get("avatar")

    if not username or not email:
        flash("Username and email are required.")
        return redirect(next_url)

    taken_username = User.query.filter(
        User.username == username, User.id != current_user.id
    ).first()
    if taken_username:
        flash("That username is already taken.")
        return redirect(next_url)

    taken_email = User.query.filter(
        User.email == email, User.id != current_user.id
    ).first()
    if taken_email:
        flash("That email is already registered.")
        return redirect(next_url)

    if password:
        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(next_url)
        current_user.set_password(password)

    if avatar and avatar.filename:
        if not allowed_file(avatar.filename, app.config["ALLOWED_EXTENSIONS"]):
            flash("That avatar file type is not allowed.")
            return redirect(next_url)

        ext = avatar.filename.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        avatar_path = os.path.join(app.config["AVATARS_FOLDER"], unique_name)
        save_avatar(avatar, avatar_path, size=200)
        current_user.avatar_path = f"uploads/avatars/{unique_name}"

    current_user.username = username
    current_user.email = email
    db.session.commit()

    flash("Profile updated.")
    return redirect(next_url)


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("image")

    if not file or file.filename == "":
        flash("Please choose an image file.")
        return redirect(url_for("dashboard"))

    if not allowed_file(file.filename, app.config["ALLOWED_EXTENSIONS"]):
        flash("That file type is not allowed.")
        return redirect(url_for("dashboard"))

    # generate a unique filename so uploads never overwrite each other
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    original_path = os.path.join(app.config["ORIGINALS_FOLDER"], unique_name)
    thumbnail_path = os.path.join(app.config["THUMBNAILS_FOLDER"], unique_name)

    file.save(original_path)
    original_size, thumbnail_size = make_thumbnail(original_path, thumbnail_path, scale=0.5)

    image = Image(
        user_id=current_user.id,
        original_filename=file.filename,
        original_path=f"uploads/originals/{unique_name}",
        thumbnail_path=f"uploads/thumbnails/{unique_name}",
        original_width=original_size[0],
        original_height=original_size[1],
        original_bytes=os.path.getsize(original_path),
        thumbnail_width=thumbnail_size[0],
        thumbnail_height=thumbnail_size[1],
        thumbnail_bytes=os.path.getsize(thumbnail_path),
    )
    db.session.add(image)
    db.session.commit()

    flash("Image uploaded successfully.")
    return redirect(url_for("dashboard"))


@app.route("/admin/logs")
@login_required
@admin_required
@limiter.limit("10/minute", key_func=user_id_key)
def admin_logs():
    show = request.args.get("show", "all")

    query = RateLimitLog.query
    if show == "blocked":
        query = query.filter_by(blocked=True)
    elif show == "allowed":
        query = query.filter_by(blocked=False)

    logs = query.order_by(RateLimitLog.created_at.desc()).limit(200).all()

    counts = {
        "all": RateLimitLog.query.count(),
        "blocked": RateLimitLog.query.filter_by(blocked=True).count(),
        "allowed": RateLimitLog.query.filter_by(blocked=False).count(),
    }
    return render_template("admin/logs.html", logs=logs, counts=counts, show=show)


if __name__ == "__main__":
    app.run(debug=True)
