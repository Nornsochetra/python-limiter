# Research Py

A small Flask app with image upload, authentication, rate limiting, and rate limit logging.

---

## What you need before starting

| Requirement | Notes |
|---|---|
| **Python 3.10+** | Check with `python --version` |
| **PostgreSQL** | Must be installed and running |

---

## ⚡ The short version

If you know your way around Flask, this is everything you have to configure:

1. Create an empty PostgreSQL database.
2. Copy `.env.example` → `.env`, then set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `SECRET_KEY`.
3. `pip install -r requirements.txt` and `python run.py`.

**`.env` is the only file you must create.** It is intentionally *not* in the repository
(it holds a database password), so a fresh clone will not run until you make it.
Everything else — including the database tables — is set up automatically.

Full walkthrough below.

---

## Setup (6 steps)

### 1. Get the code

**If you cloned from GitHub:**

```bash
git clone https://github.com/Nornsochetra/python-limiter.git
cd python-limiter
```

**If you were sent a zip:** unzip it, then open a terminal inside that folder.

> The `static/uploads/` folders arrive empty — that's expected. Uploaded images aren't
> stored in the repo; the app writes your own into them at runtime.

### 2. Create the database

The app creates its **tables** automatically, but it cannot create the **database** itself.
Create an empty database first — using `psql`:

```bash
psql -U postgres -c "CREATE DATABASE \"research-py\";"
```

Or do it in pgAdmin: right-click *Databases* → *Create* → *Database…* → name it `research-py`.

> You can name it anything you like — just use the same name in step 5.

### 3. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

- **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
- **Windows (CMD):** `venv\Scripts\activate.bat`
- **Mac / Linux:** `source venv/bin/activate`

> If PowerShell blocks the script, run this first:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### 4. Install the dependencies

```bash
pip install -r requirements.txt
```

### 5. Create your `.env` file  ← **THIS IS THE ONLY THING YOU MUST CONFIGURE**

There is no `.env` in the repo or the zip — it contains a database password, so it is
never shared. You create your own from the template:

- **Windows:** `copy .env.example .env`
- **Mac / Linux:** `cp .env.example .env`

Then open `.env` and set these values to match **your own** PostgreSQL setup:

```ini
DB_HOST=localhost                 # usually stays localhost
DB_PORT=5432                      # usually stays 5432
DB_NAME=research-py               # the database you created in step 2
DB_USER=postgres                  # your postgres username
DB_PASSWORD=your_password_here    # <-- YOUR postgres password
SECRET_KEY=...                    # <-- generate your own, see below
```

`DB_PASSWORD` and `SECRET_KEY` are the two that always need changing; the rest usually
work as-is.

Generate a `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output after `SECRET_KEY=` **on the same line**, like:

```ini
SECRET_KEY=0000000000000000000000000000000000000000000000000000000000000000
```

### 6. Run it

Make sure your virtual environment is still activated — your prompt should start with
`(venv)` — then:

```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser. On first run the app creates the
`users`, `images`, and `rate_limit_logs` tables for you.

---

## First time using the app

1. Click **Register** and create an account.
2. **The first account you register automatically becomes the admin.** Everyone who
   registers after that is a normal user.
3. Log in — you land on the **Dashboard**.

### What you can do

| Where | What |
|---|---|
| **Dashboard** | Upload an image (a 50% thumbnail is generated automatically). Each card lists the original and thumbnail dimensions + file sizes, and **Compare** opens them side by side |
| **Avatar menu → Profile** | A popup to change your username, email, password, and profile picture |
| **Sidebar → Limit Log** | *(admin only)* Every request to a rate limited page is recorded here, marked **allowed** or **blocked**, with filter tabs for each |

---

## Rate limits (how to see them working)

| Limit | Where | Trigger it by |
|---|---|---|
| **5 per minute per IP** | Login and Register pages | Refresh or submit either page 6 times in a minute |
| **10 per minute per user** | Limit Log page (admin) | Refresh the Limit Log page 11 times in a minute |

When you go over, you get a **429 "Too Many Requests"** page showing a **live countdown**
of the real time left on your block — it ticks down each second and reloads the page by
itself once you're free, so you never have to guess or keep retrying. A row is also
written to the `rate_limit_logs` table, visible in the admin **Limit Log** page.

> Note: page *views* count too, not just form submissions — so simply refreshing the login
> page 6 times will lock you out of it for 60 seconds. This is intentional.
>
> Because of this, a **failed** login costs 2 requests (the submit, plus the reload that
> shows the error message), and opening the page costs 1. So in practice you get about
> two wrong-password tries per minute before the limit kicks in. Wait 60 seconds and the
> 429 page will let you back in automatically.

---

## Project structure

```
research-py/
├── app.py              # all routes (login, register, dashboard, upload, admin)
├── models.py           # database tables: User, Image, RateLimitLog
├── config.py           # reads .env and builds the database connection string
├── utils.py            # thumbnail + avatar image processing (Pillow)
├── run.py              # starts the app
├── requirements.txt    # python packages
├── .env                # YOUR settings - you create this (never shared, never committed)
├── .env.example        # template to copy
├── .gitignore          # keeps .env, venv/ and uploaded images out of git
├── templates/          # HTML pages
│   ├── base.html            # layout for login/register
│   ├── sidebar_base.html    # layout for logged-in pages (sidebar + topbar)
│   ├── login.html, register.html, dashboard.html
│   ├── rate_limited.html    # the custom 429 page
│   ├── admin/logs.html      # rate limit log table
│   └── partials/profile_modal.html   # the profile popup
└── static/
    ├── css/style.css   # the shared styling for every page
    └── uploads/        # uploaded files land here (empty on a fresh clone)
        ├── originals/  # full-size images
        ├── thumbnails/ # 50% versions
        └── avatars/    # profile pictures (cropped to 200x200)
```

Database tables are created automatically on startup by `db.create_all()` in `app.py`.

---

## Troubleshooting

**`password authentication failed for user "postgres"`**
Either you haven't created your `.env` yet (step 5 — without it the app falls back to a
default password that won't match yours), or the `DB_PASSWORD` in it is wrong.
Fix it and restart.

**`database "research-py" does not exist`**
You skipped step 1. Create the database first.

**`RuntimeError: The session is unavailable because no secret key was set`**
Your `SECRET_KEY` in `.env` is empty, or the key ended up on its own line.
It must be on the **same line** as `SECRET_KEY=`.

**`ModuleNotFoundError: No module named 'flask'`**
The virtual environment isn't activated, or you skipped `pip install -r requirements.txt`.

**Pillow or psycopg2 fails to install**
Usually means a very new Python version has no prebuilt package yet. Either use
Python 3.12, or install the newest versions without pinning:
`pip install Flask Flask-SQLAlchemy Flask-Login Flask-Limiter psycopg2-binary python-dotenv Pillow`

**I changed a model and the new column doesn't appear**
This project has no migration tool. `db.create_all()` only creates *missing tables* — it
won't add a column to a table that already exists. Either drop the table and let it be
recreated, or add the column manually with `ALTER TABLE`.

---

## Notes

- Rate limit counters are stored **in memory**, so they reset every time you restart the app.
  The *log* of breaches is stored in PostgreSQL and persists.
- Passwords are stored hashed (never in plain text).
