# pytest -s tests/agents/test_new_loop_agent.py
import pytest
from schemas import AgentState, Code, Purpose, OutputOfCode
from agents.new_loop_agent import new_loop_logic
from dotenv import load_dotenv

from tests.utils.color_print import print_colored_diff

load_dotenv()

## THIS PURPOSE IS TO TEST PART WHEN NEW ROUND START AND WE TRY TO OPTIMIZE GENERATED CODE
## USED AFTER CODE OUTPUT ANALYZER AGENT IF USER DETERM TO OPTIMIZE CODE


@pytest.fixture
def mock_state():
    return AgentState(
        code=Code(
            python_code=last_code,
            requirements="",
            resources="",
        ),
        purpose=Purpose(
            user_summary="The user aims to optimize the cutting of materials for production orders to reduce waste and utilize materials efficiently.",
            problem_type="Cutting Stock Problem",
            optimization_focus="The solution should focus on generating cutting plans that minimize material waste while ensuring that all production order requirements are met, taking into account the dimensions and quantities of both materials and orders.",
            chatbot_response="chatbot_response",
            goal="The primary objective is to achieve an optimal",
            resource_requirements="We need to account for the total lengths and widths of each material available, as well as the required lengths and widths for each order. The materials available are 6000 mm and 8000 mm lengths, while the orders require cuts of 2000 mm, 3000 mm, and 4000 mm lengths in various quantities.",
        ),
        promptFiles=fileData,
        result=OutputOfCode(
            answer_description="The allocation suggests that to fulfill the customer orders, Material 1 will be mostly used for Orders 2 and 3, while Material 2 will primarily fulfill Order 1. This allocation strategy indicates which materials are effectively utilized according to the orders placed.",
            answer="",
            improvement="",
            explanation="",
            is_goal_achieved="",
        ),
    )


@pytest.mark.asyncio
async def test_new_loop_agent(mock_state):
    try:
        response = await new_loop_logic(mock_state)
        assert response.python_code is not None, "Expected code output from LLM"

        print(response)

        print_colored_diff(
            last_code,
            response.python_code,
            fromfile="Original code",
            tofile="Optimized code",
        )
    except Exception as e:
        assert False, f"Error: {e}"


# CODE THAT NEED TO BE OPTIMIZED
last_code = """import pandas as pd
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpStatus

# Load data from Excel file
file_path = 'cutting_stock_problem_data.xlsx'
materials_df = pd.read_excel(file_path, sheet_name='Materials', engine='openpyxl')
orders_df = pd.read_excel(file_path, sheet_name='Orders', engine='openpyxl')

# Define the optimization problem
prob = LpProblem("Cutting_Stock_Problem", LpMinimize)

# Create variables for each material and order combination
variables = {}
for i, material in materials_df.iterrows():
    for j, order in orders_df.iterrows():
        var_name = f"x_{i}_{j}"
        variables[(i, j)] = LpVariable(var_name, lowBound=0, cat='Integer')

# Objective: Minimize waste
prob += lpSum(variables[(i, j)] * (material['Length (mm)'] * material['Width (mm)'] - order['Length (mm)'] * order['Width (mm)']) \
             for (i, j), var in variables.items() for i, material in materials_df.iterrows() for j, order in orders_df.iterrows())

# Constraints: Fulfill each order
for j, order in orders_df.iterrows():
    prob += lpSum(variables[(i, j)] for i, material in materials_df.iterrows()) >= order['Quantity']

# Constraints: Material availability
for i, material in materials_df.iterrows():
    prob += lpSum(variables[(i, j)] for j, order in orders_df.iterrows()) <= material['Quantity']

# Solve the problem
prob.solve()

# Output the results
print("Status:", LpStatus[prob.status])
for (i, j), var in variables.items():
    print(f"Material {i+1} to Order {j+1} units: {var.varValue}")

print("Objective (Total Waste):", prob.objective.value())"""

# DATA FROM FILES
fileData = """File: cutting_stock_problem_data.xlsx, Sheet: Materials
Data:
[
  {
    "Material ID":"Materiaali 1",
    "Length (mm)":6000,
    "Width (mm)":100,
    "Quantity":10
  },
  {
    "Material ID":"Materiaali 2",
    "Length (mm)":8000,
    "Width (mm)":150,
    "Quantity":5
  }
]

File: cutting_stock_problem_data.xlsx, Sheet: Orders
Data:
[
  {
    "Order ID":"Tilaus 1",
    "Length (mm)":2000,
    "Width (mm)":50,
    "Quantity":6
  },
  {
    "Order ID":"Tilaus 2",
    "Length (mm)":3000,
    "Width (mm)":75,
    "Quantity":7
  },
  {
    "Order ID":"Tilaus 3",
    "Length (mm)":4000,
    "Width (mm)":100,
    "Quantity":3
  }
]"""
