from typing import Dict, Any, List
import uuid

from pysondb import DB


class DBProxy:
    """Proxy class to communicate with the DB"""

    def __init__(self, name: str):
        self.name = name

        self.db = DB(
            ["created", "last_updated", "model", "version", "data", "metadata"], False
        )
        self.db.load(self.db_filename)
        self.db.set_id_generator(self.uuid_generator)

    def add(self, data: Dict[str, Any]):
        _id = self.db.add(data)
        self.save()
        return _id

    def add_many(self, data: List[Dict[str, Any]]):
        self.db.add_many(data)

    def get_all(self):
        return self.db.get_all()

    def get_by_model(self, model_name: str):
        return self.db.get_by_query({"model": model_name})

    def get_by_id(self, _id: str):
        return self.db.get_by_id(str(_id))

    def update_by_id(self, _id: str, data: Dict[str, Any]):
        self.db.update_by_id(str(_id), data)
        self.save()

    def delete_by_id(self, _id: str):
        self.db.pop(str(_id))
        self.save()

    def save(self):
        self.db.commit(self.db_filename, indent=4)

    @property
    def db_filename(self):
        return self.name + ".json"

    @staticmethod
    def uuid_generator():
        return str(uuid.uuid4())
