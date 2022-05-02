"""
amazon aws s3 file sync support
"""

import os
import asyncio
import logging
import threading

import boto3
from boto3.s3.transfer import TransferConfig

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone

from _collections_abc import Generator

from build_tool.auth_method import AuthUserPass
from build_tool.arkon_config import CONFIG

frozen_class = dataclass(frozen=True)
logger = logging.getLogger(__name__)


async def asyncio_exec(func, *args):
    ""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)


@frozen_class
class AuthBucketS3(AuthUserPass):
    "account and access identity"

    section_auth = "cloud/aws/bucket/auth"

    region:str
    bucket:str
    use_ssl_mode:bool
    use_ssl_verify:bool

    @classmethod
    def from_config(cls) -> "AuthBucketS3":
        section = cls.config_section()
        return cls(
            region=section['region'],
            bucket=section['bucket'],
            username=section['username'],
            password=section['password'],
            use_ssl_mode=section.getboolean("use_ssl_mode", True),
            use_ssl_verify=section.getboolean("use_ssl_verify", True),
        )


@frozen_class
class ConfigTransferS3:
    ""

    section_transfer = "cloud/aws/bucket/transfer"

    max_io_queue:int
    max_concurrency:int
    io_chunksize:int
    multipart_chunksize:int

    @classmethod
    def from_config(cls) -> TransferConfig:
        ""
        config = CONFIG()
        if not config.has_section(cls.section_transfer):
            config.add_section(cls.section_transfer)
        section = config[cls.section_transfer]
        return TransferConfig(
            max_io_queue=section.getint('max_io_queue@int', 128),
            max_concurrency=section.getint('max_concurrency@int', 16),
            io_chunksize=section.getint('io_chunksize@int', 262144),
            multipart_chunksize=section.getint('multipart_chunksize@int', 16777216),
        )


@frozen_class
class MetaEntryS3:
    "local/remot resource meta info"

    path:str = field(compare=False)  # file/object path
    length: int  # file/object size
    modified:datetime  # file/object time

    def has_none(self) -> bool:
        "detect if this meta represents a 'NONE' value"
        return self.length == 0 and self.modified == SupportFuncS3.convert_unix_time(0)


class SupportFuncS3:
    "map between local and remot meta format"

    # s3 api keys
    key_Metadata = "Metadata"
    key_Key = "Key"
    key_Size = "Size"
    key_LastModified = "LastModified"

    # custom metadata stored with bucket object
    meta_entry_path = "entry_path"
    meta_entry_length = "entry_length"
    meta_entry_modified = "entry_modified"

    @classmethod
    def convert_date_time(cls, date_time:datetime) -> float:
        "map from python date time into unix time "
        return date_time.replace(tzinfo=timezone.utc).timestamp()

    @classmethod
    def convert_unix_time(cls, unix_time:float) -> datetime:
        "map from unix time into python date time"
        unix_secs = int(unix_time)
        base_time = datetime.utcfromtimestamp(unix_secs)
        return base_time.replace(tzinfo=timezone.utc)

    @classmethod
    def meta_encode_head(cls, meta_data:MetaEntryS3) -> dict:
        "map from local meta into remot meta"
        return {
            cls.key_Metadata: {
                cls.meta_entry_path: meta_data.path,
                cls.meta_entry_length: str(meta_data.length),
                cls.meta_entry_modified: meta_data.modified.isoformat(),
            }
        }

    @classmethod
    def meta_decode_head(cls, head_object:dict) -> MetaEntryS3:
        "map from remot meta into local meta"
        meta_data = head_object[cls.key_Metadata]
        return MetaEntryS3(
            path=meta_data[cls.meta_entry_path],
            length=int(meta_data[cls.meta_entry_length]),
            modified=datetime.fromisoformat(meta_data[cls.meta_entry_modified]),
        )

    @classmethod
    def meta_decode_list_v2(cls, list_entry:dict) -> MetaEntryS3:
        return MetaEntryS3(
            path=list_entry.get(SupportFuncS3.key_Key),
            length=list_entry.get(SupportFuncS3.key_Size),
            modified=list_entry.get(SupportFuncS3.key_LastModified),
        )

    @classmethod
    def meta_nothing(cls) -> MetaEntryS3:
        "produce a 'NONE' representation for file meta data"
        return MetaEntryS3(
            path="",
            length=0,
            modified=SupportFuncS3.convert_unix_time(0),
        )


class ProgressReportS3:
    "transfer progress reporter"

    def __init__(self, total_size:int, perc_step:float=4.0):
        self.update_lock = threading.Lock()
        self.wired_size = 0
        self.total_size = total_size
        self.perc_step = perc_step
        self.percent = 0

    def __call__(self, block_size:int) -> None:
        with self.update_lock:
            self.wired_size += block_size
        percent = 100 * self.wired_size / self.total_size
        if percent - self.percent > self.perc_step:
            self.percent = percent
            self.report_progress()

    def report_progress(self):
        logger.debug(f"{self.percent:6.2f}% {self.wired_size:,}")


