"""
"""

import os
import time
import shutil

from build_tool.arkon_config import CONFIG
from build_tool.arkon_config import ConfigSupport

from build_tool.amazon_deploy import AmazonConfig
from build_tool.amazon_deploy import AmazonDeploy

this_dir = os.path.dirname(__file__)
test_dir = f"{this_dir}/test.dir"

config_path = __file__.replace(".py", ".ini")
ConfigSupport.ensure_enviro(f"/home/user0/.trader.ini;{config_path}")
CONFIG()


def test_amazon_config():
    print()
    AmazonConfig.from_config()


def make_test_file(file_name:str) -> None:
    file_path = f"{test_dir}/{file_name}"
    os.makedirs(test_dir, exist_ok=True)
    with open(file_path, "w+") as file_hand:
        file_hand.write(f"hello-kitty = {file_name}")
    return file_path


def test_package_crypto():
    print()

    amazon_config = AmazonConfig.from_config()

    deployer = AmazonDeploy(
        amazon_config=amazon_config,
    )

    source_path = make_test_file("package-crypto.txt")

    os.makedirs(test_dir, exist_ok=True)
    with open(source_path, "w+") as file_hand:
        file_hand.write("hello-kitty")

    source_hash = deployer.package_file_hash(source_path)
    source_data = deployer.package_encrypt(source_path)

    os.remove(source_path)
    assert not os.path.exists(source_path)

    target_path = deployer.package_decrypt(source_data)
    target_hash = deployer.package_file_hash(target_path)

    os.remove(target_path)
    assert not os.path.exists(target_path)

    assert source_hash == target_hash
    assert source_path == target_path

    os.remove(source_data)


def test_package_depoy():
    print()

    shutil.rmtree(test_dir, ignore_errors=True)

    amazon_config = AmazonConfig.from_config()

    deployer = AmazonDeploy(
        amazon_config=amazon_config,
    )

    file_name = f"data-{time.time()}.whl"

    file_path = make_test_file(file_name)
    print(f"{file_path=}")
    assert os.path.isfile(file_path)

    upload_regex = r"data-.+[.]whl"
    upload_file_list = list()
    for source_path in deployer.package_upload(upload_regex):
        print(f"{source_path=}")
        upload_file_list.append(source_path)

    print(f"file_list: {len(upload_file_list)}")
    assert file_path in upload_file_list

    shutil.rmtree(test_dir, ignore_errors=True)

    download_regex = r"data-.+[.]whl[.]aes"
    download_file_list = list()
    for target_path in deployer.package_download(download_regex):
        print(f"{target_path=}")
        download_file_list.append(target_path)

    assert file_path in download_file_list
