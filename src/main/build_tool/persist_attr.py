"""
persist json values as file attibutes
"""

import json

import xattr


class PersistAttr:
    ""

    @classmethod
    def attr_key(cls, key:str) -> str:
        return f"user.{key}".encode()

    @classmethod
    def persist_json(cls, key:str, value:dict, data_path:str) -> None:
        "save json value into file attibute"
        with open(data_path, "rb") as data_file:
            attr_data = xattr.xattr(data_file)
            attr_key = cls.attr_key(key)
            attr_data[attr_key] = json.dumps(value).encode()

    @classmethod
    def extract_json(cls, key:str, data_path:str) -> dict:
        "load json value from file attribute"
        with open(data_path, "rb") as data_file:
            attr_data = xattr.xattr(data_file)
            attr_key = cls.attr_key(key)
            if attr_key in attr_data:
                return json.loads(attr_data[attr_key].decode())
