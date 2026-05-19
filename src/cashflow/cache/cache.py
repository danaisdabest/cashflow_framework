from pydantic import BaseModel, PrivateAttr
from typing import Any
from abc import ABC, abstractmethod
import os
import logging
import json
import pyarrow.parquet as parquet
import pyarrow as pyarrow
from typing import Type
from functools import cached_property
from pydantic import computed_field


class StorageBackend(ABC, BaseModel):
    @abstractmethod
    def in_cache(self, cache_key: str) -> bool:
        raise NotImplementedError("must be implemented by subclass")

    @abstractmethod
    def _bytes_to_storage(self, cache_key: str, data: bytes) -> None:
        raise NotImplementedError("must be implemented by subclass")

    @abstractmethod
    def _bytes_from_storage(self, cache_key: str) -> bytes:
        raise NotImplementedError("must be implemented by subclass")

class FileStorageBackend(StorageBackend):
    graph_cache_key: str
    _home_directory: str = PrivateAttr()

    def __init__(self, graph_cache_key: str):
        super().__init__(graph_cache_key=graph_cache_key)
        self._home_directory = self.create_home_directory()

    def _file_path(self, file_name: str) -> str:
        return os.path.join(self._home_directory, file_name)

    def create_home_directory(self) -> None:
        """
        create the directory for the cache
        """
        home_directory = os.path.join(os.path.expanduser("~"), ".cashflow", self.graph_cache_key)
        if not os.path.exists(home_directory):
            os.makedirs(home_directory, exist_ok=True)
        logging.info(f"created home directory: {home_directory}")
        return home_directory


    def in_cache(self, cache_key: str) -> bool:
        return os.path.exists(self._file_path(cache_key))

    def _bytes_to_storage(self, file_name: str, data: bytes) -> None:
        return self._bytes_to_file(self._file_path(file_name), data)

    def _bytes_from_storage(self, file_name: str) -> bytes:
        return self._bytes_from_file(self._file_path(file_name))

    def _bytes_to_file(self, file_path: str, data: bytes) -> None:
        """
        store data in file as Parquet
        """
        print(f"writing data to file: {file_path}")
        with open(file_path, "wb") as f:
            f.write(data)
        logging.info(f"wrote parquet data to file: {file_path}")

    def _bytes_from_file(self, cache_key: str) -> bytes:
        """
        retrieve data from file as Parquet
        """
        if not self.in_cache(cache_key):
            return None
        file_path = self._file_path(cache_key)
        print(f"reading data from file: {file_path}")
        with open(file_path, "rb") as f:
            return f.read()

class RedisStorageBackend(StorageBackend):
    """
    TODO: Implement this
    """
    def in_cache(self, cache_key: str) -> bool:
        return self._in_redis(cache_key)

    def _bytes_to_storage(self, cache_key: str, data: bytes) -> None:
        return self._bytes_to_redis(cache_key, data)

    def _bytes_from_storage(self, cache_key: str) -> bytes:
        return self._bytes_from_redis(cache_key)

    def _in_redis(self, cache_key: str) -> bool:
        raise NotImplementedError("must be implemented here .... ") 

    def _bytes_to_redis(self, cache_key: str, data: bytes) -> None:
        raise NotImplementedError("must be implemented here .... ")

    def _bytes_to_redis(self, cache_key: str, data: bytes) -> None:
        raise NotImplementedError("must be implemented here .... ")

    def _bytes_from_redis(self, cache_key: str) -> bytes:
        raise NotImplementedError("must be implemented here .... ")

