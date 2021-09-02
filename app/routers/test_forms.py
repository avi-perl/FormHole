from datetime import datetime

from fastapi.testclient import TestClient


def test_create_model_from_form(client: TestClient):
    form_data = {"FormField": "FormValue"}
    model_name = "FormData"
    response = client.post(
        f"/form/{model_name}", data=form_data, params={"version": 770.5}
    )
    item = response.json()

    assert response.status_code == 200
    assert item["id"] == 1
    assert item["model"] == model_name
    assert item["version"] == 770.5
    assert item["data"] == form_data
    assert item["created"] is not None
    assert item["last_updated"] is None
    assert not item["deleted"]
    assert isinstance(
        datetime.strptime(item["created"], "%Y-%m-%dT%H:%M:%S.%f"), datetime
    )
