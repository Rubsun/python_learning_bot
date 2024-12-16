from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_WEBHOOK_URL: str | None

    BOT_TOKEN: str

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    RABBIT_HOST: str
    RABBIT_PORT: int
    RABBIT_USER: str
    RABBIT_PASSWORD: str

    REDIS_HOST: str
    REDIS_PORT: str

    USER_TASK_QUEUE_TEMPLATE: str = 'user_tasks.{user_id}'

    @property
    def db_url(self) -> str:
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def rabbit_url(self) -> str:
        return f'amqp://{self.RABBIT_USER}:{self.RABBIT_PASSWORD}@{self.RABBIT_HOST}:{self.RABBIT_PORT}/'

    class Config:
        env_file = '#YOUR_PATH_TO_THIS_DIRECTORY/config/.env'


settings = Settings()
