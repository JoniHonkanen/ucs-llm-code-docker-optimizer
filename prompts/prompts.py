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

    The code **must use the provided data (including resources, orders, and any other numeric values or relevant details)** to accurately represent the problem. The solution should ensure that all provided data are appropriately utilized, whether they pertain to materials, quantities, measurements, or any other key factors relevant to the user's task.
    Provided data (Python code, Excel files, or may be empty)
    {data}
    
    Resource Requirements:
    {resource_requirements}
    
    **Note:** The **Resource Requirements and data** sections is very important for the generated code. It details thkey resources available (e.g., materials, vehicles, personnel) and specific requirements (e.g.quantities, sizes) that must be fulfilled to solve the problem. The generated code must prioritize thesresource requirements when forming the solution, ensuring that all available resources are utilizeefficiently and constraints are respected.

    ### Important Instructions
    **Do not include code block formatting (e.g., `````json ... `````) in your response.** Only output the plain JSON object.
    
    Key points to address:
    - What is the optimization problem, and what constraints or requirements need to be considered?
    - Should the solution use PuLP for exact optimization, or is a heuristic algorithm more appropriate for solving this problem?
    - How should the code structure reflect the optimization method to ensure clarity and efficiency?
    - Define parameters for testing, based on user input or the provided files, to validate the optimization approach.
    - What packages or libraries are required for requirements.txt to run the generated Python code, including any necessary for file handling (e.g., pandas, openpyxl) if provided data includes Excel or other files? Ensure to handle potential encoding issues in file reading to avoid errors.
    - **Make sure the code outputs the final result clearly (e.g., using print statements or by returning the result in a structured format like a table or numerical answer).**
    """
)

CODE_PROMPT_NO_DATA = ChatPromptTemplate.from_template(
    """
    Your task is to generate Python code that solves the optimization problem described by the user, using either PuLP (for linear programming) or heuristic algorithms (e.g., genetic algorithms, simulated annealing) depending on the problem's complexity and requirements.

    Based on the user's input, generate Python code that implements either exact optimization (using PuLP) or heuristic algorithms where an approximate solution is more practical. The goal is to develop a solution that efficiently addresses the problem's constraints and objectives.

    The code must be fully functional and structured to solve the task optimally or near-optimally, depending on the method chosen. You should also define any necessary test parameters derived from the user input to validate the solution.

    In your response, generate the following fields:
    - **python_code**: The fully functional Python code that solves the user's problem.
    - **requirements**: A comprehensive list of all Python packages or dependencies (e.g., pandas, PuLP) needed to run the generated Python code. This will be used to create a requirements.txt file.

    Summary of the user's input:
    {user_summary}

    Problem type identified in earlier analysis:
    {problem_type}

    Optimization focus:
    {optimization_focus}

    Planned next steps for solving the problem:
    {next_steps}
    
    Resource Requirements:
    {resource_requirements}
    
    **Note:** The **Resource Requirements** section is very important for the generated code. It details thkey resources available (e.g., materials, vehicles, personnel) and specific requirements (e.g.quantities, sizes) that must be fulfilled to solve the problem. The generated code must prioritize thesresource requirements when forming the solution, ensuring that all available resources are utilizeefficiently and constraints are respected.

    The code **must accurately represent the problem** based on the user's input, ensuring that all key factors (e.g., materials, quantities, constraints) relevant to the user's task are considered.
    
    ### Important Instructions
    **Do not include code block formatting (e.g., `````json ... `````) in your response.** Only output the plain JSON object.
    
    Key points to address:
    - What is the optimization problem, and what constraints or requirements need to be considered?
    - Should the solution use PuLP for exact optimization, or is a heuristic algorithm more appropriate for solving this problem?
    - How should the code structure reflect the optimization method to ensure clarity and efficiency?
    - Define parameters for testing, based on user input, to validate the optimization approach.
    - What packages or libraries are required for requirements.txt to run the generated Python code?
    - **Make sure the code outputs the final result clearly (e.g., using print statements or by returning the result in a structured format like a table or numerical answer).**
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
    
    **Original Goal:**
    {original_goal}
    
    **Planned steps (we should be in last steps now):
    {next_steps}

    **Output of the Code:**
    {code_output}

**Instructions:**

- **Parse the Numerical Results or Tables:** 
  - Extract the relevant numerical answers or tables from the code output (e.g., how materials should be cut, total waste, objective value, etc.).
  - Present these results clearly and concisely.
