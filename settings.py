from pydantic_settings import BaseSettings
import pytz
from datetime import datetime
from environs import Env


env = Env()
env.read_env()


class Settings(BaseSettings):
    """
    Settings for the application.
    """
    DEBUG: bool = env.bool("DEBUG")
    HOST: str = 'localhost'
    PORT: int = 8000

    # DB_HOST: str = env.str("DB_HOST")
    # DB_PORT: int = env.int("DB_PORT")
    # DB_USER: str = env.str("DB_USER")
    # DB_PASSWORD: str = env.str("DB_PASSWORD")
    # DB_NAME: str = env.str("DB_NAME")



    TZ: str = 'Asia/Tashkent'

    SECRET_KEY: str = env.str("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 60 * 24 * 14
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 60 * 24 * 7

    def get_tz(self):
        tz = pytz.timezone(self.TZ)
        return datetime.now(tz)

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
