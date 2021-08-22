from .databases import DBProxy
from .config import settings


def get_db():
    db = DBProxy(settings.db_name)
    return db
