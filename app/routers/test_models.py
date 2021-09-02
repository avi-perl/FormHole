from copy import deepcopy
from datetime import datetime

from fastapi.testclient import TestClient
from sqlmodel import Session
from app.routers.items import Item

# test item that can be used by tests.
test_item = Item(
    model="TestModel",
    data={"key": "value"},
    created=datetime.now(),
)
deleted_test_item = Item(
    model="TestModel", data={"key": "value"}, created=datetime.now(), deleted=True
)


def test_read_models_unknown_model(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.commit()

    response = client.get(f"/model/SomeModelNotInTheDB")
    items = response.json()

    assert response.status_code == 200
    assert len(items) == 0
    assert items == []


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
    response = client.post(f"/model/{test_item.model}", json=post_data)
    item = response.json()

    assert response.status_code == 200
    assert item["id"] == 1
    assert item["model"] == test_item.model
    assert item["version"] == 0
    assert item["data"] == post_data
    assert item["created"] is not None
    assert item["last_updated"] is None
    assert not item["deleted"]
    assert isinstance(
        datetime.strptime(item["created"], "%Y-%m-%dT%H:%M:%S.%f"), datetime
    )


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
    assert isinstance(
        datetime.strptime(item["created"], "%Y-%m-%dT%H:%M:%S.%f"), datetime
    )


def test_read_model_list(session: Session, client: TestClient):
    session.add(deepcopy(test_item))
    session.add(deepcopy(test_item))

    test_item_2 = deepcopy(test_item)
    test_item_2.version = 1.0
    session.add(test_item_2)

    some_other_model = deepcopy(test_item)
    some_other_model.model = "SomeOtherModel"
    some_other_model.version = 770
    session.add(some_other_model)
    session.commit()

    response = client.get(f"/model/list")
    metadata = response.json()

    assert response.status_code == 200
    assert len(metadata) == 2

    some_other_model_metadata = metadata[0]
    assert some_other_model_metadata["count"] == 1
    assert len(some_other_model_metadata["versions"]) == 1
    assert some_other_model_metadata["versions"] == {'770.0': 1}

    test_item_metadata = metadata[1]
    assert test_item_metadata["count"] == 3
    assert len(test_item_metadata["versions"]) == 2
    assert test_item_metadata["versions"] == {'0.0': 2, '1.0': 1}
