import os
from dotenv import load_dotenv

# load values from the .env file into os.environ
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "research_py")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # where uploaded images are stored, relative to the project root
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ORIGINALS_FOLDER = os.path.join(UPLOAD_FOLDER, "originals")
    THUMBNAILS_FOLDER = os.path.join(UPLOAD_FOLDER, "thumbnails")
    AVATARS_FOLDER = os.path.join(UPLOAD_FOLDER, "avatars")

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max upload size
