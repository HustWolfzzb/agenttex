from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8000
    data_dir: Path = Path("data")
    redis_url: str = "redis://localhost:6379/0"
    max_zip_size: int = 100 * 1024 * 1024  # 100MB
    max_file_count: int = 1000
    compile_timeout_soft: int = 90
    compile_timeout_hard: int = 120

    model_config = {"env_prefix": "AGENTTEX_"}


settings = Settings()
