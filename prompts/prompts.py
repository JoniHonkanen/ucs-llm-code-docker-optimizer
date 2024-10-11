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

    If the provided files include data sheets (e.g., Excel files), ensure that the necessary packages for file handling (such as pandas or openpyxl) are included, and the code correctly handles file input/output as part of the solution. LLM must analyze the files and understand how to process them appropriately.

    In your response, generate the following fields:
    - **python_code**: The fully functional Python code that solves the user's problem.
    - **requirements**: A comprehensive list of all Python packages or dependencies (e.g., pandas, PuLP, openpyxl) needed to run the generated Python code. This will be used to create a requirements.txt file.
    - **resources**: List any additional files, resources, or external data (e.g., Excel sheets) that the code requires to run successfully.

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
    - What packages or libraries are required for requirements.txt to run the generated Python code, including any necessary for file handling (e.g., pandas, openpyxl) if provided data includes Excel or other files?
    """
)


DOCKER_FILES_PROMPT = ChatPromptTemplate.from_template(
    """
    Your task is to create the necessary Docker environment files to run the Python code generated for the optimization problem. This includes creating a Dockerfile and a compose.yaml file. Requirements.txt (in Generated requirements part) file have defined the project's dependencies.

    Start by creating a Dockerfile that specifies the base image, environment setup, and commands needed to run the Python code. Ensure that the Dockerfile includes all the necessary configurations to execute the generated code successfully.

    Then, create a compose.yaml file that sets up the Docker container for the Python code and includes folder watching functionality. This should ensure that the container automatically detects changes to the code or files in the specified folder and restarts if necessary.

    The generated Python code will always be saved as **generated.py**, so your Dockerfile and compose.yaml should be set up accordingly.

- The Docker Compose `watch` feature under the `develop` section to automatically handle file changes. For example:
    ```yaml
services:
  app:
    build: .
    container_name: my-python-app
    volumes:
      - .:/app
    command: python /app/generated.py  # Modify the command as per your project
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
    
    Remember to include any additional resources or files that are required to run the Python code but are not listed in the main requirements.
    {resources}

    Key tasks:
    - Create a Dockerfile with the necessary configurations to run the generated Python code.
    - Create a compose.yaml file (Docker Compose V2) that enables folder watching and automatically restarts the container on code changes.
    - Ensure the setup is ready for local testing by building and running the container.
    """
)
