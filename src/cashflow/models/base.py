from pydantic import BaseModel
from pydantic import computed_field
from functools import cached_property
from abc import abstractmethod
from cashflow.cache.cache import CacheLayer, FileStorageBackend


class BaseCashflowModel(BaseModel):
    """
    BaseCashflowModel is the main class for the cashflow model
    """
    graph_cache_key: str
    class Nodes(BaseModel):
        pass

    @computed_field
    @cached_property
    @abstractmethod
    def _nodes(self) -> Nodes:
        raise NotImplementedError("must be implemented by subclass")

    @computed_field
    @cached_property
    def _cache_layer(self) -> CacheLayer:
        return CacheLayer(graph_cache_key=self.graph_cache_key, storage_backend_class=FileStorageBackend)

    def run(self):
        raise NotImplementedError("must be implemented by subclass")