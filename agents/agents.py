import os
import subprocess
import chainlit as cl
from langchain.output_parsers import PydanticOutputParser
from prompts.prompts import (
    CODE_FIXER_PROMPT,
    CODE_PROMPT,
    CODE_PROMPT_NO_DATA,
    DOCKER_FILES_PROMPT,
    TASK_ANALYSIS_PROMPT,
    CODE_OUTPUT_ANALYSIS_PROMPT,
    NEW_LOOP_CODE_PROMPT,
    NEW_LOOP_CODE_PROMPT_NO_DATA,
    FINAL_REPORT_PROMPT,
)
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from schemas import AgentState, DockerFiles, Purpose, Code, OutputOfCode, FinalReport

# Load the environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini", disable_streaming=False)


# THIS FIRST AGENT HAVE MORE COMMENTS HOW IT WORKS, same style should be used in other agents
# Problem analyzer agent
@cl.step(name="Problem Analyzer Agent")  # decorator registers the function as a step
async def problem_analyzer_agent(state: AgentState):
    print("*** PROBLEM ANALYZER AGENT ***")
    current_step = cl.context.current_step  # Retrieves the current step from Chainlit
    userInput = state["userInput"]
    prompt_files = state["promptFiles"]

    # display the user's input and any provided files in the Chainlit interface
    current_step.input = (
        f"Analyzing the problem for the following input:\n{state['userInput']}\n\n"
        f"Prompt Files:\n{state['promptFiles']}"
    )

    prompt = TASK_ANALYSIS_PROMPT.format(user_input=userInput, data=prompt_files)

    # PydanticOutputParser: A LangChain utility that parses the LLM's output into a structured Pydantic model.
    output_parser = PydanticOutputParser(pydantic_object=Purpose)
    # Retrieves instructions for the LLM on how to format the output so that it can be parsed correctly.
    format_instructions = output_parser.get_format_instructions()

    # Append format instructions to the prompt
    prompt += f"\n\n{format_instructions}"

    # Collect the full response while streaming it
    full_response = ""

    # Asynchronously streams the LLM's response in chunks.
    async for chunk in llm.astream(prompt):
        if hasattr(chunk, "content"):
            # Streams each token (chunk of text) to the user interface in real-time,
            # allowing the user to see the response as it's generated.
            await current_step.stream_token(chunk.content)
            full_response += chunk.content

    # Once streaming is done, parse the full response using the output parser
    try:
        # Uses the output parser to parse the full response into the "Purpose" Pydantic model
        response = output_parser.parse(full_response)
    except Exception as e:
        await cl.Message(content=f"Error parsing response: {e}").send()
        return state  # or handle accordingly
    state["purpose"] = response

    # Extracting Information from the Parsed Response
    chatbot_response = response.chatbot_response
    next_steps = response.next_steps

    # Enhances readability by adding extra line breaks between steps.
    formatted_next_steps = next_steps.replace("\n", "\n\n")
    # Sends a message to the user
    await cl.Message(
        content=f"{chatbot_response}\n\n**Next Steps:**\n\n{formatted_next_steps}"
    ).send()

    # Asking the user how to proceed
    res = await cl.AskActionMessage(
        content="Sounds good, proceed?!",
        actions=[
            cl.Action(name="continue", value="continue", label="✅ Continue"),
            cl.Action(name="new", value="new", label="❌ Create new plan"),
            cl.Action(name="cancel", value="cancel", label="❌ Cancel and start over"),
        ],
    ).send()

    # Handling the user's response
    if res and res.get("value") == "continue":
        state["proceed"] = "continue"
    elif res and res.get("value") == "cancel":
        state["proceed"] = "cancel"
        await cl.Message(content="Alright, let's cancel this and start over!").send()
    else:
        state["proceed"] = "new"
        await cl.Message(content="Alright, let's create a new plan!").send()

    return state


