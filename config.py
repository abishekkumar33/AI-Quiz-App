"""
Application configuration.
Loads settings from environment variables (.env file).
"""
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'

    _default_sqlite = os.path.join(basedir, 'database', 'app.db')
    _sqlite_path = os.environ.get('SQLITE_PATH', '').strip() or _default_sqlite
    _db_url = os.environ.get('DATABASE_URL', '').strip() or f"sqlite:///{_sqlite_path}"
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif _db_url.startswith('postgresql://'):
        _db_url = _db_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    DB_IS_EPHEMERAL = (
        bool(os.environ.get('RENDER'))
        and _db_url.startswith('sqlite')
        and _sqlite_path == _default_sqlite
    )

    # Session
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24  # 1 day (seconds)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = bool(os.environ.get('RENDER'))
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 30

    # Gemini API
    # A pinned stable model avoids an alias being moved to a preview model.
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.6-flash').strip()

    # Uploads / misc
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
