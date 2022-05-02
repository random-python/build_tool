"""
"""

import os
from configparser import ConfigParser

CONFIG_PATH = "BUILD_TOOL_CONFIG_PATH"


class ConfigSupport:
    ""

    instance:ConfigParser = None

    @classmethod
    def ensure_enviro(cls, config_path:str) -> None:
        os.environ[CONFIG_PATH] = config_path

    @classmethod
    def ensure_instance(cls) -> ConfigParser:
        "produce singleton instance"
        if cls.instance is None:
            cls.instance = cls.produce_config()
        return cls.instance

    @classmethod
    def produce_config(cls,) -> ConfigParser:
        "provide global configuration"
        config_path = os.environ.get(CONFIG_PATH, "").split(";")
        config_parser = ConfigParser()
        config_parser.read(config_path)
        return config_parser


def CONFIG() -> ConfigParser:
    return ConfigSupport.ensure_instance()
