from sqlmodel import create_engine

from .config import settings

# Heroku by default will use the URI of "postgres" when using their postgres sql instances.
# This is not supported by SQL Alchemy. Updating it here makes deployment easy for users.
database_url = settings.database_url
if database_url.split(":")[0] == "postgres":
    database_url = f"postgresql:{database_url.split(':')[1]}"

connect_args = {"check_same_thread": False}
engine = create_engine(settings.database_url, echo=True, connect_args=connect_args)
