import os

class Settings:
    # Ambiente
    APP_ENV = os.getenv("APP_ENV", "dev")
    PORT = int(os.getenv("PORT", "8080"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Providers (qual servico usar)
    STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "azure")
    FACE_PROVIDER = os.getenv("FACE_PROVIDER", "azure")

    # AWS (backup/fallback)
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_RAW = os.getenv("S3_BUCKET_RAW", "photo-find-raw")
    S3_BUCKET_PUBLIC = os.getenv("S3_BUCKET_PUBLIC", "")
    REKOGNITION_PREFIX = os.getenv("REKOGNITION_PREFIX", "evt-")

    # Azure Face API
    AZURE_FACE_ENDPOINT = os.getenv("AZURE_FACE_ENDPOINT", "")
    AZURE_FACE_KEY = os.getenv("AZURE_FACE_KEY", "")
    AZURE_FACELIST_PREFIX = os.getenv("AZURE_FACELIST_PREFIX", "evt-")

    # Azure Blob Storage
    AZURE_BLOB_CONNECTION_STRING = os.getenv("AZURE_BLOB_CONNECTION_STRING", "")
    AZURE_BLOB_ACCOUNT_NAME = os.getenv("AZURE_BLOB_ACCOUNT_NAME", "")
    AZURE_BLOB_ACCOUNT_KEY = os.getenv("AZURE_BLOB_ACCOUNT_KEY", "")
    AZURE_BLOB_CONTAINER = os.getenv("AZURE_BLOB_CONTAINER", "photo-find-raw")

    # URLs Pre-assinadas
    PRESIGNED_EXPIRE_SECONDS = int(os.getenv("PRESIGNED_EXPIRE_SECONDS", "3600"))

    # Autenticacao
    JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
    BASIC_ADMIN_USER = os.getenv("BASIC_ADMIN_USER", "admin")
    BASIC_ADMIN_PASS = os.getenv("BASIC_ADMIN_PASS", "secret")

    # CORS
    CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")

settings = Settings()
