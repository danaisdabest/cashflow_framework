from cashflow.models.example import ExampleCashflowModel
from cashflow.viz.dag_mermaid import model_to_mermaid, nodes_to_mermaid


def test_example_cashflow_model_mermaid():
    m = ExampleCashflowModel(graph_cache_key="test_graph")
    out = model_to_mermaid(m)
    assert "flowchart LR" in out
    assert "input_node_0" in out
    assert "input_node_1" in out
    assert "series_node_1" in out
    assert "  input_node_0 --> series_node_1" in out
    assert "  input_node_1 --> series_node_1" in out


def test_nodes_to_mermaid_same_as_model():
    m = ExampleCashflowModel(graph_cache_key="test_graph2")
    assert nodes_to_mermaid(m._nodes) == model_to_mermaid(m)
