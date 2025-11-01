import sys

IS_CELERY_WORKER = "celery" in sys.argv[0]

if IS_CELERY_WORKER:
    import eventlet
    eventlet.monkey_patch()

from celery import Celery
from pydantic_settings import BaseSettings, SettingsConfigDict

class CelerySettings(BaseSettings):
    """
    Reads the Redis connection string from an environment variable.
    Default value is for our local docker-compose setup.
    """
    REDIS_CONNECTION_STRING: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

# Initialize settings
settings = CelerySettings()

celery_app = Celery(
    "pactparser_tasks",
    broker=settings.REDIS_CONNECTION_STRING,
    backend=settings.REDIS_CONNECTION_STRING,
    include=["app.celery_worker"]  
)
celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)

if __name__ == "__main__":
    celery_app.start()