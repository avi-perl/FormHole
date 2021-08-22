from typing import Optional, Dict
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from .databases import DBProxy
from .dependencies import get_db
from .config import settings

app = FastAPI(
    debug=settings.debug,
    title=settings.site_title,
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


class Metadata(BaseModel):
    """
    Metadata related to this item.
    Used for filtering get requests.
    """

    id: Optional[str]
    created: datetime
    last_updated: Optional[datetime]
    deleted: bool = False


class CreateItem(BaseModel):
    """
    Model for data that can be passed when creating an item.
    The "created" timestamp is added when saving the record.
    """

    model: str
    version: float = 0
    data: dict

    class Config:
        schema_extra = {
            "example": {
                "model": "SomeModel",
                "version": 1.0,
                "data": {"key": "value"},
            }
        }


class UpdateItem(BaseModel):
    """
    Model for data that can be passed when creating an item.
    The "last_updated" timestamp is updated when saving the record.
    """

    model: Optional[str]
    version: Optional[float] = 0
    data: Optional[dict]

    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "key": "value",
                    "new_key": "new_value",
                }
            }
        }


class Item(BaseModel):
    """
    An item in the database.

    Only model, version, data, and the metadata values can be edited by a user. All other fields are reserved and
    updated automatically.
    """

    model: str
    version: float
    data: dict
    metadata: Optional[Metadata]


@app.get(
    "/items",
    response_model=Dict[str, Item],
    tags=["All Items"],
    response_model_exclude_unset=True,
)
async def list_all_items(
    show_deleted: bool = settings.list_all_items_show_deleted_default,
    db: DBProxy = Depends(get_db),
):
    """
    **List all items in the database**

    Pass optional options for filtering data based on metadata values.
    """
    items = {_id: Item(**item) for (_id, item) in db.get_all().items()}
    if not show_deleted:
        items = {
            _id: item for (_id, item) in items.items() if not item.metadata.deleted
        }
    return items


@app.get(
    "/item/{item_id}",
    response_model=Item,
    tags=["All Items"],
    response_model_exclude_unset=True,
)
async def get_item(
    item_id: str,
    show_deleted: bool = settings.get_item_show_deleted_default,
    db: DBProxy = Depends(get_db),
):
    """
    **Return a specific item from the database by its ID**

    Pass an optional option to show an item that is marked as deleted.
    """
    item = db.get_by_id(item_id)

    if not show_deleted and item and Item(**item).metadata.deleted:
        item = None

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.get("metadata").update({"id": item_id})
    return item


@app.post(
    "/", response_model=Item, tags=["All Items"], response_model_exclude_unset=True
)
async def create_item(item: CreateItem, db: DBProxy = Depends(get_db)):
    """
    **Create a new item in the Database**
    """
    item = Item(
        created=datetime.now(), **item.dict(), metadata=Metadata(created=datetime.now())
    )
    _id = db.add(jsonable_encoder(item))
    item.metadata.id = _id
    return item


@app.put(
    "/item/{item_id}",
    response_model=Item,
    tags=["All Items"],
    response_model_exclude_unset=True,
)
async def replace_item(
    item_id: str, create_item: CreateItem, db: DBProxy = Depends(get_db)
):
    """
    **Update an item in the Database**

    Note that put requests will replace all fields with the values passed or their defaults.
    For partial updates, use PATCH.

    This will cause the last_updated datetime to be updated.
    """
    stored_item_data = db.get_by_id(item_id)
    if not stored_item_data:
        raise HTTPException(status_code=400, detail="Item does not exist")

    item = Item(**create_item.dict(), metadata=Item(**stored_item_data).metadata)
    item.metadata.last_updated = datetime.now()
    db.update_by_id(item_id, jsonable_encoder(item))
    item.metadata.id = item_id
    return item


@app.patch(
    "/item/{item_id}",
    response_model=Item,
    tags=["All Items"],
    response_model_exclude_unset=True,
)
async def partial_update_item(
    item_id: str, update_item: UpdateItem, db: DBProxy = Depends(get_db)
):
    """
    **Partial update an item in the Database**

    Note that patch requests will replace only fields passed leaving the rest with their current values.
    This does _not_ apply to the contents of "data".
    To replace a record, use PUT.

    This will cause the last_updated datetime to be updated.
    """
    # TODO patch data as well?
    stored_item_data = db.get_by_id(item_id)
    if not stored_item_data:
        raise HTTPException(status_code=400, detail="Item does not exist")

    stored_item_model = Item(**stored_item_data)
    stored_item_model.metadata.last_updated = datetime.now()
    update_data = update_item.dict(exclude_unset=True)
    updated_item = stored_item_model.copy(update=update_data)
    db.update_by_id(item_id, jsonable_encoder(updated_item))
    updated_item.metadata.id = item_id
    return updated_item


@app.delete("/item/{item_id}", tags=["All Items"])
def delete_item(
    item_id: str,
    permanent: bool = settings.delete_item_permanent_default,
    db: DBProxy = Depends(get_db),
):
    """
    **Delete an item from the DB**

    Pass optional options to control if the data should be removed from the database entirely or if the record should
    be marked deleted by setting the metadata "deleted" value to true.
    """
    stored_item_data = db.get_by_id(item_id)
    if not stored_item_data:
        raise HTTPException(status_code=400, detail="Item does not exist")

    if permanent:
        db.delete_by_id(item_id)
    else:
        stored_item_model = Item(**stored_item_data)
        stored_item_model.metadata.last_updated = datetime.now()
        stored_item_model.metadata.deleted = True
        db.update_by_id(item_id, jsonable_encoder(stored_item_model))
    return {}


@app.get(
    "/model/{model_name}",
    response_model=Dict[str, Item],
    tags=["Models"],
    response_model_exclude_unset=True,
)
def list_model_items(
    model_name: str,
    show_deleted: bool = settings.list_model_items_show_deleted_default,
    db: DBProxy = Depends(get_db),
):
    """
    **List all items of a particular model**

    Selects and lists all models of a particular type.
    """
    items = {_id: Item(**item) for (_id, item) in db.get_by_model(model_name).items()}

    if not show_deleted:
        items = {
            _id: item for (_id, item) in items.items() if not item.metadata.deleted
        }

    return items


@app.post("/model/{model_name}", tags=["Models"], response_model_exclude_unset=True)
def create_model_item(
    model_name: str,
    post_data: dict,
    version: float = settings.create_model_item_version_default,
    db: DBProxy = Depends(get_db),
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
        metadata=Metadata(created=datetime.now()),
    )
    _id = db.add(jsonable_encoder(item))
    item.metadata.id = _id
    return item
