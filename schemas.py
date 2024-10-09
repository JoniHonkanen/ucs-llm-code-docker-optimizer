from enum import Enum
from typing import List, TypedDict, Optional
from langchain_core.pydantic_v1 import BaseModel, Field, Extra, validator

# Define an Enum for the proceed field
class ProceedOption(str, Enum):
    CONTINUE = "continue"
    CANCEL = "cancel"
    NEW = "new"
    

# Schema for whole code project
class Purpose(BaseModel):
    user_summary: str = Field(
        description="A summarized statement of what the user wants to achieve."
    )
    problem_type: str = Field(
        description="The type of problem that is being solved, e.g., logistics optimization, resource allocation, etc."
    )
    optimization_focus: str = Field(
        description="A description of how the solution should be optimized, focusing on improving how effectively the problem is solved. The emphasis is on achieving better alignment with the problem's core objectives, enhancing solution quality, and refining the approach to meet the user's goals without prioritizing performance metrics such as runtime."
    )
    chatbot_response: str = Field(
        description="The chatbot's response to the user, explaining what is the problem, what will be done to solve the problem and why this approach is being taken."
    )
    next_steps: str = Field(
        description="A detailed, numbered list outlining the next actions the AI agents will take to solve and optimize the problem. This includes generating code to address the problem, executing the necessary steps, and iterating through improvements to refine the solution. It should also highlight specific focus areas such as generating algorithms, validating correctness, and ensuring the solution aligns with the stated goals."
    )


class AgentState(TypedDict):
    userInput: str
    iterations: int
    promptFiles: List[str]
    messages: List[str]
    purpose: Purpose
    proceed: ProceedOption
    