from __future__ import annotations

from abc import abstractmethod
from typing import Any

from cashflow.nodes.base import BaseNode
from pydantic import BaseModel, PrivateAttr
#from tsbucket import TimeSeries

class TimeSeries(BaseModel):
    index: list[Any]
    series: list[Any]

class BaseIndexedSeriesNode(BaseNode):
    """
    IndexedSeries are for indexed series values stored as parquet files
    """
    class Input(BaseNode.Input):
        pass


    class Output(BaseNode.Output):
        pass

        def validate(self) -> None:
            # check that all fields are TimeSeries
            for field_name in self.model_fields:
                if not isinstance(getattr(self, field_name), TimeSeries):
                    raise ValueError(f"Field {field_name} is not a TimeSeries")
            # check that all the time series have the same index
            all_indices = [getattr(self, field_name).index for field_name in self.model_fields]
            if not all(indices == all_indices[0] for indices in all_indices):
                raise ValueError("All time series must have the same index")

        

    input: Input
    _output: Output = PrivateAttr()
    

    @abstractmethod
    def _compute_result(self) -> Output:
        raise NotImplementedError("must be implemented by subclass")
        
    def _serialize_output(self, output: Output) -> dict[str, list[Any]]:
        # confirm that all the time series have the same index
        all_indices = [getattr(output, field_name).index for field_name in output.model_fields]
        if not all(indices == all_indices[0] for indices in all_indices):
            raise ValueError("All time series must have the same index")
        shared_index = all_indices[0]
        columns: dict[str, list[Any]] = {"index": shared_index}
        for field_name in output.model_fields:
            ts: TimeSeries = getattr(output, field_name)
            columns[field_name] = ts.series
        return columns
    
    def _deserialize_output(self, data: dict[str, list[Any]]) -> Output:
        index = data["index"]   
        kwargs = {}
        for field_name in self.Output.model_fields:
            series = data[field_name]
            kwargs[field_name] = TimeSeries(index=index, series=series)
        return self.Output(**kwargs)

    def _send_to_cache(self, output: Output) -> None:
        # pre process the list of time series into a dataframe
        self.cache_layer.to_parquet(self.compute_result_cache_key, self._serialize_output(output))

    def _get_from_cache(self) -> Output:
        table = self.cache_layer.from_parquet(self.compute_result_cache_key)
        if table is not None:
            return self._deserialize_output(table)
        else:
            return None

