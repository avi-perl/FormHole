from pydantic import BaseSettings


class Settings(BaseSettings):
    db_name: str = "db"


settings = Settings()
