from pydantic import BaseSettings


class Settings(BaseSettings):
    site_title: str = "Post Hole"
    site_description: str = "Post Hole is a catch all API that can accept data of any shape, save it to a database, " \
                            "and allows you to perform CRUD actions on those records."

    list_all_items_show_deleted_default: bool = False
    get_item_show_deleted_default: bool = False
    delete_item_permanent_default: bool = False
    list_model_items_show_deleted_default: bool = False
    create_model_item_version_default: float = 0

    db_name: str = "db"


settings = Settings()
