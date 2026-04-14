from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    PROJECT_NAME: str = "Device Management API"
    API_V1_STR: str = "/api/v1"

    # Database
    DB_HOST: str
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS – JSON-Array in der .env, z. B.:
    # CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Basis-URL für QR-Codes
    BASE_URL: str = "http://localhost:8050"

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"        # intern (App → MinIO)
    MINIO_PUBLIC_ENDPOINT: str = "minio:9000" # öffentlich (Presigned-URLs im Browser)
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "geraete-bilder"
    MINIO_SECURE: bool = False

    # Sentry (optional)
    SENTRY_DSN: str = ""


settings = Settings()
