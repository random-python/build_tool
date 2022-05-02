"""
"""
import os
import time
import shutil

from build_tool.arkon_config import CONFIG
from build_tool.arkon_config import ConfigSupport

from build_tool.cloud_aws_s3 import AuthBucketS3
from build_tool.cloud_aws_s3 import BucketOperatorS3
from build_tool.cloud_aws_s3 import ConfigTransferS3

this_dir = os.path.dirname(__file__)
config_path = __file__.replace(".py", ".ini")
ConfigSupport.ensure_enviro(f"/home/user0/.trader.ini;{config_path}")
CONFIG()


def test_config_access():
    print()
    config_access = AuthBucketS3.from_config()
    print(f"{config_access=}")


def test_config_transfer():
    print()
    config_trans = ConfigTransferS3.from_config()
    print(f"{config_trans=}")


def test_resource_transfer():
    print()

    bucket_oper = BucketOperatorS3()

    object_root = "vendor/tester"

    file_size = 64 * 1024
    file_name = f"aws-s3-tester-{time.time()}.tmp"
    local_path = f"/tmp/{file_name}"
    remot_path = f"{object_root}/{file_name}"

    shutil.rmtree(local_path, ignore_errors=True)

    with open(local_path, "wb") as local_file:
        local_file.truncate(file_size)

    local_meta = bucket_oper.local_meta(local_path)
    assert local_meta.length == file_size

    bucket_oper.resource_put_sync(local_path, remot_path)

    shutil.rmtree(local_path, ignore_errors=True)

    remot_meta = bucket_oper.remot_meta(remot_path)
    print(f"{remot_meta=}")

    bucket_oper.resource_get_sync(local_path, remot_path)

    local_meta = bucket_oper.local_meta(local_path)
    print(f"{local_meta=}")

    assert local_meta.length == file_size

    assert remot_meta == local_meta

    shutil.rmtree(local_path, ignore_errors=True)

    resource_list = bucket_oper.resource_list_sync(object_root)
    for resource in resource_list:
        print(f"{resource=}")

    bucket_oper.resource_delete_sync(remot_path)
