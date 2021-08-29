import json
from copy import deepcopy
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from .main import app, Item
from .dependencies import get_session


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# test item that can be used by tests.
test_item = Item(
    model="TestModel",
    data={"key": "value"},
    created=datetime.now(),
)
deleted_test_item = Item(
    model="TestModel",
    data={"key": "value"},
    created=datetime.now(),
    deleted=True
)


def test_read_items_no_show_deleted(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.add(deepcopy(deleted_test_item))
    session.commit()

    response = client.get("/items?show_deleted=false")
    items = response.json()

    assert response.status_code == 200
    assert len(items) == 1
    assert not items[0].get("deleted")


def test_read_items_show_deleted(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.add(deepcopy(deleted_test_item))
    session.commit()

    response = client.get("/items?show_deleted=true")
    items = response.json()

    assert response.status_code == 200
    assert len(items) == 2
    assert not items[0].get("deleted")
    assert items[1].get("deleted")


def test_read_items_limit_offset(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.add(deepcopy(test_item))
    session.add(deepcopy(test_item))
    session.add(deepcopy(test_item))
    session.add(deepcopy(test_item))
    session.commit()

    response = client.get("/items", params={"limit": 2, "offset": 1})
    items = response.json()

    assert response.status_code == 200
    assert len(items) == 2
    assert items[0].get("id") == 2
    assert items[1].get("id") == 3


def test_read_item(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.commit()

    response = client.get("/item/2")
    assert response.status_code == 404

    response = client.get("/item/1")
    assert response.status_code == 200


def test_read_item_show_deleted(session: Session, client: TestClient):
    session.add(deepcopy(deleted_test_item))
    session.commit()

    response = client.get("/item/1", params={"show_deleted": False})
    assert response.status_code == 404

    response = client.get("/item/1", params={"show_deleted": True})
    item = response.json()

    assert response.status_code == 200
    assert item.get("deleted")


def test_create_item(client: TestClient):
    post_data = {"model": "SomeModel", "version": 1, "data": {"key": "value"}}
    response = client.post(
        "/", json=post_data
    )
    item = response.json()

    assert response.status_code == 200
    assert item["id"] == 1
    assert item["model"] == post_data["model"]
    assert item["version"] == post_data["version"]
    assert item["data"] == post_data["data"]
    assert item["created"] is not None
    assert item["last_updated"] is None
    assert not item["deleted"]
    assert isinstance(datetime.strptime(item["created"], "%Y-%m-%dT%H:%M:%S.%f"), datetime)


def test_create_item_deleted(client: TestClient):
    post_data = {"model": "SomeModel", "version": 1, "data": {"key": "value"}, "deleted": True}
    response = client.post(
        "/", json=post_data
    )
    item = response.json()

    assert response.status_code == 200
    assert item["id"] == 1
    assert item["model"] == post_data["model"]
    assert item["version"] == post_data["version"]
    assert item["data"] == post_data["data"]
    assert item["created"] is not None
    assert item["last_updated"] is None
    assert item["deleted"]
    assert isinstance(datetime.strptime(item["created"], "%Y-%m-%dT%H:%M:%S.%f"), datetime)


def test_delete_soft(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.commit()

    response = client.delete("/item/1", params={"permanent": False})
    assert response.status_code == 200
    assert response.json() == {'ok': True}

    response = client.get("/item/1", params={"show_deleted": False})
    assert response.status_code == 404

    response = client.get("/item/1", params={"show_deleted": True})
    item = response.json()
    assert response.status_code == 200
    assert item.get("deleted")


def test_delete_permanent(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.commit()

    response = client.delete("/item/1", params={"permanent": True})
    assert response.status_code == 200
    assert response.json() == {'ok': True}

    response = client.get("/item/1", params={"show_deleted": False})
    assert response.status_code == 404

    response = client.get("/item/1", params={"show_deleted": True})
    assert response.status_code == 404


def test_update_item(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.commit()
    old_item = deepcopy(test_item)

    response = client.patch(
        "/item/1",
        json={
            "model": "SomeNewModelName",
        },
    )
    assert response.status_code == 200
    new_item = response.json()

    assert old_item != new_item
    assert old_item.model != new_item["model"]
    assert new_item["model"] == "SomeNewModelName"
    assert old_item.version == new_item["version"]
    assert json.loads(old_item.data) == json.loads(json.dumps(new_item["data"]))
    assert old_item.last_updated != new_item["last_updated"]
    assert old_item.last_updated is None
    assert new_item["last_updated"] is not None
    assert not old_item.deleted
    assert not new_item["deleted"]


def test_update_item_no_updating_deleted_item(session: Session, client: TestClient):
    session.add(deepcopy(deleted_test_item))
    session.commit()

    response = client.patch(
        "/item/1",
        json={
            "deleted": "true",
        },
    )
    assert response.status_code == 404


def test_update_item_update_deleted(session: Session, client: TestClient):
    session.add(deepcopy(deleted_test_item))
    session.commit()
    old_item = deepcopy(deleted_test_item)

    response = client.patch(
        "/item/1",
        json={
            "deleted": False,
        },
        params={"update_deleted": True}
    )
    assert response.status_code == 200
    new_item = response.json()

    assert old_item != new_item
    assert old_item.model == new_item["model"]
    assert old_item.version == new_item["version"]
    assert json.loads(old_item.data) == json.loads(json.dumps(new_item["data"]))
    assert old_item.last_updated != new_item["last_updated"]
    assert old_item.last_updated is None
    assert new_item["last_updated"] is not None
    assert old_item.deleted
    assert not new_item["deleted"]


def test_read_models_no_show_deleted(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.add(deepcopy(deleted_test_item))
    session.commit()

    response = client.get(f"/model/{test_item.model}", params={"show_deleted": False})
    items = response.json()

    assert response.status_code == 200
    assert len(items) == 1
    assert not items[0].get("deleted")


def test_read_models_show_deleted(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.add(deepcopy(deleted_test_item))
    session.commit()

    response = client.get(f"/model/{test_item.model}", params={"show_deleted": True})
    items = response.json()

    assert response.status_code == 200
    assert len(items) == 2
    assert not items[0].get("deleted")
    assert items[1].get("deleted")


def test_create_model_item(session: Session, client: TestClient):
    post_data = {"key": "value"}
    response = client.post(
        f"/model/{test_item.model}", json=post_data
    )
    item = response.json()

    assert response.status_code == 200
    assert item["id"] == 1
    assert item["model"] == test_item.model
    assert item["version"] == 0
    assert item["data"] == post_data
    assert item["created"] is not None
    assert item["last_updated"] is None
    assert not item["deleted"]
    assert isinstance(datetime.strptime(item["created"], "%Y-%m-%dT%H:%M:%S.%f"), datetime)


def test_create_model_item_include_version(session: Session, client: TestClient):
    post_data = {"key": "value"}
    response = client.post(
        f"/model/{test_item.model}", json=post_data, params={"version": 770.5}
    )
    item = response.json()

    assert response.status_code == 200
    assert item["id"] == 1
    assert item["model"] == test_item.model
    assert item["version"] == 770.5
    assert item["data"] == post_data
    assert item["created"] is not None
    assert item["last_updated"] is None
    assert not item["deleted"]
    assert isinstance(datetime.strptime(item["created"], "%Y-%m-%dT%H:%M:%S.%f"), datetime)

