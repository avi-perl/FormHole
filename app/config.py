import os
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    # Fast API settings
    debug: bool = False
    site_title: str = "Post Hole"
    site_description: str = (
        "Post Hole is a catch all API that can accept data of any shape, save it to a database, "
        "and allows you to perform CRUD actions on those records."
    )
    openapi_url: str = "/openapi.json"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    # Disable specific endpoint URLs
    list_items_enabled: bool = True
    read_item_enabled: bool = True
    create_item_enabled: bool = True
    update_item_enabled: bool = True
    delete_item_enabled: bool = True
    read_model_items_enabled: bool = True
    create_model_item_enabled: bool = True
    read_model_list_enabled: bool = True

    # Set setting defaults
    list_items_show_deleted_default: bool = False
    read_item_show_deleted_default: bool = False
    delete_item_permanent_default: bool = False
    read_model_items_show_deleted_default: bool = False
    update_item_update_deleted_default: bool = False
    create_model_item_version_default: float = 0

    # Database settings
    sqlite_file_name = "database.db"
    database_url: str = f"sqlite:///{sqlite_file_name}"

    # CORS Settings
    cors_allow_origins: list = []
    cors_allow_origin_regex: Optional[str]
    cors_allow_methods: list = ['POST']
    cors_allow_headers: list = []
    cors_allow_credentials: bool = False
    cors_expose_headers: list = []
    cors_max_age: int = 600


    class Config:
        env_file = f'{os.environ.get("environment", "production")}.env'
        env_file_encoding = "utf-8"


settings = Settings()
