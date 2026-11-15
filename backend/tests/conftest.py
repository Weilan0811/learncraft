import os


os.environ.setdefault("CONTENT_GENERATOR_DATABASE_URL", "sqlite:///storage/pytest_tasks.db")
os.environ.setdefault("CONTENT_GENERATOR_DB_LOG_ECHO", "false")
# Tests assert the disabled-retrieval contract; keep the local KB (and its model
# downloads) out of the test environment even when the developer's .env enables it.
os.environ.setdefault("CONTENT_GENERATOR_KB_PROVIDER", "external")
os.environ.setdefault("CONTENT_GENERATOR_PROVIDER_MODE", "stub")
