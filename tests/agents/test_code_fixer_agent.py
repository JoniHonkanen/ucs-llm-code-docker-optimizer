# pytest -s tests/agents/test_code_fixer_agent.py
import pytest
import difflib
from agents.code_fixer_agent import fix_code_logic
from schemas import AgentState, Code, CodeFix

# Load environment variables for API access
from dotenv import load_dotenv

load_dotenv()

# You can tests code with error in here...
error_code = """import pandas as pd
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD

# Load data from the Excel file
materials_df = pd.read_excel('cutting_stock_problem_data.xlsx', sheet_name='Materials', engine='openpyxl')
orders_df = pd.read_excel('cutting_stock_problem_data.xlsx', sheet_name='Orders', engine='openpyxl')

# Initialize the linear programming problem
problem = LpProblem("CuttingStockProblem", LpMaximize)

# Dictionaries to hold data from dataframes
materials = {}
orders = {}

# Fill materials and orders dictionaries
for index, row in materials_df.iterrows():
    materials[row['Material ID']] = {
        'length': row['Length (mm)'],
        'width': row['Width (mm)'],
        'quantity': row['Quantity']
    }

for index, row in orders_df.iterrows():
    orders[row['Order ID']] = {
        'length': row['Length (mm)'],
        'width': row['Width (mm)'],
        'quantity': row['Quantity']
    }

# Decision variables
x = LpVariable.dicts("cut", ((m, o) for m in materials for o in orders), lowBound=0, cat='Integer')

# Objective: Maximize usage of material
problem += lpSum(x[m][o] * orders[o]['length'] * orders[o]['width'] for m in materials for o in orders)

# Constraints
# Ensure that the total order quantity is satisfied
for o in orders:
    problem += lpSum(x[m][o] for m in materials) >= orders[o]['quantity'], f"Demand_{o}"

# Ensure that material quantity is not exceeded
for m in materials:
    problem += lpSum(x[m][o] * orders[o]['length'] * orders[o]['width'] for o in orders) <= \
               materials[m]['length'] * materials[m]['width'] * materials[m]['quantity'], f"Supply_{m}"

# Solve the problem
solver = PULP_CBC_CMD(msg=True)
problem.solve(solver)

# Output the results
print("Status:", problem.status)
for m in materials:
    for o in orders:
        print(f"Material {m}, Order {o}: {x[m][o].varValue} pieces")

print("Total utilized material:", pulp.value(problem.objective))"""

error_message = """Docker container execution failed
Details:
Traceback (most recent call last):
File "/app/generated.py", line 34, in <module>
problem += lpSum(x[m][o] * orders[o]['length'] * orders[o]['width'] for m in materials for o in orders)
File "/usr/local/lib/python3.9/site-packages/pulp/pulp.py", line 2233, in lpSum
return LpAffineExpression().addInPlace(vector)
File "/usr/local/lib/python3.9/site-packages/pulp/pulp.py", line 867, in addInPlace
for e in other:
File "/app/generated.py", line 34, in <genexpr>
problem += lpSum(x[m][o] * orders[o]['length'] * orders[o]['width'] for m in materials for o in orders)
KeyError: 'Materiaali 1'
my-python-app exited with code 1"""


@pytest.fixture
def mock_state():
    return AgentState(
        code=Code(
            python_code=error_code,
            requirements="pandas\nopenpyxl\nPuLP",
            resources="cutting_stock_problem_data.xlsx",
        ),
        docker_output=error_message,
    )


@pytest.mark.asyncio
async def test_fix_code_logic(mock_state):

    try:
        # Call the core logic function directly
        response: CodeFix = await fix_code_logic(mock_state["code"], mock_state["docker_output"])
        print("\n\n\n RESPONSE: ", response)

        # Assertions to verify output structure and content
        assert response.fixed_python_code is not None, "Expected code output from LLM"
        assert isinstance(
            response.fixed_python_code, str
        ), "Expected code output as string"

        # Verify that the original error message is no longer in the code
        assert (
            error_message not in response.fixed_python_code
        ), "Expected error to be corrected in output code"

        # Print the fixed code for review
        print("\n\n**Fixed code:")
        print(response.fixed_python_code)

        print("\nWhat fixed and why: ", response.fix_description)

        # Print the differences between the original and fixed code
        diff = difflib.unified_diff(
            error_code.splitlines(),
            response.fixed_python_code.splitlines(),
            fromfile="Mock Error Code",
            tofile="Fixed Code",
            lineterm="",
        )

        print("\n\n**Differences between original and fixed code:")
        print("\n".join(diff))

        print("Test passed: fix_code_logic function produced a valid response.")
    except Exception as e:
        pytest.fail(f"Test failed with unexpected error: {e}")