# Code generator agent
# Generates Python code based on the user's problem analysis
@cl.step(name="Code Generator Agent")
async def code_generator_agent(state: AgentState):
    print("*** CODE GENERATOR AGENT ***")
    current_step = cl.context.current_step
    inputs = state["purpose"]

    if state["promptFiles"] == "":
        prompt = CODE_PROMPT_NO_DATA.format(
            user_summary=inputs.user_summary,
            problem_type=inputs.problem_type,
            optimization_focus=inputs.optimization_focus,
            next_steps=inputs.next_steps,
            resource_requirements=inputs.resource_requirements,
        )
    else:
        prompt = CODE_PROMPT.format(
            user_summary=inputs.user_summary,
            problem_type=inputs.problem_type,
            optimization_focus=inputs.optimization_focus,
            next_steps=inputs.next_steps,
            data=state["promptFiles"],
            resource_requirements=inputs.resource_requirements,
        )

    # Display input in the Chainlit interface
    current_step.input = (
        f"Generating code based on the following inputs:\n\n"
        f"User Summary: {inputs.user_summary}\n"
        f"Problem Type: {inputs.problem_type}\n"
        f"Optimization Focus: {inputs.optimization_focus}\n"
        f"Next Steps: {inputs.next_steps}\n"
        f"Data: {state['promptFiles']}"
    )

    # Set up the output parser
    output_parser = PydanticOutputParser(pydantic_object=Code)
    format_instructions = output_parser.get_format_instructions()

    # Append format instructions to the prompt
    prompt += f"\n\n{format_instructions}"

    # Collect the full response while streaming
    full_response = ""

    # Stream the response from the LLM
    try:
        async for chunk in llm.astream(prompt):
            if hasattr(chunk, "content"):
                await current_step.stream_token(chunk.content)
                full_response += chunk.content
    except Exception as e:
        await cl.Message(content=f"Error during code generation: {e}").send()
        return state

    # Parse the full response
    try:
        response = output_parser.parse(full_response)
    except Exception as e:
        await cl.Message(content=f"Error parsing code response: {e}").send()
        return state

    state["code"] = response

    # This function ensures the input text is safely encoded in UTF-8.
    def clean_text(text):
        return text.encode("utf-8", "replace").decode("utf-8")

    # Save the generated code and requirements to files
    with open("generated/generated.py", "w", encoding="utf-8") as f:
        f.write(clean_text(response.python_code))

    with open("generated/requirements.txt", "w", encoding="utf-8") as f:
        f.write(clean_text(response.requirements))

    return state


# Docker environment setup agent
# Generates necessary Docker files based on the generated code
@cl.step(name="Docker Environment Files Agent")
async def docker_environment_files_agent(state: AgentState):
    print("*** DOCKER ENVIRONMENT AGENT ***")
    current_step = cl.context.current_step
    inputs = state["code"]

    # Prepare the prompt
    prompt = DOCKER_FILES_PROMPT.format(
        python_code=inputs.python_code,
        requirements=inputs.requirements,
        resources=inputs.resources,
    )

    # Display input in the Chainlit interface
    current_step.input = (
        f"Generating Docker environment files based on the following inputs:\n\n"
        f"Python Code:\n```python\n{inputs.python_code}\n```\n"
        f"Requirements:\n```\n{inputs.requirements}\n```\n"
        f"Resources: {inputs.resources}"
    )

    # Set up the output parser
    output_parser = PydanticOutputParser(pydantic_object=DockerFiles)
    format_instructions = output_parser.get_format_instructions()

    # Append format instructions to the prompt
    prompt += f"\n\n{format_instructions}"

    # Collect the full response while streaming
    full_response = ""

    # Stream the response from the LLM
    try:
        async for chunk in llm.astream(prompt):
            if hasattr(chunk, "content"):
                await current_step.stream_token(chunk.content)
                full_response += chunk.content
    except Exception as e:
        await cl.Message(content=f"Error during Docker files generation: {e}").send()
        return state

    # Parse the full response
    try:
        response = output_parser.parse(full_response)
    except Exception as e:
        await cl.Message(content=f"Error parsing Docker files response: {e}").send()
        return state

    state["docker_files"] = response

    # Save the Dockerfile and Compose file
    with open("generated/Dockerfile", "w", encoding="utf-8") as f:
        f.write(response.dockerfile)

    with open("generated/compose.yaml", "w", encoding="utf-8") as f:
        f.write(response.compose_file)

    return state


