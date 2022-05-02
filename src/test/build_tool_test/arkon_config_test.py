"""
"""

import os

from build_tool.arkon_config import ConfigSupport
from build_tool.arkon_config import CONFIG

this_dir = os.path.dirname(__file__)
config_path = __file__.replace(".py", ".ini")


def test_config_path():
    print()

    ConfigSupport.ensure_enviro(config_path)

    config_parser = CONFIG()

    cloud_config = config_parser['cloud/aws/bucket/auth']
    
    assert "username" in cloud_config
    assert "password" in cloud_config
