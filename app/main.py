import json
from typing import Optional, Dict, List
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import validator
from sqlmodel import Field, Session, SQLModel, create_engine, select

from .dependencies import engine, get_session
from .config import settings


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI(
    debug=settings.debug,
    title=settings.site_title,
    version="0.2.0",
    description=settings.site_description,
    openapi_url=settings.openapi_url,
    openapi_tags=[
        {
            "name": "All Items",
            "description": "Perform actions on all model types.",
        },
        {
            "name": "Models",
            "description": "Perform actions on specific model types.",
        },
    ],
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


class ItemBase(SQLModel):
    model: str
    version: float = 0
    data: dict
    deleted: bool = False


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    id: int
    created: datetime
    last_updated: Optional[datetime]
    

class ItemUpdate(SQLModel):
    model: Optional[str]
    version: Optional[float]
    data: Optional[dict]
    deleted: Optional[bool]


class Item(ItemBase, table=True):
    """
    An item in the database.

    Only model, version, data, and the metadata values can be edited by a user. All other fields are reserved and
    updated automatically.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    created: datetime
    last_updated: Optional[datetime]
    data: str

    @validator('data', pre=True)
    def convert_data_dict_to_str(cls, v):
        """
        Convert data to a string when the class is initiated.
        This is a temp hack to make saving data to the DB work.
        TODO: Fix this.
        """
        return json.dumps(v)


@app.get(
    "/items",
    response_model=List[ItemRead],
    tags=["All Items"],
)
async def list_items(
        *,
        session: Session = Depends(get_session),
        show_deleted: bool = settings.list_items_show_deleted_default,
        offset: int = 0,
        limit: int = Query(default=100, lte=100),
):
    """
    **List all items in the database**

    Pass optional options for filtering data based on metadata values.
    """
    query = select(Item) if show_deleted else select(Item).where(Item.deleted != True)
    items = []

    # Hack: Convert the string instances of data to dicts so the response_model will work.
    # TODO: Fix this.
    for item in session.exec(query.offset(offset).limit(limit)).all():
        item.data = json.loads(item.data)
        items.append(item)

    return items


@app.get(
    "/item/{item_id}",
    response_model=ItemRead,
    tags=["All Items"],
)
async def read_item(
        *, session: Session = Depends(get_session),
        item_id: str,
        show_deleted: bool = settings.read_item_show_deleted_default,
):
    """
    **Return a specific item from the database by its ID**

    Pass an optional option to show an item that is marked as deleted.
    """
    item = session.get(Item, item_id)
    if item and not show_deleted and item.deleted:
        item = None

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Hack: Convert the string instance of data to dict so the response_model will work.
    # TODO: Fix this.
    item.data = json.loads(item.data)
    return item


@app.post("/", response_model=ItemRead, tags=["All Items"])
async def create_item(*, session: Session = Depends(get_session), item: ItemCreate):
    """
    **Create a new item in the Database**
    """
    db_item = Item(
        model=item.model,
        version=item.version,
        created=datetime.now(),
        deleted=item.deleted,
        data=item.data,
    )
    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    # Hack: Convert the string instance of data to dict so the response_model will work.
    # TODO: Fix this.
    db_item.data = json.loads(db_item.data)
    return db_item


@app.patch(
    "/item/{item_id}",
    response_model=ItemRead,
    tags=["All Items"],
)
async def update_item(
        *, session: Session = Depends(get_session),
        item_id: str,
        item: ItemUpdate,
        update_deleted: bool = settings.update_item_update_deleted_default,
):
    """
    **Partial update an item in the Database**

    Note that patch requests will replace only fields passed leaving the rest with their current values.
    This does _not_ apply to the contents of "data".
    To replace a record, use PUT.

    This will cause the last_updated datetime to be updated.
    """
    # TODO patch data as well?
    db_item = session.get(Item, item_id)
    if not update_deleted and db_item.deleted:
        db_item = None
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    item_data = item.dict(exclude_unset=True)
    for key, value in item_data.items():
        # Hack: Convert the dict instance of data to a str so the Item can be put into the DB.
        # This needs to be done here because the validator in Item is not called when using setattr.
        # TODO: Fix this.
        if key == "data":
            value = json.dumps(value)
        setattr(db_item, key, value)
    db_item.last_updated = datetime.now()
    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    # Hack: Convert the string instances of data to dicts so the response_model will work.
    # TODO: Fix this.
    db_item.data = json.loads(db_item.data)
    return db_item


@app.delete("/item/{item_id}", tags=["All Items"])
async def delete_item(
        *, session: Session = Depends(get_session),
        item_id: str,
        permanent: bool = settings.delete_item_permanent_default,
):
    """
    **Delete an item from the DB**

    Pass optional options to control if the data should be removed from the database entirely or if the record should
    be marked deleted by setting the metadata "deleted" value to true.
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if permanent:
        session.delete(item)
    else:
        item.deleted = True
        item.last_updated = datetime.now()

    session.commit()
    return {"ok": True}


@app.get(
    "/model/{model_name}",
    response_model=List[ItemRead],
    tags=["Models"],
)
async def read_model_items(
        *, session: Session = Depends(get_session),
        model_name: str,
        show_deleted: bool = settings.read_model_items_show_deleted_default,
        offset: int = 0,
        limit: int = Query(default=100, lte=100),
):
    """
    **List all items of a particular model**

    Selects and lists all models of a particular type.
    """
    query = select(Item) if show_deleted else select(Item).where(Item.deleted != True)

    # Hack: Convert the string instances of data to dicts so the response_model will work.
    # TODO: Fix this.
    model_items = []
    for model_item in session.exec(query.offset(offset).limit(limit)).all():
        model_item.data = json.loads(model_item.data)
        model_items.append(model_item)

    return model_items


@app.post("/model/{model_name}", tags=["Models"], response_model=ItemRead)
async def create_model_item(
        *,
        session: Session = Depends(get_session),
        model_name: str,
        post_data: dict,
        version: float = settings.create_model_item_version_default,
):
    """
    **Create an item with the model name in the URL**

    This endpoint is useful when you don't want to specify all the required fields required by the root POST endpoint.
    Use this when you want to send a completely schema free body in your request.

    The model name specified in the URL will be used as the model name, and the optional version query param can be used
    to set the version being used.

    The created datetime will be added automatically.
    """
    item = Item(
        model=model_name,
        version=version,
        data=post_data,
        created=datetime.now()
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    # Hack: Convert the string instance of data to dict so the response_model will work.
    # TODO: Fix this.
    item.data = json.loads(item.data)
    return item
