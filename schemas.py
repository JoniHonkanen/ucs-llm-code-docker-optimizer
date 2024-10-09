from typing import TypedDict, List


class AgentState(TypedDict):
    userInput: str
    iterations: int
    promptFiles: List[str]
    messages: List[str]
