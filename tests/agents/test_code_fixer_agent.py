# pytest -s tests/agents/test_code_fixer_agent.py
import pytest
import difflib
from agents.code_fixer_agent import fix_code_logic
from schemas import AgentState, Code

# Load environment variables for API access
from dotenv import load_dotenv

load_dotenv()

# You can tests code with error in here...
error_code = """
import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus

# Load data from Excel files
materials_df = pd.read_excel('cutting_stock_problem_data.xlsx', sheet_name='Materials', engine='openpyxl')
orders_df = pd.read_excel('cutting_stock_problem_data.xlsx', sheet_name='Orders', engine='openpyxl')

# Convert DataFrame to usable lists
materials = materials_df.to_dict(orient='records')
orders = orders_df.to_dict(orient='records')

# Create a linear programming problem
problem = LpProblem('CuttingStockProblem', LpMinimize)

# Decision variables: number of each material used for each order
x = LpVariable.dicts('cut', ((m['Material ID'], o['Order ID']) for m in materials for o in orders), lowBound=0, cat='Integer')

# Objective function: minimize waste
problem += lpSum((m['Length (mm)'] - lpSum(x[m['Material ID'], o['Order ID']] * o['Length (mm)'] for o in orders)) * m['Quantity'] for m in materials), 'TotalWaste'

# Constraints
# Ensure each order is fulfilled
for o in orders:
    problem += lpSum(x[m['Material ID'], o['Order ID']] for m in materials) >= o['Quantity'], f"Order_{o['Order ID']}"

# Ensure we do not exceed material quantities
for m in materials:
    problem += lpSum(x[m['Material ID'], o['Order ID']] for o in orders) <= m['Quantity'], f"MaterialLimit_{m['Material ID']}"

# Solve the problem
problem.solve()

# Output results
if LpStatus[problem.status] == 'Optimal':
    print('Optimal Solution Found:')
    for m in materials:
        for o in orders:
            if x[m['Material ID'], o['Order ID']].varValue > 0:
                print(f"Use {x[m['Material ID'], o['Order ID']].varValue} of {m['Material ID']} for {o['Order ID']}")
else:
    print('No optimal solution found')
"""

error_message = "SyntaxError: f-string: unmatched '['"


@pytest.fixture
def mock_state():
    return AgentState(code=Code(python_code=error_code), docker_output=error_message)


@pytest.mark.asyncio
async def test_fix_code_logic():
    code = Code(python_code=error_code)
    docker_output = error_message

    try:
        # Call the core logic function directly
        response = await fix_code_logic(code, docker_output)

        # Assertions to verify output structure and content
        assert response.python_code is not None, "Expected code output from LLM"
        assert isinstance(response.python_code, str), "Expected code output as string"

        # Verify that the original error message is no longer in the code
        assert (
            error_message not in response.python_code
        ), "Expected error to be corrected in output code"

        # Print the fixed code for review
        print("\n\n**Fixed code:")
        print(response.python_code)

        diff = difflib.unified_diff(
            error_code.splitlines(),
            response.python_code.splitlines(),
            fromfile="Original Code",
            tofile="Fixed Code",
            lineterm="",
        )

        print("\n\n**Differences between original and fixed code:")
        print("\n".join(diff))

        print("Test passed: fix_code_logic function produced a valid response.")
    except Exception as e:
        pytest.fail(f"Test failed with unexpected error: {e}")
