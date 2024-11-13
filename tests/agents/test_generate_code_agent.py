# pytest -s tests/agents/test_generate_code_agent.py

import pytest
from schemas import AgentState, Code, Purpose
from agents.code_generator_agent import generate_code_logic
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def mock_state():
    return AgentState(
        purpose=Purpose(
            user_summary="The user aims to optimize the cutting of materials for production orders to reduce waste and utilize materials efficiently.",
            problem_type="Cutting Stock Problem",
            optimization_focus="The solution should focus on generating cutting plans that minimize material waste while ensuring that all production order requirements are met, taking into account the dimensions and quantities of both materials and orders.",
            chatbot_response="chatbot_response",
            goal="The primary objective is to achieve an optimal cutting strategy that meets all order specifications while minimizing leftover material, thereby enhancing resource utilization and reducing costs.",
            resource_requirements="We need to account for the total lengths and widths of each material available, as well as the required lengths and widths for each order. The materials available are 6000 mm and 8000 mm lengths, while the orders require cuts of 2000 mm, 3000 mm, and 4000 mm lengths in various quantities.",
        ),
        promptFiles=(
            """File: cutting_stock_problem_data.xlsx, Sheet: Materials
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
        ),
    )


@pytest.mark.asyncio
async def test_code_generator_agent(mock_state):
    try:
        # Call `code_generator_agent` with the mock state
        response: Code = await generate_code_logic(mock_state)

        # Assertions to check the response content
        assert response.python_code is not None, "Expected code output from LLM"

        # Print the response for verification
        print(response)
    except Exception as e:
        pytest.fail(f"Test failed with unexpected error: {e}")
