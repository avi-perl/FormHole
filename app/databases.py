from sqlmodel import create_engine

from .config import settings

connect_args = {"check_same_thread": False}
engine = create_engine(settings.database_url, echo=True, connect_args=connect_args)
