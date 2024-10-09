from langchain_core.prompts import ChatPromptTemplate

TASK_ANALYSIS_PROMPT = ChatPromptTemplate.from_template(
    """
    Your task is to carefully analyze the user's input and any provided data to understand the problem they are trying to solve. The task could involve logistics process optimization (e.g., finding the shortest or fastest routes), the cutting stock problem, or other similar challenges.

    First, identify the core purpose of the task and what the user ultimately wants to achieve. Summarize the user's real objective in your own words, based on the task description and any available data (Python code, Excel files, or no data at all). If no data is provided, think about what might be missing to solve the task.

    Once the goal is clear, consider how the provided data can be used to optimize the solution, focusing on improving how well the problem is solved. Do not prioritize runtime or performance metrics, but instead aim to enhance the quality and effectiveness of the solution.

    User task description:
    {user_input}

    Provided data (can be Python code, Excel files, or may be empty):
    {data}

    Key objectives:
    - What is the user trying to achieve with this task? (Summarize the user's real objective)
    - What is the purpose of solving this task?
    - How can the solution be optimized to achieve the best result, focusing on quality and problem-solving?
    """
)


