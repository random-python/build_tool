"""
base type for resource access
"""

from dataclasses import dataclass

from build_tool.arkon_config import CONFIG

frozen_class = dataclass(frozen=True)


@frozen_class
class AuthAny:
    "base type for resource access"

    # required configuration source
    section_auth = "vendor/any/auth"

    @classmethod
    def config_section(cls) -> dict:
        return  CONFIG()[cls.section_auth]


@frozen_class
class AuthUserPass(AuthAny):
    "base type for user/pass login"

    username:str
    password:str

    @classmethod
    def from_config(cls) -> "AuthToken":
        section = cls.config_section()
        return cls(
            username=section['username'],
            password=section['password'],
        )


@frozen_class
class AuthToken(AuthAny):
    "base type for bearer token access"

    token:str

    @classmethod
    def from_config(cls) -> "AuthToken":
        section = cls.config_section()
        return cls(
            token=section['token'],
        )
