"""
Flask application configuration
"""
import os
from dotenv import load_dotenv


def _load_env_no_bom(path: str = ".env") -> None:
    """Load .env stripping UTF-8 BOM if present (Notepad on Windows adds it)."""
    import pathlib
    p = pathlib.Path(path)
    if p.exists():
        raw = p.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):          # BOM detected
            p.write_bytes(raw[3:])                    # strip it in-place
    load_dotenv(path, override=True)


_load_env_no_bom(".env")


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    IBM_API_KEY = os.getenv("IBM_API_KEY", "")
    WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
    WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    GRANITE_MODEL_ID = os.getenv("GRANITE_MODEL_ID", "ibm/granite-4-h-small")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
