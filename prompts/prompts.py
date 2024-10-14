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

    If the provided files include data sheets (e.g., Excel files), ensure that the necessary packages for file handling (such as pandas or openpyxl) are included, and the code correctly handles file input/output as part of the solution. **It is suggested to explicitly specify file-handling options like using the 'openpyxl' engine for reading `.xlsx` files and ensuring no encoding issues arise by avoiding the default 'charmap' codec or potential encoding conflicts**. The LLM must analyze the files and understand how to process them appropriately.

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
    - What packages or libraries are required for requirements.txt to run the generated Python code, including any necessary for file handling (e.g., pandas, openpyxl) if provided data includes Excel or other files? Ensure to handle potential encoding issues in file reading to avoid errors.
    """
)


DOCKER_FILES_PROMPT = ChatPromptTemplate.from_template(
    """
    Your task is to create the necessary Docker environment files to run the Python code generated for the optimization problem. This includes creating a Dockerfile and a compose.yaml file. The requirements.txt file (in the Generated requirements part) has defined the project's dependencies.

    Start by creating a Dockerfile that specifies the base image, environment setup, and commands needed to run the Python code. Ensure that the Dockerfile includes all the necessary configurations to execute the generated code successfully.

    Then, create a compose.yaml file that sets up the Docker container for the Python code. The compose.yaml should define the services and configurations needed to build and run the code.

    The generated Python code will always be saved as **generated.py**, so your Dockerfile and compose.yaml should be set up accordingly.

    For example:
    ```yaml
    services:
      app:
        build: .
        container_name: my-python-app
        command: python /app/generated.py  # Modify the command as per your project
    ```

    Generated Python code:
    {python_code}

    Generated requirements (requirements.txt):
    {requirements}
    
    Remember to include any additional resources or files that are required to run the Python code but are not listed in the main requirements.
    {resources}

    Key tasks:
    - Create a Dockerfile with the necessary configurations to run the generated Python code.
    - Create a compose.yaml file (Docker Compose V2) that defines the services to build and run the code.
    - Ensure the setup is ready for local testing by building and running the container.
    """
)

CODE_OUTPUT_ANALYSIS_PROMPT = ChatPromptTemplate.from_template(
    """
    Your task is to analyze the output generated by the Python code and parse the relevant information, such as numerical results or tables, to directly answer the user's question. This involves examining the output data, identifying any issues or discrepancies, and providing insights into the quality of the solution.

    **Original Question:**
    {user_summary}

    **Output of the Code:**
    {code_output}

    **Instructions:**

    - **Parse the Numerical Results or Tables:** 
      - Extract the relevant numerical answers or tables from the code output (e.g., how materials should be cut, total waste, objective value, etc.).
      - Present these results clearly and concisely.
    - **Answer the Original Question:** 
      - Based on the parsed results, provide a clear and direct answer to the user's question.
    - **Evaluate the Output Data:** 
      - Does the output data look correct and logically consistent?
      - Are there any issues, errors, or discrepancies present?
    - **Assess the Solution:**
      - Has the original question or problem been effectively solved?
      - How well does the solution meet the requirements?
    - **Summarize the Results:** 
      - Highlight key findings or outputs from the code (e.g., how the materials were allocated, total waste, etc.).
      - Provide any relevant metrics or outcomes.
    - **Provide Insights and Recommendations:** 
      - Offer any observations about the quality or efficiency of the solution.
      - Suggest possible improvements or next steps if applicable.

    **Your response should be thorough, accurate, and suitable for use in further analysis or decision-making.**
    """
)
