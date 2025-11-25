"""Settings module.

This module provides access to configuration settings for the application.
"""

from pathlib import Path
from tempfile import gettempdir

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from yarl import URL

from app.core.enums import AppEnv, ApplicationLogLevel

TEMP_DIR = Path(gettempdir())


class Settings(BaseSettings):
    """Application settings.

    These parameters are loaded from environment variables.
    """

    # Application environment
    app_env: AppEnv = Field(
        AppEnv.DEV,
        alias="APP_ENV",
        description="Application runtime environment (dev/stage/prod)",
    )

    # Application settings
    application_name: str = "NeuralERP AI"
    debug: bool = Field(False, alias="DEBUG")  #  ADD THIS
    host: str = Field("127.0.0.1", alias="HOST")
    port: int = Field(5000, alias="PORT")  #  CHANGE: lowercase 'port'
    reload: bool = Field(True, alias="APPLICATION_AUTO_RELOAD")
    workers_count: int = Field(1, alias="APPLICATION_UVICORN_WORKERS_COUNT")


    # SuperAdmin Credential
    superadmin_email: str = Field(..., alias="SUPERADMIN_EMAIL")
    superadmin_password: str = Field(..., alias="SUPERADMIN_PASSWORD")
    
    
        
    # Logging settings
    log_level: ApplicationLogLevel = Field(
        ApplicationLogLevel.INFO,
        alias="APPLICATION_LOG_LEVEL",
    )
    enable_file_logging: bool = Field(True, alias="ENABLE_FILE_LOGGING")
    logs_dir: Path = Field(Path("logs"), alias="LOGS_DIR")
    log_retention_days: int = Field(30, alias="LOG_RETENTION_DAYS")
    log_rotation: str = Field("daily", alias="LOG_ROTATION")
    dataset_upload_dir: Path = Field(
        Path("storage/tenant_datasets"), alias="DATASET_UPLOAD_DIR"
    )
        # ==================== NEW: DATASET SETTINGS ====================
    dataset_allowed_extensions: list[str] = Field(
        default=[".csv", ".xlsx"],
        alias="DATASET_ALLOWED_EXTENSIONS"
    )

    dataset_preview_limit: int = Field(
        default=100,
        alias="DATASET_PREVIEW_LIMIT"
    )


    # CORS settings
    cors_allow_origins: str = Field("*", alias="CORS_ALLOW_ORIGINS")
    cors_allow_methods: str = Field("GET,POST,PUT,DELETE", alias="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field(
        "Content-Type,Authorization,X-Requested-With,Accept,Origin,Access-Control-Request-Method,Access-Control-Request-Headers",
        alias="CORS_ALLOW_HEADERS",
        
    )

    # Database settings
    postgres_database_host: str = Field(..., alias="POSTGRES_DATABASE_HOST")
    postgres_database_port: int = Field(..., alias="POSTGRES_DATABASE_PORT")
    postgres_database_username: str = Field(..., alias="POSTGRES_DATABASE_USERNAME")
    postgres_database_password: str = Field(..., alias="POSTGRES_DATABASE_PASSWORD")
    postgres_database_name: str = Field(..., alias="POSTGRES_DATABASE_NAME")
    postgres_database_echo: bool = Field(False, alias="POSTGRES_DATABASE_ECHO")

    # JWT settings
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_lifetime_seconds: int = Field(172800, alias="JWT_LIFETIME_SECONDS")

    # ==================== NEW: AUTH SETTINGS ====================
    secret_key: str = Field(..., alias="SECRET_KEY")
    access_token_expire_seconds: int = Field(
        default=604800,
        alias="ACCESS_TOKEN_EXPIRE_SECONDS",
    )
    reset_password_token_secret: str = Field(..., alias="RESET_PASSWORD_TOKEN_SECRET")
    verification_token_secret: str = Field(..., alias="VERIFICATION_TOKEN_SECRET")

    # ==================== NEW: EMAIL SETTINGS ====================
    smtp_server: str = Field(..., alias="SMTP_SERVER")
    smtp_port: int = Field(587, alias="SMTP_PORT")
    smtp_username: str = Field(..., alias="SMTP_USERNAME")
    smtp_password: str = Field(..., alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(True, alias="SMTP_USE_TLS")

    # ==================== NEW: FRONTEND SETTINGS ====================
    frontend_base_url: str = Field(..., alias="FRONTEND_BASE_URL")
    
    
 
    CHROMA_DB_PATH: str = Field(
        default="chroma_db",
        description="Directory path for the Chroma vector database.",
    )

    CHROMA_COLLECTION_NAME: str = Field(
        default="sap_migration_knowledge",
        description="Chroma collection name for RAG retrieval.",
    )

    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="Model used for generating embeddings.",
    )

    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="OpenAI API key for embedding generation.",
    )

    OPENAI_CONTEXT_MODEL: str = Field(
        default="gpt-4.1",
        alias="OPENAI_CONTEXT_MODEL",
        description="OpenAI model for contextual question generation.",
    )


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        _settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customise the settings sources and their priority."""
        return (
            dotenv_settings,
            env_settings,
            init_settings,
            file_secret_settings,
        )

    @property
    def postgres_database_url(self) -> str:
        """Returns the URL for the postgres database."""
        database_url = URL.build(
            scheme="postgresql+asyncpg",
            host=self.postgres_database_host,
            port=self.postgres_database_port,
            user=self.postgres_database_username,
            password=self.postgres_database_password,
            path=f"/{self.postgres_database_name}",
        )
        return str(database_url)

    @property
    def postgres_sync_database_url(self) -> str:
        """Returns the synchronous URL for the postgres database."""
        database_url = URL.build(
            scheme="postgresql+psycopg",
            host=self.postgres_database_host,
            port=self.postgres_database_port,
            user=self.postgres_database_username,
            password=self.postgres_database_password,
            path=f"/{self.postgres_database_name}",
        )
        return str(database_url)

    @property
    def cors_allow_origins_list(self) -> list[str]:
        """Returns a list of allowed CORS origins."""
        return self.cors_allow_origins.split(",")

    @property
    def cors_allow_methods_list(self) -> list[str]:
        """Returns a list of allowed CORS HTTP methods."""
        return self.cors_allow_methods.split(",")

    @property
    def cors_allow_headers_list(self) -> list[str]:
        """Returns a list of allowed CORS headers."""
        return self.cors_allow_headers.split(",")

    @property
    def forgot_password_url(self) -> str:
        """Returns the complete forgot password URL for frontend."""
        base_url = self.frontend_base_url.rstrip("/")
        return f"{base_url}/forgot-password"

    @property
    def verification_url(self) -> str:
        """Returns the complete verification URL for frontend."""
        base_url = self.frontend_base_url.rstrip("/")
        return f"{base_url}/verify-email"


settings = Settings.model_validate({})