class BucketOperatorS3:
    "amazon bucket resource operations"

    def __init__(self,
            config_access:AuthBucketS3=None,
            config_transfer:TransferConfig=None,
        ):
        self.config_access = config_access or AuthBucketS3.from_config()
        self.config_transfer = config_transfer or ConfigTransferS3.from_config()
        self.session = boto3.session.Session(
            region_name=self.config_access.region,
            aws_access_key_id=self.config_access.username,
            aws_secret_access_key=self.config_access.password,
        )

    def client_s3(self) -> "Client":
        "produce aws s3 client"
        return self.session.client('s3',
           use_ssl=self.config_access.use_ssl_mode,
           verify=self.config_access.use_ssl_verify,
        )

    def local_meta(self, entry_path:str) -> MetaEntryS3:
        "discover local file meta data"
        if os.path.isfile(entry_path):
            length = os.path.getsize(entry_path)
            modified = SupportFuncS3.convert_unix_time(os.path.getmtime(entry_path))
        elif os.path.isdir(entry_path):
            length = 0
            modified = SupportFuncS3.convert_unix_time(os.path.getmtime(entry_path))
        else:
            length = 0
            modified = SupportFuncS3.convert_unix_time(0)
        return MetaEntryS3(
            path=entry_path,
            length=length,
            modified=modified,
        )

    def remot_meta(self, entry_path:str) -> MetaEntryS3:
        "discover remot object meta data"
        try:
            head_object = self.client_s3().head_object(
                Bucket=self.config_access.bucket,
                Key=entry_path,
            )
            return SupportFuncS3.meta_decode_head(head_object)
        except:
            return SupportFuncS3.meta_nothing()

    async def resource_delete(self,
            remot_path:str,
        ) -> None:
        "remove file from remot bucket"
        await asyncio_exec(self.resource_delete_sync, remot_path)

    def resource_delete_sync(self,
            remot_path:str,
        ) -> None:
        "remove file from remot bucket"

        logger.debug(f"remot: {remot_path}")

        self.client_s3().delete_object(
            Bucket=self.config_access.bucket,
            Key=remot_path,
        )

    async def resource_get(self,
            local_path:str,
            remot_path:str,
            use_check:bool=False,
        ) -> None:
        "transfer file from remot into local"
        await asyncio_exec(self.resource_get_sync, local_path, remot_path, use_check)

    # @logster_duration
    def resource_get_sync(self,
            local_path:str,
            remot_path:str,
            use_check:bool=False,
        ) -> None:
        "transfer file from remot into local"

        logger.debug(f"local: {local_path}")
        logger.debug(f"remot: {remot_path}")

        local_meta = self.local_meta(local_path)
        remot_meta = self.remot_meta(remot_path)

        if use_check and (local_meta == remot_meta):
            logger.debug(f"no change")
            return

        extra_args = dict()

        total_size = remot_meta.length
        logger.debug(f"total: {total_size:,}")

        self.client_s3().download_file(
            Bucket=self.config_access.bucket,
            Filename=local_path,
            Key=remot_path,
            ExtraArgs=extra_args,
            Config=self.config_transfer,
            Callback=ProgressReportS3(total_size),
        )

        meta_time = SupportFuncS3.convert_date_time(remot_meta.modified)

        os.utime(local_path, (meta_time, meta_time))

        local_meta = self.local_meta(local_path)
        if local_meta != remot_meta:
            raise RuntimeError(f"wrong transfer {local_meta=} {remot_meta=}")

    async def resource_put(self,
            local_path:str,
            remot_path:str,
            use_check:bool=False,
        ) -> None:
        "transfer file from local into remot"
        await asyncio_exec(self.resource_put_sync, local_path, remot_path, use_check)

    # @logster_duration
    def resource_put_sync(self,
            local_path:str,
            remot_path:str,
            use_check:bool=False,
        ) -> None:
        "transfer file from local into remot"

        logger.debug(f"local: {local_path}")
        logger.debug(f"remot: {remot_path}")

        local_meta = self.local_meta(local_path)
        remot_meta = self.remot_meta(remot_path)

        if use_check and (local_meta == remot_meta):
            logger.debug(f"no change")
            return

        extra_args = dict()
        extra_args.update(SupportFuncS3.meta_encode_head(local_meta))

        total_size = local_meta.length
        logger.debug(f"total: {total_size:,}")

        self.client_s3().upload_file(
            Bucket=self.config_access.bucket,
            Filename=local_path,
            Key=remot_path,
            ExtraArgs=extra_args,
            Config=self.config_transfer,
            Callback=ProgressReportS3(total_size),
        )

    def resource_list_sync(self,
            object_root:str,
        ) -> Generator[MetaEntryS3]:
        ""
        result = self.client_s3().list_objects_v2(Bucket=self.config_access.bucket, Prefix=object_root)
        for list_entry in result.get('Contents'):
            yield SupportFuncS3.meta_decode_list_v2(list_entry)
