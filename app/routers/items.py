import json
from typing import Optional, List
from datetime import datetime

from fastapi import Depends, HTTPException, Query, APIRouter
from pydantic import validator
from sqlmodel import Field, Session, SQLModel, select

from ..dependencies import get_session
from ..config import settings

router = APIRouter()


class ItemBase(SQLModel):
    model: str
    version: float = 0
    data: dict
    deleted: bool = False


class ItemCreate(ItemBase):
    pass

    class Config:
        schema_extra = {
            "example": {
                "model": "ContactForm",
                "version": 1.0,
                "data": {
                    "email": "avi@email.com",
                    "subject": "Contact form example",
                    "body": "This is an example of arbitrary data that can be stored in the data field.",
                },
                "deleted": False,
            }
        }


class ItemRead(ItemBase):
    id: int
    created: datetime
    last_updated: Optional[datetime]

    class Config:
        schema_extra = {
            "example": {
                "model": "ContactForm",
                "version": 1.0,
                "data": {
                    "email": "avi@email.com",
                    "subject": "Contact form example",
                    "body": "This is an example of arbitrary data that can be stored in the data field.",
                },
                "deleted": False,
                "id": 1,
                "created": "2021-09-03T06:04:51.477Z",
                "last_updated": None,
            }
        }


class ItemUpdate(SQLModel):
    model: Optional[str]
    version: Optional[float]
    data: Optional[dict]
    deleted: Optional[bool]

    class Config:
        schema_extra = {
            "example": {
                "model": "NewModelName",
                "version": 1.1,
                "data": {
                    "key": "New value replacing the data currently stored.",
                },
                "deleted": False,
            }
        }


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

    @validator("data", pre=True)
    def convert_data_dict_to_str(cls, v):
        """
        Convert data to a string when the class is initiated.
        This is a temp hack to make saving data to the DB work.
        TODO: Fix this.
        """
        return json.dumps(v)


if settings.list_items_enabled:

    @router.get(
        "/items",
        response_model=List[ItemRead],
    )
    async def list_items(
        *,
        session: Session = Depends(get_session),
        show_deleted: bool = settings.list_items_show_deleted_default,
        offset: int = 0,
        limit: int = Query(default=100, lte=100),
    ):
        """
        ## List all items in the database

        Get a list of all items in the database.

        By default, items that are soft deleted are not returned, but passing the show_deleted parameter will cause
        them to be returned.

        To get all items of a particular model, see the Models endpoints.
        """
        query = (
            select(Item) if show_deleted else select(Item).where(Item.deleted != True)
        )
        items = []

        # Hack: Convert the string instances of data to dicts so the response_model will work.
        # TODO: Fix this.
        for item in session.exec(query.offset(offset).limit(limit)).all():
            item.data = json.loads(item.data)
            items.append(item)

        return items


if settings.read_item_enabled:

    @router.get(
        "/item/{item_id}",
        response_model=ItemRead,
    )
    async def read_item(
        *,
        session: Session = Depends(get_session),
        item_id: str,
        show_deleted: bool = settings.read_item_show_deleted_default,
    ):
        """
        ## Return a specific item from the database by its ID

        By default, items that are soft deleted are not returned, but passing the show_deleted parameter will cause
        them to be returned.
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


if settings.create_item_enabled:

    @router.post("/", response_model=ItemRead)
    async def create_item(*, session: Session = Depends(get_session), item: ItemCreate):
        """
        ## Create a new item in the Database

        Create a new item with a post request.

        A simple post request can be made by putting a model name in the URL. See the Models endpoints.
        Items can also be created by form, see the Forms endpoints.
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


if settings.update_item_enabled:

    @router.patch(
        "/item/{item_id}",
        response_model=ItemRead,
    )
    async def update_item(
        *,
        session: Session = Depends(get_session),
        item_id: str,
        item: ItemUpdate,
        update_deleted: bool = settings.update_item_update_deleted_default,
    ):
        """
        ## Partial update an item in the Database

        Note that patch requests will replace only fields passed leaving the rest with their current values.
        This does _not_ apply to the contents of "data".

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


if settings.delete_item_enabled:

    @router.delete("/item/{item_id}", response_model=dict)
    async def delete_item(
        *,
        session: Session = Depends(get_session),
        item_id: str,
        permanent: bool = settings.delete_item_permanent_default,
    ):
        """
        ## Delete an item from the DB

        Pass optional options to control if the data should be removed from the database entirely or if the record
        should be marked deleted by setting the metadata "deleted" value to true.
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
