from sqlmodel import Session

from .databases import engine


def get_session():
    with Session(engine) as session:
        yield session