# Start Docker container agent
# Executes the generated code in a Docker container - output results
@cl.step(name="Start Docker Container Agent")
async def start_docker_container_agent(state: AgentState):
    print("*** START DOCKER CONTAINER AGENT ***")
    current_step = cl.context.current_step

    # Display input in the Chainlit interface
    current_step.input = "Starting Docker container to execute the generated code."

    os.chdir("generated")
    full_output = ""

    try:
        # Build the Docker image
        print("Building Docker image...")
        build_command = ["docker-compose", "build"]
        build_process = subprocess.Popen(
            build_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        # Loops through each line of stdout from the build process
        for line in build_process.stdout:
            print(line, end="")
            full_output += line
            await current_step.stream_token(line)

        build_process.wait()

        # check if the build process was successful (0 is success)
        if build_process.returncode != 0:
            raise Exception("Docker image build failed")

        # Run the Docker container
        print("Running Docker container...")
        up_command = [
            "docker-compose",
            "up",
            "--abort-on-container-exit",
            "--no-log-prefix",
        ]
        up_process = subprocess.Popen(
            up_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        for line in up_process.stdout:
            print(line, end="")
            full_output += line
            await current_step.stream_token(line)

        up_process.wait()
        if up_process.returncode != 0:
            raise Exception("Docker container execution failed")

        state["docker_output"] = full_output

    except Exception as e:
        print(f"An error occurred: {e}")
        state["docker_output"] = str(e)
        await cl.Message(content=f"An error occurred: {e}").send()

    finally:
        # Clean up Docker resources
        down_command = ["docker-compose", "down"]
        subprocess.run(down_command)
        # Prune dangling images (those with the same name but unused)
        prune_command = ["docker", "image", "prune", "-f"]
        subprocess.run(prune_command)
        os.chdir("..")

    return state


# Code output analyzer agent
@cl.step(name="Code Output Analyzer Agent")
async def code_output_analyzer_agent(state: AgentState):
    print("*** CODE OUTPUT ANALYZER AGENT ***")
    current_step = cl.context.current_step
    docker_output = state["docker_output"]

    # Prepare the prompt
    prompt = CODE_OUTPUT_ANALYSIS_PROMPT.format(
        user_summary=state["purpose"].user_summary,
        original_goal=state["purpose"].goal,
        next_steps=state["purpose"].next_steps,
        code_output=docker_output,
    )

    # Display input in the Chainlit interface
    current_step.input = (
        f"Analyzing the code output based on the following inputs:\n\n"
        f"User Summary: {state['purpose'].user_summary}\n"
        f"Original Goal: {state['purpose'].goal}\n"
        f"Next Steps: {state['purpose'].next_steps}\n"
        f"Code Output:\n```\n{docker_output}\n```"
    )

    # Set up the output parser
    output_parser = PydanticOutputParser(pydantic_object=OutputOfCode)
    format_instructions = output_parser.get_format_instructions()

    # Append format instructions to the prompt
    prompt += f"\n\n{format_instructions}"

    # Collect the full response while streaming
    full_response = ""

    # Stream the response from the LLM
    try:
        async for chunk in llm.astream(prompt):
            if hasattr(chunk, "content"):
                await current_step.stream_token(chunk.content)
                full_response += chunk.content
    except Exception as e:
        await cl.Message(content=f"Error during code output analysis: {e}").send()
        return state

    # Parse the full response
    try:
        response = output_parser.parse(full_response)
        response.code = state["code"].python_code
    except Exception as e:
        await cl.Message(
            content=f"Error parsing code output analysis response: {e}"
        ).send()
        return state

    state["result"] = response

    if "results" not in state:
        state["results"] = []

    state["results"].append(response)

    # Display the analysis result to the user
    await cl.Message(content=f"Analysis Result:\n{response.answer_description}").send()

    # Ask the user if they want to start a new optimization round
    res = await cl.AskActionMessage(
        content="Let's begin a new optimization round?",
        actions=[
            cl.Action(
                name="continue", value="continue", label="✅ Yes, let's continue"
            ),
            cl.Action(name="done", value="done", label="❌ This is enough for now"),
        ],
    ).send()

    # Handle the user's response
    if res and res.get("value") == "continue":
        state["proceed"] = "continue"
        await cl.Message(content="Starting new optimization round!").send()
    else:
        state["proceed"] = "done"
        await cl.Message(
            content="Generating the final report! We are done for now."
        ).send()

    return state


# New loop agent
# Starts a new optimization round based on the previous results and code
@cl.step(name="New Loop Agent")
async def new_loop_agent(state: AgentState):
    print("*** NEW LOOP AGENT ***")
    current_step = cl.context.current_step
    inputs = state["purpose"]
    last_code = state["code"]
    last_output = state["result"]

    if state["promptFiles"] == "":
        prompt = NEW_LOOP_CODE_PROMPT_NO_DATA.format(
            user_summary=inputs.user_summary,
            problem_type=inputs.problem_type,
            optimization_focus=inputs.optimization_focus,
            next_steps=inputs.next_steps,
            previous_results=last_output.answer_description,
            previous_code=last_code.python_code,
            resource_requirements=inputs.resource_requirements,
        )
    else:
        prompt = NEW_LOOP_CODE_PROMPT.format(
            user_summary=inputs.user_summary,
            problem_type=inputs.problem_type,
            optimization_focus=inputs.optimization_focus,
            next_steps=inputs.next_steps,
            data=state["promptFiles"],
            previous_results=last_output.answer_description,
            previous_code=last_code.python_code,
            resource_requirements=inputs.resource_requirements,
        )

    # Display input in the Chainlit interface
    current_step.input = (
        f"Starting a new optimization round with the following inputs:\n\n"
        f"User Summary: {inputs.user_summary}\n"
        f"Problem Type: {inputs.problem_type}\n"
        f"Optimization Focus: {inputs.optimization_focus}\n"
        f"Next Steps: {inputs.next_steps}\n"
        f"Data: {state['promptFiles']}\n"
        f"Previous Results: {last_output.answer_description}\n"
        f"Previous Code:\n```python\n{last_code.python_code}\n```"
    )

    # Set up the output parser
    output_parser = PydanticOutputParser(pydantic_object=Code)
    format_instructions = output_parser.get_format_instructions()
    print(format_instructions)

    # Append format instructions to the prompt
    prompt += f"\n\n{format_instructions}"

    print("Prompt:")
    print(prompt)

    # Collect the full response while streaming
    full_response = ""

    # Stream the response from the LLM
    try:
        async for chunk in llm.astream(prompt):
            if hasattr(chunk, "content"):
                await current_step.stream_token(chunk.content)
                full_response += chunk.content
    except Exception as e:
        await cl.Message(content=f"Error during new optimization round: {e}").send()
        return state

    def clean_text(text):
        return text.encode("utf-8", "replace").decode("utf-8")

    # Clean the full response before parsing
    cleaned_response = clean_text(full_response)

    # Parse the full response
    try:
        response = output_parser.parse(cleaned_response)
    except Exception as e:
        await cl.Message(content=f"Error parsing new code response: {e}").send()
        print("Error parsing new code response")
        print(e)
        return state

    state["code"] = response

    # Display the new code and requirements
    await cl.Message(
        content=f"New Generated Code:\n```python\n{response.python_code}\n```"
    ).send()
    await cl.Message(
        content=f"New Requirements:\n```\n{response.requirements}\n```"
    ).send()

    # Save the new code and requirements to files
    with open("generated/generated.py", "w", encoding="utf-8") as f:
        f.write(response.python_code)

    with open("generated/requirements.txt", "w", encoding="utf-8") as f:
        f.write(response.requirements)
    print("New Loop Agent done")
    return state


# Final report, decide which optimization is best and why
# This agent is the last agent in the chain
# Should provide a final report and code for the best optimization
async def final_report_agent(state: AgentState):
    print("*** FINAL REPORT AGENT ***")
    current_step = cl.context.current_step
    results = state["results"]
    user_input = state["userInput"]
    current_step.input = (
        "Generating the final report based on the optimization results."
    )

    # Let LLM choose which optimization is the best, so convert results to format that LLM can use for comparison
    # Main criteria for comparison: objective_value, answer, is_goal_achieved
    comparison_data = []
    for result in results:
        comparison_data.append(
            {
                "index": results.index(result) + 1,
                "objective_value": result.objective_value,
                "answer": result.answer,
                "is_goal_achieved": result.is_goal_achieved,
            }
        )

    print(comparison_data)

    prompt = FINAL_REPORT_PROMPT.format(
        user_input=user_input, summaries_of_optimizations=comparison_data
    )

    # Set up the output parser
    output_parser = PydanticOutputParser(pydantic_object=FinalReport)
    format_instructions = output_parser.get_format_instructions()

    # Append format instructions to the prompt
    prompt += f"\n\n{format_instructions}"

    full_response = ""

    # Stream the response from the LLM
    try:
        async for chunk in llm.astream(prompt):
            if hasattr(chunk, "content"):
                await current_step.stream_token(chunk.content)
                full_response += chunk.content
    except Exception as e:
        await cl.Message(content=f"Error during new optimization round: {e}").send()
        return state

        # Parse the full response
    try:
        response = output_parser.parse(full_response)
    except Exception as e:
        await cl.Message(content=f"Error parsing new code response: {e}").send()
        return state

    print(response)
    index_of_best_optimization = response.index_of_optimization
    best_optimization = results[index_of_best_optimization - 1]

    # Send the final report to the user
    await cl.Message(content=best_optimization.code, language="python").send()

    return state


# If error occurs during code execution in the Docker container
async def code_fixer_agent(state: AgentState):
    print("*** CODE FIXER AGENT ***")

    current_step = cl.context.current_step

    code = state["code"]
    docker_output = state["docker_output"]

    current_step.input = (
        "Fixing the code based on the error encountered during execution."
    )

    prompt = CODE_FIXER_PROMPT.format(
        code=code.python_code, docker_output=docker_output
    )

    # PydanticOutputParser: A LangChain utility that parses the LLM's output into a structured Pydantic model.
    output_parser = PydanticOutputParser(pydantic_object=Code)
    # Retrieves instructions for the LLM on how to format the output so that it can be parsed correctly.
    format_instructions = output_parser.get_format_instructions()

    prompt += f"\n\n{format_instructions}"

    full_response = ""

    # Stream the response from the LLM
    try:
        async for chunk in llm.astream(prompt):
            if hasattr(chunk, "content"):
                await current_step.stream_token(chunk.content)
                full_response += chunk.content
    except Exception as e:
        await cl.Message(content=f"Error during code generation: {e}").send()
        return state

    # Parse the full response
    try:
        response = output_parser.parse(full_response)
    except Exception as e:
        await cl.Message(content=f"Error parsing code response: {e}").send()
        return state

    state["code"] = response

    # This function ensures the input text is safely encoded in UTF-8.
    def clean_text(text):
        return text.encode("utf-8", "replace").decode("utf-8")

    # Save the generated code and requirements to files
    with open("generated/generated.py", "w", encoding="utf-8") as f:
        f.write(clean_text(response.python_code))
