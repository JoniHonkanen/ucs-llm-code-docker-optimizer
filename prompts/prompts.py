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

CODE_PROMPT = ChatPromptTemplate.from_template(
    """
    Your task is to generate Python code that solves the optimization problem described by the user, using either PuLP (for linear programming) or heuristic algorithms (e.g., genetic algorithms, simulated annealing) depending on the problem's complexity and requirements.

    Based on the user's input and the provided files (e.g., Python code, Excel sheets), generate Python code that implements either exact optimization (using PuLP) or heuristic algorithms where an approximate solution is more practical. The goal is to develop a solution that efficiently addresses the problem's constraints and objectives.

    The code must be fully functional and structured to solve the task optimally or near-optimally, depending on the method chosen. You should also define any necessary test parameters derived from the user input or provided files to validate the solution.

    Summary of the user's input:
    {user_summary}

    Problem type identified in earlier analysis:
    {problem_type}

    Optimization focus:
    {optimization_focus}

    Planned next steps for solving the problem:
    {next_steps}

    Provided data (Python code, Excel files, or may be empty):
    {data}
    


    Key points to address:
    - What is the optimization problem, and what constraints or requirements need to be considered?
    - Should the solution use PuLP for exact optimization, or is a heuristic algorithm more appropriate for solving this problem?
    - How should the code structure reflect the optimization method to ensure clarity and efficiency?
    - Define parameters for testing, based on user input or the provided files, to validate the optimization approach.
    - What packages or libraries are required for requirements.txt to run the generated Python code?
    """
)

DOCKER_FILES_PROMPT = ChatPromptTemplate.from_template(
    """
    Your task is to create the necessary Docker environment files to run the Python code generated for the optimization problem. This includes creating a Dockerfile and a compose.yaml file. Requirements.txt (in Generated requirements part) file have defined the project's dependencies.

    Start by creating a Dockerfile that specifies the base image, environment setup, and commands needed to run the Python code. Ensure that the Dockerfile includes all the necessary configurations to execute the generated code successfully.

    Then, create a compose.yaml file that sets up the Docker container for the Python code and includes folder watching functionality. This should ensure that the container automatically detects changes to the code or files in the specified folder and restarts if necessary.

    The generated Python code will always be saved as **generated.py**, so your Dockerfile and compose.yaml should be set up accordingly.

    Here’s an example of how folder watching can be added in the compose.yaml file:
    ```yaml
    develop:
      watch:
        - action: sync
          path: ./*.py  # Watch for changes in Python files
          target: /app
        - action: rebuild
          path: requirements.txt  # Rebuild if dependencies change
    ```

    Generated Python code:
    {python_code}

    Generated requirements (requirements.txt):
    {requirements}

    Key tasks:
    - Create a Dockerfile with the necessary configurations to run the generated Python code.
    - Create a compose.yaml file (Docker Compose V2) that enables folder watching and automatically restarts the container on code changes.
    - Ensure the setup is ready for local testing by building and running the container.
    """
)
