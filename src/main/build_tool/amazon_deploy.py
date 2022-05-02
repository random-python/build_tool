"""
build support
"""

import os
import re
import filehash
import pyAesCrypt
from dataclasses import dataclass
from _collections_abc import Generator

from build_tool.cloud_aws_s3 import AuthBucketS3
from build_tool.cloud_aws_s3 import BucketOperatorS3

frozen_class = dataclass(frozen=True)


@frozen_class
class AmazonConfig(AuthBucketS3):
    ""

    package_secret:str  # aes key
    package_s3_root:str  # remote path
    package_file_root:str  # local path

    @classmethod
    def from_config(cls) -> "AmazonConfig":
        section = cls.config_section()
        return cls(
            region=section['region'],
            bucket=section['bucket'],
            username=section['username'],
            password=section['password'],
            package_secret=section['package_secret'],
            package_s3_root=section['package_s3_root'],
            package_file_root=section['package_file_root'],
            use_ssl_mode=section.getboolean("use_ssl_mode", True),
            use_ssl_verify=section.getboolean("use_ssl_verify", True),
        )


@dataclass
class AmazonDeploy:

    amazon_config:AmazonConfig

    def __post_init__(self):
        self.operator_s3 = BucketOperatorS3(self.amazon_config)

    def package_erase(self, remot_glob:str) -> Generator[str]:
        "TODO"

    def package_download(self, remot_regex:str) -> Generator[str]:
        object_root = self.amazon_config.package_s3_root
        filesys_root = os.path.abspath(self.amazon_config.package_file_root)
        print(f"### {object_root=} {filesys_root=}")
        object_meta_list = self.operator_s3.resource_list_sync(object_root)
        object_regex = re.compile(remot_regex)
        for object_meta in object_meta_list:
            remot_path = object_meta.path
            if not object_regex.search(remot_path): continue
            package_file = remot_path.removeprefix(object_root).removeprefix("/")
            local_path = f"{filesys_root}/{package_file}"
            self.ensure_local_path(local_path)
            self.operator_s3.resource_get_sync(local_path, remot_path, use_check=True)
            package_path = self.package_decrypt(local_path)
            yield package_path

    def package_upload(self, local_regex:str) -> Generator[str]:
        object_root = self.amazon_config.package_s3_root
        filesys_root = os.path.abspath(self.amazon_config.package_file_root)
        print(f"### {object_root=} {filesys_root=}")
        package_regex = re.compile(local_regex)
        for this_root, dir_list, file_list in os.walk(filesys_root):
            for this_file in file_list:
                package_path = f"{this_root}/{this_file}"
                if not package_regex.search(package_path): continue
                local_path = self.package_encrypt(package_path)
                local_file = local_path.removeprefix(filesys_root).removeprefix("/")
                remot_path = f"{object_root}/{local_file}"
                self.operator_s3.resource_put_sync(local_path, remot_path, use_check=True)
                yield package_path

    def ensure_local_path(self, file_path:str) -> None:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)

    def package_decrypt(self, data_path:str) -> str:
        file_path = data_path.removesuffix(".aes")
        self.ensure_local_path(file_path)
        package_secret = self.amazon_config.package_secret
        pyAesCrypt.decryptFile(data_path, file_path, package_secret)
        return file_path

    def package_encrypt(self, file_path:str) -> str:
        data_path = f"{file_path}.aes"
        self.ensure_local_path(file_path)
        package_secret = self.amazon_config.package_secret
        pyAesCrypt.encryptFile(file_path, data_path, package_secret)
        return data_path

    def package_file_hash(self, file_path) -> str:
        hasher = filehash.FileHash("sha1")
        return hasher.hash_file(file_path)
