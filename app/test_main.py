import json

from fastapi.testclient import TestClient

from .main import app
from .dependencies import get_db
from app.databases.DBProxy import DBProxy


def override_get_db():
    test_data = {
        "non_deleted_record": {
            "model": "WelcomeMessage",
            "version": 1.0,
            "data": {"message": "Hello Yossi \ud83d\udc4b"},
            "metadata": {
                "deleted": False,
                "created": "2021-08-22T10:16:01.205519",
                "last_updated": None,
            },
        },
        "deleted_record": {
            "model": "DeletedModel",
            "version": 1.0,
            "data": {"message": "I've been deleted!"},
            "metadata": {
                "created": "2021-08-22T11:15:21.578248",
                "last_updated": "2021-08-22T11:16:24.093868",
                "deleted": True,
            },
        },
        "deleted_welcome_message": {
            "model": "WelcomeMessage",
            "version": 1.0,
            "data": {"message": "Hello Avi \ud83d\udc4b"},
            "metadata": {
                "deleted": True,
                "created": "2021-09-22T10:16:01.205519",
                "last_updated": "2021-10-22T10:16:01.205519",
            },
        },
    }

    with open("test_db.json", "w") as fp:
        json.dump(test_data, fp)

    db = DBProxy("test_db")
    return db


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_items_no_show_deleted():
    response = client.get("/items?show_deleted=false")
    items = response.json()
    assert response.status_code == 200
    assert len(items) > 0
    assert "non_deleted_record" in items.keys()
    assert "deleted_record" not in items.keys()


def test_items_show_deleted():
    response = client.get("/items?show_deleted=true")
    items = response.json()
    assert response.status_code == 200
    assert len(items) >= 2
    assert "non_deleted_record" in items.keys()
    assert "deleted_record" in items.keys()


def test_item():
    response = client.get("/item/some_id_that_does_not_exist")
    assert response.status_code == 404

    response = client.get("/item/non_deleted_record")
    assert response.status_code == 200


def test_item_no_deleted():
    response = client.get("/item/non_deleted_record?show_deleted=true")
    item = response.json()
    assert response.status_code == 200
    assert item["metadata"]["id"] == "non_deleted_record"
    assert item["metadata"]["deleted"] is False

    response = client.get("/item/deleted_record?show_deleted=false")
    assert response.status_code == 404


def test_item_yes_deleted():
    response = client.get("/item/deleted_record?show_deleted=true")
    item = response.json()
    assert response.status_code == 200
    assert item["metadata"]["id"] == "deleted_record"
    assert item["metadata"]["deleted"] is True


def test_post():
    response = client.post(
        "/", json={"model": "SomeModel", "version": 1, "data": {"key": "value"}}
    )
    item = response.json()
    assert response.status_code == 200
    assert isinstance(item["metadata"]["id"], str)


def test_put():
    response = client.get("/item/non_deleted_record")
    assert response.status_code == 200
    old_item = response.json()

    response = client.put(
        "/item/non_deleted_record",
        json={
            "model": "SomeNewModel",
            "version": 5.6,
            "data": {"new_key": "new_value"},
        },
    )
    assert response.status_code == 200
    new_item = response.json()

    assert old_item["model"] != new_item["model"]
    assert old_item["version"] != new_item["version"]
    assert old_item["data"] != new_item["data"]
    assert old_item["metadata"]["last_updated"] != new_item["metadata"]["last_updated"]
    assert new_item["metadata"]["last_updated"] is not None


def test_delete_soft():
    response = client.delete("/item/non_deleted_record?permanent=false")
    assert response.status_code == 200
    assert response.json() == {}


def test_delete_permanent():
    response = client.delete("/item/non_deleted_record?permanent=true")
    assert response.status_code == 200
    assert response.json() == {}


def test_patch():
    response = client.get("/item/non_deleted_record")
    assert response.status_code == 200
    old_item = response.json()

    response = client.patch(
        "/item/non_deleted_record",
        json={
            "model": "SomeNewModelName",
        },
    )
    assert response.status_code == 200
    new_item = response.json()

    assert old_item["model"] != new_item["model"]
    assert old_item["version"] == new_item["version"]
    assert old_item["data"] == new_item["data"]
    assert old_item["metadata"]["last_updated"] != new_item["metadata"]["last_updated"]
    assert new_item["metadata"]["last_updated"] is not None


def test_models_no_show_deleted():
    response = client.get("/model/WelcomeMessage?show_deleted=false")
    assert response.status_code == 200
    items = response.json()
    assert "deleted_welcome_message" not in items.keys()
    assert "non_deleted_record" in items.keys()


def test_models_show_deleted():
    response = client.get("/model/WelcomeMessage?show_deleted=true")
    assert response.status_code == 200
    items = response.json()
    assert "deleted_welcome_message" in items.keys()
    assert "non_deleted_record" in items.keys()


def test_models_post():
    data = {"some_random_key": "some_value"}
    model_name = "RandomModel"
    response = client.post(f"/model/{model_name}", json=data)
    assert response.status_code == 200
    item = response.json()
    assert item["data"] == data
    assert item["model"] == model_name


def test_models_post_with_version():
    data = {"some_random_key": "some_value"}
    model_name = "RandomModel"
    response = client.post(f"/model/{model_name}?version=770", json=data)
    assert response.status_code == 200
    item = response.json()
    assert item["version"] == 770
