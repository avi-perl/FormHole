import json
from datetime import datetime

from fastapi import Depends, Query, APIRouter, Form, UploadFile, File
from starlette.requests import Request
from sqlmodel import Session

from .items import Item, ItemRead
from ..dependencies import get_session
from ..config import settings

router = APIRouter()

if settings.form_create_enabled:

    @router.post("/{model_name}", response_model=ItemRead)
    async def create_model_from_form(
        *,
        session: Session = Depends(get_session),
        model_name: str,
        request: Request,
        version: float = settings.create_model_item_version_default,
    ):
        """
        **Create an item by submitting form data**

        This endpoint can be used as the "action" of a properly configured web form.

        The model name specified in the URL will be used as the model name, and the optional version query param can be
        used to set the version being used.

        All form data contained in the request is converted to a dict and used as the Item Data.


        ### Note:
        Your form **must** have a "name" for each input.
        - This will work: `<input name="email" type="email" />`
        - This will not be recognized: `<input type="email" />`
        """
        form_data = await request.form()
        data = {k: v for k, v in form_data.items()} if form_data else {}

        item = Item(
            model=model_name, version=version, data=data, created=datetime.now()
        )
        session.add(item)
        session.commit()
        session.refresh(item)

        # Hack: Convert the string instance of data to dict so the response_model will work.
        # TODO: Fix this.
        item.data = json.loads(item.data)
        return item
