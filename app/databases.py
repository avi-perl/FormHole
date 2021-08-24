import json
import uuid
from typing import Dict, Any, List

import boto3
from botocore.errorfactory import ClientError
from pysondb import DB

from .config import settings


class DBProxy:
    """Proxy class to communicate with the DB"""

    FILE_DB = "FILE"
    S3_DB = "S3"
    DB_TYPES = [FILE_DB, S3_DB]
    DB_DEFAULT = FILE_DB

    __s3_client = None

    def __init__(self, name: str, db_type: str = DB_DEFAULT):
        self.name = name
        self.db_type = (
            db_type.upper()
            if db_type and db_type.upper() in self.DB_TYPES
            else self.DB_DEFAULT
        )

        self.db = DB(
            ["created", "last_updated", "model", "version", "data", "metadata"], False
        )
        self.load()
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

    @property
    def s3_client(self):
        if not self.__s3_client:
            self.__s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )

        return self.__s3_client

    def save(self):
        if self.db_type == self.FILE_DB:
            self.db.commit(self.db_filename, indent=4)
        elif self.db_type == self.S3_DB:
            db_data = self.db.get_all()
            binary_db_data = json.dumps(db_data).encode("utf-8")
            self.s3_client.put_object(
                Body=binary_db_data,
                Bucket=settings.s3_bucket_name,
                Key=settings.s3_db_key,
            )

    def load(self):
        if self.db_type == self.FILE_DB:
            self.db.load(self.db_filename)
        elif self.db_type == self.S3_DB:
            try:
                s3_data = self.s3_client.get_object(
                    Bucket=settings.s3_bucket_name, Key=settings.s3_db_key
                )
                db_data = json.loads(s3_data.get("Body").read().decode("utf-8"))
                self.db._db = db_data
            except ClientError:
                # DB file not found in S3, create it now.
                self.save()

    @property
    def db_filename(self):
        return self.name + ".json"

    @staticmethod
    def uuid_generator():
        return str(uuid.uuid4())