- **Check against the Planned Steps:**
  - Verify that the final output reflects the steps outlined in "planned steps part".
  - Ensure that the results match the plan and that each step in the process has been executed correctly.
  - If any planned steps were skipped or not fully implemented, provide details.
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

**Your response should be thorough, accurate, and suitable for use in further analysis or decision-making.**
    """
)

NEW_LOOP_CODE_PROMPT = ChatPromptTemplate.from_template(
    """
    Your task is to generate Python code that solves the optimization problem described by the user, using either PuLP (for linear programming) or heuristic algorithms (e.g., genetic algorithms, simulated annealing) depending on the problem's complexity and requirements.

    You should also take into account the results from previous optimization iterations to further improve the solution. Analyze the previously generated results (e.g., cutting patterns, waste minimization, resource utilization) and incorporate those insights into the next round of optimization. Ensure that the new solution is an improvement over the prior result and **does not duplicate any previous code**.

    Based on the user's input, the provided files (e.g., Python code, Excel sheets), and the outcomes from the previous iteration(s), generate Python code that implements either exact optimization (using PuLP) or heuristic algorithms where an approximate solution is more practical. The goal is to develop a solution that efficiently addresses the problem's constraints and objectives, while **explicitly improving on the last used code**.

    The new code must:
    - Be fully functional and structured to solve the task optimally or near-optimally, depending on the method chosen.
    - Avoid duplicating any parts of the previous code and **explicitly comment on what improvements have been made** in terms of efficiency, structure, or the optimization goal (e.g., less waste, faster routes).
    - Define any necessary test parameters derived from the user input, provided files, and previous results to validate the new solution.

    If the provided files include data sheets (e.g., Excel files), ensure that the necessary packages for file handling (such as pandas or openpyxl) are included, and the code correctly handles file input/output as part of the solution. **It is suggested to explicitly specify file-handling options like using the 'openpyxl' engine for reading `.xlsx` files and ensuring no encoding issues arise by avoiding the default 'charmap' codec or potential encoding conflicts**. The LLM must analyze the files and understand how to process them appropriately.

    In your response, generate the following fields:
    - **python_code**: The fully functional Python code that solves the user's problem, improving on previous iterations and avoiding duplication of the last used code.
    - **requirements**: A comprehensive list of all Python packages or dependencies (e.g., pandas, PuLP, openpyxl) needed to run the generated Python code. This will be used to create a requirements.txt file.
    - **resources**: List any additional files, resources, or external data (e.g., Excel sheets) that the code requires to run successfully.

    **Original user input:**
    {user_summary}

    **Original problem type:**
    {problem_type}

    **Original optimization focus:**
    {optimization_focus}

    **Original planned next steps:**
    {next_steps}

    **Results from prior optimizations:**
    {previous_results}
    
    **Last used code:**
    {previous_code}

    The code **must use the provided data (including resources, orders, and any other numeric values or relevant details)** to accurately represent the problem. The solution should ensure that all provided data are appropriately utilized, whether they pertain to materials, quantities, measurements, or any other key factors relevant to the user's task. The previous optimization results should also guide the current solution in refining the approach.
    
    Provided data (Python code, Excel files, or may be empty):
    {data}
    
    Resource Requirements:
    {resource_requirements}
    
    **Note:** The **Resource Requirements** section is very important for the generated code. It details thkey resources available (e.g., materials, vehicles, personnel) and specific requirements (e.g.quantities, sizes) that must be fulfilled to solve the problem. The generated code must prioritize thesresource requirements when forming the solution, ensuring that all available resources are utilizeefficiently and constraints are respected.
    
    ### Important Instructions
    **Do not include code block formatting (e.g., `````json ... `````) in your response.** Only output the plain JSON object.
    
    Key points to address:
    - What is the optimization problem, and what constraints or requirements need to be considered?
    - Should the solution use PuLP for exact optimization, or is a heuristic algorithm more appropriate for solving this problem?
    - **How does the new code differ from the last used code?** What improvements have been made to avoid duplication and enhance the previous solution?
    - Define parameters for testing, based on user input, the provided files, and the results of previous optimizations, to validate the new solution.
    - What packages or libraries are required for requirements.txt to run the generated Python code, including any necessary for file handling (e.g., pandas, openpyxl) if provided data includes Excel or other files? Ensure to handle potential encoding issues in file reading to avoid errors.
    - **Make sure the code outputs the final result clearly (e.g., using print statements or by returning the result in a structured format like a table or numerical answer), with improvements from the previous iteration and no duplication.**
    - Ensure the generated Python code is **free from syntax errors**. All functions should be properly defined, and indentation should follow Python's strict indentation rules. Ensure all variables, function definitions, and imports are correctly structured.
    """
)

NEW_LOOP_CODE_PROMPT_NO_DATA = ChatPromptTemplate.from_template(
    """
    Your task is to generate Python code that solves the optimization problem described by the user, using either PuLP (for linear programming) or heuristic algorithms (e.g., genetic algorithms, simulated annealing) depending on the problem's complexity and requirements.

    You should also take into account the results from previous optimization iterations to further improve the solution. Analyze the previously generated results (e.g., cutting patterns, waste minimization, resource utilization) and incorporate those insights into the next round of optimization. Ensure that the new solution is an improvement over the prior result and **does not duplicate any previous code**.

    Based on the user's input and the outcomes from the previous iteration(s), generate Python code that implements either exact optimization (using PuLP) or heuristic algorithms where an approximate solution is more practical. The goal is to develop a solution that efficiently addresses the problem's constraints and objectives, while **explicitly improving on the last used code**.

    The new code must:
    - Be fully functional and structured to solve the task optimally or near-optimally, depending on the method chosen.
    - Avoid duplicating any parts of the previous code and **explicitly comment on what improvements have been made** in terms of efficiency, structure, or the optimization goal (e.g., less waste, faster routes).
    - Define any necessary test parameters derived from the user input and previous results to validate the new solution.

    In your response, generate the following fields:
    - **python_code**: The fully functional Python code that solves the user's problem, improving on previous iterations and avoiding duplication of the last used code.
    - **requirements**: A comprehensive list of all Python packages or dependencies (e.g., pandas, PuLP) needed to run the generated Python code. This will be used to create a requirements.txt file.

    **Original user input:**
    {user_summary}

    **Original problem type:**
    {problem_type}

    **Original optimization focus:**
    {optimization_focus}

    **Original planned next steps:**
    {next_steps}

    **Results from prior optimizations:**
    {previous_results}
    
    **Last used code:**
    {previous_code}

    The code **must accurately represent the problem** based on the user's input, ensuring that all key factors (e.g., materials, quantities, constraints) relevant to the user's task are considered. The previous optimization results should also guide the current solution in refining the approach.

    Resource Requirements:
    {resource_requirements}
    
    **Note:** The **Resource Requirements** section is very important for the generated code. It details the key resources available (e.g., materials, vehicles, personnel) and specific requirements (e.g., quantities, sizes) that must be fulfilled to solve the problem. The generated code must prioritize these resource requirements when forming the solution, ensuring that all available resources are utilized efficiently and constraints are respected.
    
    ### Important Instructions
    **Do not include code block formatting (e.g., `````json ... `````) in your response.** Only output the plain JSON object.
    
    Key points to address:
    - What is the optimization problem, and what constraints or requirements need to be considered?
    - Should the solution use PuLP for exact optimization, or is a heuristic algorithm more appropriate for solving this problem?
    - **How does the new code differ from the last used code?** What improvements have been made to avoid duplication and enhance the previous solution?
    - Define parameters for testing, based on user input and the results of previous optimizations, to validate the new solution.
    - What packages or libraries are required for requirements.txt to run the generated Python code?
    - **Make sure the code outputs the final result clearly (e.g., using print statements or by returning the result in a structured format like a table or numerical answer), with improvements from the previous iteration and no duplication.**
    - Ensure the generated Python code is **free from syntax errors**. All functions should be properly defined, and indentation should follow Python's strict indentation rules. Ensure all variables, function definitions, and imports are correctly structured.

    """
)

FINAL_REPORT_PROMPT = ChatPromptTemplate.from_template(
    """
    Given the user's task:
    {user_input}

    And the following optimization codes:
    {summaries_of_optimizations}

    Your final report should include:

    1. **Performance Comparison**: Evaluate and compare the results of each optimization method, focusing on key metrics such as speed, memory usage, and task accuracy.
    2. **Best Optimization**: Identify the best optimization for the task, providing a clear explanation of why it is the most effective based on the comparison.
    3. **Visualization**: If applicable, include a visualization that clearly illustrates the performance differences between the optimizations.
    4. **Conclusion and Recommendations**: Summarize your findings and suggest potential improvements or note any limitations.

    The report should be concise, structured, and actionable, with a focus on addressing the user's specific task.
    """
)
