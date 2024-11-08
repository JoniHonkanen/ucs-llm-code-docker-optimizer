import pytest
from agents.code_fixer_agent import code_fixer_agent
from schemas import AgentState, Code
import os

# Load environment variables for API access
from dotenv import load_dotenv
load_dotenv()

error_code = """import pandas as pd\nfrom pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, LpStatusOptimal\n\n# Load data from Excel files\nmaterials_df = pd.read_excel('cutting_stock_problem_data.xlsx', sheet_name='Materials', engine='openpyxl')\norders_df = pd.read_excel('cutting_stock_problem_data.xlsx', sheet_name='Orders', engine='openpyxl')\n\n# Convert DataFrame to usable lists\nmaterials = materials_df.to_dict(orient='records')\norders = orders_df.to_dict(orient='records')\n\n# Create a linear programming problem\nproblem = LpProblem('CuttingStockProblem', LpMinimize)\n\n# Decision variables: number of each material used for each order\nx = LpVariable.dicts('cut', ((m['Material ID'], o['Order ID']) for m in materials for o in orders), lowBound=0, cat='Integer')\n\n# Objective function: minimize waste\nproblem += lpSum((m['Length (mm)'] - lpSum(x[m['Material ID'], o['Order ID']] * o['Length (mm)'] for o in orders)) * m['Quantity'] for m in materials), 'TotalWaste'\n\n# Constraints\n# Ensure each order is fulfilled\nfor o in orders:\n    problem += lpSum(x[m['Material ID'], o['Order ID']] for m in materials) >= o['Quantity'], f'Order_{o['Order ID']}'\n\n# Ensure we do not exceed material quantities\nfor m in materials:\n    problem += lpSum(x[m['Material ID'], o['Order ID']] for o in orders) <= m['Quantity'], f'MaterialLimit_{m['Material ID']}'\n\n# Solve the problem\nproblem.solve()\n\n# Output results\nif LpStatus[problem.status] == 'Optimal':\n    print('Optimal Solution Found:')\n    for m in materials:\n        for o in orders:\n            if x[m['Material ID'], o['Order ID']].varValue > 0:\n                print(f'Use {x[m['Material ID'], o['Order ID']].varValue} of {m['Material ID']} for {o['Order ID']}')\nelse:\n    print('No optimal solution found')"""

@pytest.fixture
def mock_state():
    return AgentState(code=Code(python_code=error_code), docker_output="error_message_here")

@pytest.mark.integration  # Custom marker for integration tests
@pytest.mark.asyncio
async def test_code_fixer_agent_live_api(mock_state):
    # Run the agent with a live API call
    result_state = await code_fixer_agent(mock_state)

    # Assertions to ensure proper behavior
    assert "code" in result_state
    assert result_state["code"].python_code is not None  # Expect a real code response from the LLM
    assert isinstance(result_state["code"].python_code, str)  # Ensure it returned a string code output