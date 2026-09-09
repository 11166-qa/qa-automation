import os


BASE_URL = os.getenv(
    "QA_BASE_URL",
    "http://localhost:8000",
)

ADMIN_EMAIL = os.getenv(
    "QA_ADMIN_EMAIL",
    "admin@example.com",
)

ADMIN_PASSWORD = os.getenv(
    "QA_ADMIN_PASSWORD",
    "changethis",
)

REQUEST_TIMEOUT = 10
DB_HOST = os.getenv(
    "QA_DB_HOST",
    "localhost",
)

DB_PORT = int(
    os.getenv(
        "QA_DB_PORT",
        "5432",
    )
)

DB_NAME = os.getenv(
    "QA_DB_NAME",
    "app",
)

DB_USER = os.getenv(
    "QA_DB_USER",
    "postgres",
)

DB_PASSWORD = os.getenv(
    "QA_DB_PASSWORD",
    "changethis",
)