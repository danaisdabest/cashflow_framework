from __future__ import annotations


from cashflow.nodes.base import BaseNode
from pydantic import BaseModel
from datetime import datetime

class Record(BaseModel):
    value: int | float | str | bool
    date: datetime | None = None
class BaseRecordsNode(BaseNode):
    """
    BaseRecordsNodes are for scalar values stored as json files
    """
    class Input(BaseNode.Input):
        pass
    class Output(BaseNode.Output):
        pass

    def _send_to_cache(self, output: BaseNode.Output) -> None:
        self.cache_layer.to_json(self.compute_result_cache_key, output.model_dump(mode="json"))

    def _get_from_cache(self) -> BaseNode.Output | None:
        raw = self.cache_layer.from_json(self.compute_result_cache_key)
        if raw is None:
            return None
        return self.Output.model_validate(raw)


