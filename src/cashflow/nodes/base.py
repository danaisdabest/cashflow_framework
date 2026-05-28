"""
Base classes for nodes in the cashflow model
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel, PrivateAttr, computed_field
import hashlib
from cashflow.cache.cache import CacheLayer
from functools import cached_property




class BaseNodeInput(ABC, BaseModel):

    def input_node_hashes(self) -> dict[str, str]:
        return {
            field_name: v.get_hash()
            for field_name in self.model_fields
            if isinstance((v := getattr(self, field_name)), BaseNode)
        }

    def get_input_hash(self) -> str:
        # use hashes from input nodes to get a hash of the input
        hash = ""
        for field_name in self.model_fields:
            v = getattr(self, field_name)
            hash+=field_name + "_"
            if isinstance(v, BaseNode):
                hash += v.get_hash()
            elif isinstance(v, list) or isinstance(v, tuple):
                types = list(set([type(item) for item in v]))
                if len(types) > 1:
                    raise ValueError(f"Cant have multiple types in a list: {types}")
                if types[0] == BaseNode:
                    for item in v:
                        hash += item.get_hash()
                elif types[0] in [int, float, str, bool]:
                    # compute a hash of the list
                    hash += str(v)
                else:
                    raise ValueError(f"Unsupported input type cannot be hashed: {types[0]}")
            elif type(v) in [int, float, str, bool]:
                hash += str(v)
            else:
                raise ValueError(f"Unsupported input type cannot be hashed: {type(v)}")
        return hashlib.sha256(hash.encode()).hexdigest()[:10]


class BaseNodeOutput(ABC,BaseModel):
    pass

    def get_output_hash(self) -> str:
        return "" # don't hash outputs .... it's alot of work

class BaseNode(ABC, BaseModel):
    """
    Nodes take in other Nodes and produce instances of their own OutputClass
    node initializations looks like
    cache_layer = CacheLayer(graph_cache_key="example_graph")
    some_node_0 = RootNode(cache_layer=cache_layer, input=RootNode.Input(some_input_a=1, some_input_b=2))
    some_node_1 = RootNode(cache_layer=cache_layer, input=RootNode.Input(some_input_a=3, some_input_b=4))
    my_other_node = OtherNode(cache_layer=cache_layer, input=OtherNode.Input(input_node_a=some_node_0, input_node_b=some_node_1))
    """

    class Input(BaseNodeInput):
        pass

    class Output(BaseNodeOutput):
        pass

    cache_layer: CacheLayer
    input: BaseNodeInput
    is_deterministic: bool
    _output: BaseNodeOutput = PrivateAttr() 

    def get_hash(self) -> str:
        raise NotImplementedError("must be implemented by subclass -  use ComputationNodeMixin or DataAccessNodeMixin")
    
    @property
    def input_hash(self) -> str:
        return self.input.get_input_hash()

    @property
    @abstractmethod
    def output_hash(self) -> str:
        raise NotImplementedError("must be implemented by subclass")

    @computed_field
    @property
    def input_node_hashes(self) -> dict[str, str]:
        return self.input.input_node_hashes()
    
    @property
    def class_hash_prefix(self) -> str:
        # TODO: add some docker container/image id to this? so that if the code changes, the hash changes
        return f"{self.__class__.__module__}_{self.__class__.__qualname__}"

    @computed_field
    @property
    @abstractmethod
    def compute_result_cache_key(self) -> str:
        """
        For now just the class input cache key
        """
        raise NotImplementedError("must be implemented by subclass")
        
    @property
    def class_input_cache_key(self) -> str:
        return f"{self.class_hash_prefix}_{self.input_hash}"
    
    def get(self) -> Output:
        """
        get the final result of the node
        begins by checking if the result is already computed
        if not, compute the result and return it after storing it
        """

        # check if the result is already computed

        if True or self._output is None:
            # check if result in cache
            cache_result = self._get_from_cache()
            if cache_result is not None:
                self._output = cache_result
                return self._output
            else:
                # compute the result
                self._output = self._compute_result()
                self._send_to_cache(self._output)
                return self._output
    
    @abstractmethod
    def _compute_result(self) -> Output:
        """
        compute the result of the node
        """
        raise NotImplementedError("must be implemented by subclass")
        # do something with the inputs to produce the output
    
        
    @abstractmethod
    def _send_to_cache(self, output: Output) -> None:
        """
        send the result to the cache
        """
        raise NotImplementedError("must be implemented by subclass")

    @abstractmethod
    def _get_from_cache(self) -> Output:
        """
        get the result from the cache
        """
        raise NotImplementedError("must be implemented by subclass")

    
    
class ComputationNodeMixin(BaseNode):
    """
    DeterministicMixin makes the node hash ignore output and only care about input
    The compute_result_cache_key is the same as the input hash and also the same as the node hash
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, is_deterministic=True)

    def get_hash(self) -> str:
        return self.compute_result_cache_key

    @cached_property
    def output_hash(self) -> str:
        return self._output.get_output_hash()
    
    @computed_field
    @property
    def compute_result_cache_key(self) -> str:
        """
        For now just the class input cache key
        """
        return self.class_input_cache_key


class BaseDataAccessNodeMixin(BaseNode):
    """
    StateDependentMixin makes the node hash include output and only care about input
    The compute_result_cache_key is the same as the input hash and also the same as the node hash
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, is_deterministic=False)

    @abstractmethod
    def get_data_last_modified_timestamp(self) -> str:
        """
        Could be the max(last_modified) of all relevant db tables, could be some response from an api call, could be datetime.now()
        If we have cached the data this will help us find it via self.compute_result_cache_key
        Always, it will matter for the node's final hash
        """
        raise NotImplementedError("must be implemented by subclass")

    @property
    @abstractmethod
    def output_hash(self) -> str:
        """
        NOTE: output_hash could be == '' if
            - data_last_modified_timestamp is sufficient to identify the data 
            - or if output is too expensive to hash
        """
        raise NotImplementedError("must be implemented by subclass")


    def get_hash(self) -> str:
        return f"{self.compute_result_cache_key}_{self.output_hash}"

    @computed_field
    @property
    def compute_result_cache_key(self) -> str:
        """
        For now just the class input cache key
        """
        return f"{self.class_input_cache_key}_{self.get_data_last_modified_timestamp()}"
