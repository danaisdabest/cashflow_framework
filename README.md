# cashflow

Auditable, content-addressed cashflow modeling library.
```
docker compose run --rm dev
python src/cashflow/run.py
```
Copy paste mermaid chart printed to stdout into mermaid.live, e.g. 
```
flowchart LR

  expense_input_node_cashflow.models.example_ExpenseInputNode_a4b515d540["expense_input_node: cashflow.models.example_ExpenseInputNode_a4b515d540"]
  node_that_adds_revenue_and_expenses_cashflow.models.example_NodeThatAddsRevenueAndExpenses_71f5e49861["node_that_adds_revenue_and_expenses: cashflow.models.example_NodeThatAddsRevenueAndExpenses_71f5e49861
 (
input_node_hashes: 
    revenue_input_node: cashflow.models.example_RevenueInputNode_e6c660967a
    expense_input_node: cashflow.models.example_ExpenseInputNode_a4b515d540
)"]
  revenue_input_node_cashflow.models.example_RevenueInputNode_e6c660967a["revenue_input_node: cashflow.models.example_RevenueInputNode_e6c660967a"]
  expense_input_node_cashflow.models.example_ExpenseInputNode_a4b515d540 --> node_that_adds_revenue_and_expenses_cashflow.models.example_NodeThatAddsRevenueAndExpenses_71f5e49861
  revenue_input_node_cashflow.models.example_RevenueInputNode_e6c660967a --> node_that_adds_revenue_and_expenses_cashflow.models.example_NodeThatAddsRevenueAndExpenses_71f5e49861

```
<img width="1390" height="595" alt="image" src="https://github.com/user-attachments/assets/efa3bff3-f643-4b00-b184-03d8f5336b9c" />

