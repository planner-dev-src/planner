from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


class Config:
    SECRET_KEY = "dev-secret-key"
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'planner.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False