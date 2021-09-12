from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .databases import create_db_and_tables
from .config import settings
from .routers import items, models, forms

app = FastAPI(
    debug=settings.debug,
    title=settings.site_title,
    version="0.2.0",
    description=settings.site_description,
    openapi_url=settings.openapi_url,
    openapi_tags=[
        {
            "name": "Items",
            "description": "Perform actions on all model types.",
        },
        {
            "name": "Models",
            "description": "Perform actions on specific model types.",
        },
        {
            "name": "Forms",
            "description": "Create Items by submitting a form.",
        },
    ],
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
)

app.include_router(
    items.router,
    tags=["Items"],
)
app.include_router(
    models.router,
    prefix="/model",
    tags=["Models"],
)
app.include_router(
    forms.router,
    prefix="/form",
    tags=["Forms"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
    allow_credentials=settings.cors_allow_credentials,
    expose_headers=settings.cors_expose_headers,
    max_age=settings.cors_max_age,
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