class DataManager(ABC, BaseModel):

    storage_backend: StorageBackend

    @property
    @abstractmethod
    def _file_suffix(self) -> str:
        """
        the file suffix for the file manager
        """
        raise NotImplementedError("must be implemented by subclass")

    def _file_name(self, cache_key: str) -> str:
        """
        the file name for the file manager
        """
        return os.path.join(cache_key + self._file_suffix)
    

    def _to_bytes(self, data: Any) -> bytes:
        raise NotImplementedError("must be implemented by subclass")

    def _from_bytes(self, data: bytes) -> Any:
        raise NotImplementedError("must be implemented by subclass")


    def to_cache(self, cache_key: str, data: dict[str, list[Any]]) -> None:
        """
        store data in file as Parquet
        """
        bytes_data = self._to_bytes(data)
        return self.storage_backend._bytes_to_storage(self._file_name(cache_key), bytes_data)
    
    def from_cache(self, cache_key: str) -> Any:
        """
        retrieve data from cache as Parquet
        """
        bytes_data = self.storage_backend._bytes_from_storage(self._file_name(cache_key))
        if bytes_data is None:
            return None
        return self._from_bytes(bytes_data)

class JsonDataManager(DataManager):

    @property
    def _file_suffix(self) -> str:
        """
        the file suffix for the file manager
        """
        return ".json"

    def _to_bytes(self, data: dict[str, Any]) -> bytes:
        return json.dumps(data).encode("utf-8")

    def _from_bytes(self, data: bytes) -> dict[str, Any]:
        return json.loads(data.decode("utf-8"))

class ParquetDataManager(DataManager):

    @property
    def _file_suffix(self) -> str:
        """
        the file suffix for the file manager
        """
        return ".parquet"


    def _to_bytes(self, columns: dict[str, list[Any]]) -> bytes:
        buf = pyarrow.BufferOutputStream()
        parquet.write_table(pyarrow.table(columns), buf)
        return buf.getvalue().to_pybytes()

    def _from_bytes(self, data: bytes) -> dict[str, list[Any]]:
        reader = pyarrow.BufferReader(data)
        table = parquet.read_table(reader)
        return table.to_pydict()
    

class ManifestFile(BaseModel):
    home_directory: str
    def create_manifest(self, cache_key: str) -> None:
        """
        create a manifest file
        """
        raise NotImplementedError("must be implemented by subclass")
    
    def update_manifest(self, cache_key: str) -> None:
        """
        update a manifest file
        """
        raise NotImplementedError("must be implemented by subclass")

    def read_manifest(self, cache_key: str) -> Any:
        """
        read a manifest file
        """
        raise NotImplementedError("must be implemented by subclass")


class CacheLayer(BaseModel):
    
    graph_cache_key: str
    storage_backend_class: Type[StorageBackend]

    def in_cache(self, cache_key: str) -> bool:
        """
        check if data is in cache
        """
        return self._storage_backend.in_cache(cache_key)


    def to_json(self, cache_key: str, data: Any) -> None:
        """
        store data in cache as JSON
        """
        self._json_data_manager.to_cache(cache_key, data)

    def from_json(self, cache_key: str) -> Any:
        """
        retrieve data from cache as JSON
        """
        return self._json_data_manager.from_cache(cache_key)

    def to_parquet(self, cache_key: str, data: dict[str, list[Any]]) -> None:
        """
        store data in cache as Parquet
        """
        self._parquet_data_manager.to_cache(cache_key, data)

    def from_parquet(self, cache_key: str) -> Any:
        """
        retrieve data from cache as Parquet
        """
        return self._parquet_data_manager.from_cache(cache_key)
    
    @computed_field
    @cached_property
    def _storage_backend(self) -> StorageBackend:
        """
        the backend storage
        """
        return self.storage_backend_class(graph_cache_key=self.graph_cache_key)

    @computed_field
    @cached_property
    def _json_data_manager(self) -> JsonDataManager:
        """
        the JSON file manager
        """
        return JsonDataManager(storage_backend=self._storage_backend)

    @computed_field
    @cached_property
    def _parquet_data_manager(self) -> ParquetDataManager:
        """
        the Parquet file manager
        """
        return ParquetDataManager(storage_backend=self._storage_backend)

    @computed_field
    @cached_property
    def _manifest_file(self) -> ManifestFile:
        """
        the manifest file
        """
        return ManifestFile(storage_backend=self._storage_backend)