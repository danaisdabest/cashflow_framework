"""
Every Cashflow Model gets its own .py module like this one 
"""

from cashflow.models.base import BaseCashflowModel
from cashflow.nodes.record import BaseRecordsNode
from cashflow.nodes.indexed_series import BaseIndexedSeriesNode
from cashflow.nodes.base import ComputationNodeMixin
from cashflow.nodes.data_access import DbDataAccessNodeMixin, ExternalApiDataAccessNodeMixin
from pydantic import BaseModel
from pydantic import PrivateAttr
from cashflow.nodes.indexed_series import TimeSeries
from cashflow.nodes.record import Record
from pydantic import computed_field
from functools import cached_property


class DbVectorDataNode(BaseIndexedSeriesNode, DbDataAccessNodeMixin):
    #TODO
    pass

class ExternalApiVectorDataNode(BaseIndexedSeriesNode, ExternalApiDataAccessNodeMixin):
    #TODO
    pass

class DbRecordsDataNode(BaseRecordsNode, DbDataAccessNodeMixin):
    #TODO
    pass

class ExternalApiRecordsDataNode(BaseRecordsNode, ExternalApiDataAccessNodeMixin):
    #TODO
    pass

### Example Cashflow model
class InputsNode1(BaseRecordsNode, ComputationNodeMixin):
    class Input(BaseRecordsNode.Input):
        some_input_a: int
        some_input_b: int
    
    class Output(BaseRecordsNode.Output):
        some_input_a: Record
        some_input_b: Record

    input: Input
    _output: Output = PrivateAttr()
    def _compute_result(self) -> Output:
        moo =  self.Output(some_input_a=Record(value=self.input.some_input_a, date=None), some_input_b=Record(value=self.input.some_input_b, date=None))
        return moo

class InputsNode2(BaseRecordsNode, ComputationNodeMixin):
    class Input(BaseRecordsNode.Input):
        some_input_c: int
        some_input_d: int
    
    class Output(BaseRecordsNode.Output):
        some_input_c: Record
        some_input_d: Record
    
    input: Input
    _output: Output = PrivateAttr()
    
    def _compute_result(self) -> Output:
        return self.Output(
            some_input_c=Record(value=self.input.some_input_c, date=None), 
            some_input_d=Record(value=self.input.some_input_d, date=None)
            )

class SeriesNode1(BaseIndexedSeriesNode, ComputationNodeMixin):
    class Input(BaseIndexedSeriesNode.Input):
        input_node_a: InputsNode1
        input_node_b: InputsNode2 
        input_node_c: InputsNode2 

    class Output(BaseIndexedSeriesNode.Output):
        result_time_series_1: TimeSeries
        result_time_series_2: TimeSeries
        result_time_series_3: TimeSeries

    input: Input
    _output: Output = PrivateAttr()

    def _compute_result(self) -> Output:
        input_node_a = self.input.input_node_a.get()
        input_node_b = self.input.input_node_b.get()
        input_node_c = self.input.input_node_c.get()
        index = [1, 2, 3]
        series_1 = [input_node_a.some_input_a.value * 5, input_node_a.some_input_b.value * 10, 0]
        series_2 = [input_node_b.some_input_c.value * 5, input_node_b.some_input_d.value * 10, 0]
        series_3 = [input_node_c.some_input_c.value * 5, input_node_c.some_input_d.value * 10, 0]
        return self.Output(
            result_time_series_1=TimeSeries(index=index, series=series_1),
            result_time_series_2=TimeSeries(index=index, series=series_2),
            result_time_series_3=TimeSeries(index=index, series=series_3)
        )


