import os


os.environ.setdefault("CONTENT_GENERATOR_DATABASE_URL", "sqlite:///storage/pytest_tasks.db")
os.environ.setdefault("CONTENT_GENERATOR_DB_LOG_ECHO", "false")
os.environ.setdefault("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
