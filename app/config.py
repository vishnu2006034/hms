import os


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:262112@localhost:5432/hms")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HOGC_TENANT_ID = "hms"
    HOGC_ORG_ID = "main"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