class ExampleCashflowModel(BaseCashflowModel):
    class Nodes(BaseModel):
        input_node_0: InputsNode1
        input_node_1: InputsNode2
        input_node_2: InputsNode2
        series_node_1: SeriesNode1

    @computed_field
    @cached_property
    def _nodes(self) -> Nodes:
        input_node_0=InputsNode1(cache_layer=self._cache_layer, input=InputsNode1.Input(some_input_a=1, some_input_b=2))
        input_node_1=InputsNode2(cache_layer=self._cache_layer, input=InputsNode2.Input(some_input_c=3, some_input_d=4))
        input_node_2=InputsNode2(cache_layer=self._cache_layer, input=InputsNode2.Input(some_input_c=5, some_input_d=6))
        series_node_1=SeriesNode1(cache_layer=self._cache_layer, input=SeriesNode1.Input(input_node_a= input_node_0, input_node_b=input_node_1, input_node_c=input_node_2))
        return self.Nodes(input_node_0=input_node_0, input_node_1=input_node_1, input_node_2=input_node_2, series_node_1=series_node_1)
        

    def run(self):
        from cashflow.viz.dag_mermaid import model_to_mermaid


        for k in [getattr(self._nodes, name).get() for name in self._nodes.model_fields]:
            print(k)

        print(model_to_mermaid(self))



class RevenueInputNode(BaseRecordsNode, ComputationNodeMixin):
    class Input(BaseRecordsNode.Input):
        revenue_input: list[int | float]
    
    class Output(BaseRecordsNode.Output):
        revenue_output: list[float]

    def _compute_result(self) -> Output:
        return self.Output(revenue_output=[float(x)+111 for x in self.input.revenue_input])


class ExpenseInputNode(BaseRecordsNode, ComputationNodeMixin):
    class Input(BaseRecordsNode.Input):
        expense_input: list[int | float]
    
    class Output(BaseRecordsNode.Output):
        expense_output: list[float]
    
    def _compute_result(self) -> Output:
        if any([x>0 for x in self.input.expense_input]):
            raise ValueError("Expenses cannot be positive")
        return self.Output(expense_output=[float(x)+222 for x in self.input.expense_input])


class NodeThatAddsRevenueAndExpenses(BaseRecordsNode, ComputationNodeMixin):
    class Input(BaseRecordsNode.Input):
        revenue_input_node: RevenueInputNode
        expense_input_node: ExpenseInputNode

    class Output(BaseRecordsNode.Output):
        result_output: list[float]
   

    def _compute_result(self) -> Output:
        revenue_list = self.input.revenue_input_node.get().revenue_output
        expense_list = self.input.expense_input_node.get().expense_output
        if len(revenue_list) != len(expense_list):
            raise ValueError("Revenue and expenses must have the same length")

        # this node adds revenue and expenses index by index 
        result_list = [
            revenue_list[i] + expense_list[i] for i in range(len(revenue_list))
        ]
        return self.Output(result_output=result_list)

class RevenueExpenseCashflowModel(BaseCashflowModel):
    class Nodes(BaseModel):
        revenue_input_node: RevenueInputNode
        expense_input_node: ExpenseInputNode
        node_that_adds_revenue_and_expenses: NodeThatAddsRevenueAndExpenses

    
    @computed_field
    @cached_property
    def _nodes(self) -> Nodes:
        revenue_input_node = RevenueInputNode(
            cache_layer=self._cache_layer, 
            input=RevenueInputNode.Input(revenue_input=[100, 200, 300]))
        expense_input_node = ExpenseInputNode(
            cache_layer=self._cache_layer, 
            input=ExpenseInputNode.Input(expense_input=[-50, -100, -150]))
        node_that_adds_revenue_and_expenses = NodeThatAddsRevenueAndExpenses(
            cache_layer=self._cache_layer, 
            input=NodeThatAddsRevenueAndExpenses.Input(
                revenue_input_node=revenue_input_node, 
                expense_input_node=expense_input_node))
        return self.Nodes(
            revenue_input_node=revenue_input_node, 
            expense_input_node=expense_input_node, 
            node_that_adds_revenue_and_expenses=node_that_adds_revenue_and_expenses)

    def run(self):
        from cashflow.viz.dag_mermaid import model_to_mermaid

        print("About to print my results!!!")
        print(f"adding node = {self._nodes.node_that_adds_revenue_and_expenses.get()}")
        print(f"nodes that this came from = {self._nodes.node_that_adds_revenue_and_expenses.input}")
        print("Done printing my results!!!")

        print(model_to_mermaid(self))
