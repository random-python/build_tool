#!/usr/bin/env python

#
# provision packages from amazon s3
#

import sys

from build_tool.arkon_config import  ConfigSupport
from build_tool.amazon_deploy import  AmazonConfig
from build_tool.amazon_deploy import  AmazonDeploy


def from_config_path(config_path:str) -> AmazonDeploy:
    ConfigSupport.ensure_enviro(config_path)
    amazon_config = AmazonConfig.from_config()
    amazon_master = AmazonDeploy(amazon_config)
    return amazon_master


def package_download():
    "main entry point"
    assert len(sys.argv) == 3, f"need args: config_path, remot_regex"
    config_path = sys.argv[1]
    remot_regex = sys.argv[2]
    print(f"### package_download: {config_path=} {remot_regex=}")
    amazon_master = from_config_path(config_path)
    amazon_result = amazon_master.package_download(remot_regex)
    for package_path in amazon_result:
        print(f"### {package_path=}")


def package_upload():
    "main entry point"
    assert len(sys.argv) == 3, f"need args: config_path, local_regex"
    config_path = sys.argv[1]
    local_regex = sys.argv[2]
    print(f"### package_upload: {config_path=} {local_regex=}")
    amazon_master = from_config_path(config_path)
    amazon_result = amazon_master.package_upload(local_regex)
    for package_path in amazon_result:
        print(f"### {package_path=}")
