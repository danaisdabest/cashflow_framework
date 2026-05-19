from cashflow.nodes.base import BaseDataAccessNodeMixin
from datetime import datetime



class DbDataAccessNodeMixin(BaseDataAccessNodeMixin):
    """
    Node for accessing raw data from a database
    """

    def get_db_last_modified_timestamp(self) -> datetime:
        raise NotImplementedError("must be implemented by subclass")

    def get_data_last_modified_timestamp(self) -> datetime:
        return self.get_db_last_modified_timestamp()

class ExternalApiDataAccessNodeMixin(BaseDataAccessNodeMixin):
    """
    Node for accessing raw data from an external API
    """

    def get_external_api_call_hash(self) -> str:
        raise NotImplementedError("must be implemented by subclass")

    def get_data_last_modified_timestamp(self) -> datetime:
        return self.get_external_api_call_hash()
