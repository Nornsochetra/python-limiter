# Research Py

A small Flask app with image upload, authentication, rate limiting, and rate limit logging.

---

## What you need before starting

| Requirement | Notes |
|---|---|
| **Python 3.10+** | Check with `python --version` |
| **PostgreSQL** | Must be installed and running |

---

## Setup (5 steps)

### 1. Create the database

The app creates its **tables** automatically, but it cannot create the **database** itself.
Create an empty database first — using `psql`:

```bash
psql -U postgres -c "CREATE DATABASE \"research-py\";"
```

Or do it in pgAdmin: right-click *Databases* → *Create* → *Database…* → name it `research-py`.

> You can name it anything you like — just use the same name in step 4.

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

- **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
- **Windows (CMD):** `venv\Scripts\activate.bat`
- **Mac / Linux:** `source venv/bin/activate`

> If PowerShell blocks the script, run this first:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file  ← **THIS IS WHAT YOU MUST CHANGE**

Copy the example file:

- **Windows:** `copy .env.example .env`
- **Mac / Linux:** `cp .env.example .env`

Then open `.env` and set these five values to match **your own** PostgreSQL setup:

```ini
DB_HOST=localhost                 # usually stays localhost
DB_PORT=5432                      # usually stays 5432
DB_NAME=research-py               # the database you created in step 1
DB_USER=postgres                  # your postgres username
DB_PASSWORD=your_password_here    # <-- YOUR postgres password
SECRET_KEY=...                    # <-- generate your own, see below
```

Generate a `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output after `SECRET_KEY=` **on the same line**, like:

```ini
SECRET_KEY=0000000000000000000000000000000000000000000000000000000000000000
```

### 5. Run it

```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

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
| **Sidebar → Limit Log** | *(admin only)* Every time someone gets rate limited, it's recorded here |

---

## Rate limits (how to see them working)

| Limit | Where | Trigger it by |
|---|---|---|
| **5 per minute per IP** | Login and Register pages | Refresh or submit either page 6 times in a minute |
| **10 per minute per user** | Limit Log page (admin) | Refresh the Limit Log page 11 times in a minute |

When you go over, you get a **429 "Too Many Requests"** page, and a row is written to the
`rate_limit_logs` table — visible in the admin **Limit Log** page.

> Note: page *views* count too, not just form submissions — so simply refreshing the login
> page 6 times will lock you out of it for 60 seconds. This is intentional.

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
├── .env                # YOUR settings - you create this (never share it)
├── .env.example        # template to copy
├── templates/          # HTML pages
│   ├── base.html            # layout for login/register
│   ├── sidebar_base.html    # layout for logged-in pages (sidebar + header)
│   ├── login.html, register.html, dashboard.html
│   ├── rate_limited.html    # the custom 429 page
│   ├── admin/logs.html      # rate limit log table
│   └── partials/profile_modal.html   # the profile popup
└── static/uploads/     # uploaded files land here
    ├── originals/      # full-size images
    ├── thumbnails/     # 50% versions
    └── avatars/        # profile pictures (cropped to 200x200)
```

Database tables are created automatically on startup by `db.create_all()` in `app.py`.

---

## Troubleshooting

**`password authentication failed for user "postgres"`**
The `DB_PASSWORD` in your `.env` is wrong. Fix it and restart.

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
