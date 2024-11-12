from enum import Enum
from typing import List, TypedDict, Optional
from pydantic import BaseModel, Field, Extra, validator


# Define an Enum for the proceed field
class ProceedOption(str, Enum):
    CONTINUE = "continue"
    CANCEL = "cancel"
    NEW = "new"
    DONE = "done"
    FIX = "fix"


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
    goal: str = Field(
        description="The core objective of the task, summarizing the user's real goal and the purpose of solving the task."
    )
    resource_requirements: str = Field(
        description="Specific requirements or allocations for the resource, such as how much is required for each task, order, or destination. This should include all the important details needed to solve the problem effectively."
    )


class Code(BaseModel):
    python_code: str = Field(
        description="Python code generated by the AI agents to solve the user's problem."
    )
    requirements: Optional[str] = Field(
        default="No requirements provided",  # Default value in case it's missing
        description="A list of requirements or dependencies needed to run the generated Python code, such as those used in a requirements.txt file.",
    )
    resources: Optional[str] = Field(
        default="No additional resources provided",  # Default value in case it's missing
        description="If no resources added, use default answer. Any additional requirements or files, such as data sheets (Excel files) or other resources, that are not included in the main requirements list but are necessary for the program.",
    )


class CodeFix(BaseModel):
    fixed_python_code: str = Field(
        description="Python code generated by the AI agents after fixing the user's problem."
    )
    requirements: Optional[str] = Field(
        default="No requirements provided",
        description="List of requirements or dependencies needed to run the fixed Python code, adjusted if necessary.",
    )
    requirements_changed: bool = Field(
        default=False,
        description="Indicates if requirements were changed to resolve the issue.",
    )
    fix_description: str = Field(
        description="Description of what was fixed, providing context for the changes made to the code."
    )
    original_error: str = Field(
        description="Summary of docker logs (provided error) what needed to be fixed and why."
    )


class DockerFiles(BaseModel):
    dockerfile: str = Field(
        description="The Dockerfile that defines the Docker environment for running the generated Python code."
    )
    compose_file: str = Field(
        description="The docker-compose.yaml file that specifies the services and configurations for the Docker environment."
    )


class OutputOfCode(BaseModel):
    answer: str = Field(
        description="The numerical answer, detailing the quantities or results of the calculation (e.g., how much material to cut)."
    )
    answer_description: str = Field(
        description="A very detailed explanation or context for the numerical answer, providing additional insights or interpretations of the result."
    )
    improvement: str = Field(
        description="Suggestions for enhancing the solution or optimization process."
    )
    objective_value: Optional[float] = Field(
        description="The objective value achieved by the optimization algorithm (e.g., the minimized waste or cost).",
        default=None,
    )
    explanation: str = Field(
        description="A detailed step-by-step explanation of how the algorithm arrived at the final result, describing key decisions and constraints."
    )
    is_goal_achieved: str = Field(
        description="Start with boolean value, but then explain why the goal is achieved or not.",
    )
    code: Optional[str] = Field(
        default=None,  # Empty value by default
        description="Earlier generated python code, this will be added later.",
    )


class FinalReport(BaseModel):
    index_of_optimization: int = Field(
        description="From all the optimizations, which one is the best. Use given index to find the best optimization."
    )
    reason: str = Field(description="Why this optimization is the best.")


class AgentState(TypedDict):
    userInput: str  # Original user input
    iterations: int  # Number of iterations (Not used yet)
    promptFiles: List[str]  # Given files whats been uploaded
    messages: List[str]
    purpose: Purpose  # What user want to achieve
    proceed: ProceedOption  # Enum
    code: Code  # Python code and requirements
    dockerFiles: DockerFiles  # DockerFile and compose.yaml
    docker_output: str  # What running code in docker container outputs
    result: OutputOfCode  # Results of the code execution - answer, explanation, etc.
    results: List[OutputOfCode]
