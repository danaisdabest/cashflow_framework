# run the cashflow model
from cashflow.models.example import RevenueExpenseCashflowModel

model = RevenueExpenseCashflowModel(graph_cache_key="example_graph_a")
model.run()