import os
import subprocess
import chainlit as cl
from langchain.output_parsers import PydanticOutputParser
from prompts.prompts import (
    CODE_PROMPT,
    DOCKER_FILES_PROMPT,
    TASK_ANALYSIS_PROMPT,
    CODE_OUTPUT_ANALYSIS_PROMPT,
    NEW_LOOP_CODE_PROMPT,
)
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from schemas import AgentState, DockerFiles, Purpose, Code, OutputOfCode

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
    # Output the final result after streaming is complete
    current_step.output = response

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
        await cl.Message(content="Let's proceed with this plan!").send()
    elif res and res.get("value") == "cancel":
        state["proceed"] = "cancel"
        await cl.Message(content="Alright, let's cancel this and start over!").send()
    else:
        state["proceed"] = "new"
        await cl.Message(content="Alright, let's create a new plan!").send()

    return state


# Code generator agent
@cl.step(name="Code Generator Agent")
async def code_generator_agent(state: AgentState):
    print("*** CODE GENERATOR AGENT ***")
    current_step = cl.context.current_step
    inputs = state["purpose"]

    # Prepare the prompt
    prompt = CODE_PROMPT.format(
        user_summary=inputs.user_summary,
        problem_type=inputs.problem_type,
        optimization_focus=inputs.optimization_focus,
        next_steps=inputs.next_steps,
        data=state["promptFiles"],
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

    # Output the final result
    current_step.output = response

    # Save the generated code and requirements to files
    with open("generated/generated.py", "w", encoding="utf-8") as f:
        f.write(response.python_code)

    with open("generated/requirements.txt", "w", encoding="utf-8") as f:
        f.write(response.requirements)

    return state


# Docker environment setup agent
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

    # Output the final result
    current_step.output = response

    # Save the Dockerfile and Compose file
    with open("generated/Dockerfile", "w", encoding="utf-8") as f:
        f.write(response.dockerfile)

    with open("generated/compose.yaml", "w", encoding="utf-8") as f:
        f.write(response.compose_file)

    return state


# Start Docker container agent
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
            build_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        for line in build_process.stdout:
            print(line, end="")
            full_output += line
            await current_step.stream_token(line)

        build_process.wait()

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
            up_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
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

    # Output the final result
    current_step.output = state["docker_output"]

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
    except Exception as e:
        await cl.Message(
            content=f"Error parsing code output analysis response: {e}"
        ).send()
        return state

    state["result"] = response

    # Output the final result
    current_step.output = response

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
@cl.step(name="New Loop Agent")
async def new_loop_agent(state: AgentState):
    print("*** NEW LOOP AGENT ***")
    current_step = cl.context.current_step
    inputs = state["purpose"]
    last_code = state["code"]
    last_output = state["result"]

    # Prepare the prompt
    prompt = NEW_LOOP_CODE_PROMPT.format(
        user_summary=inputs.user_summary,
        problem_type=inputs.problem_type,
        optimization_focus=inputs.optimization_focus,
        next_steps=inputs.next_steps,
        data=state["promptFiles"],
        previous_results=last_output.answer_description,
        previous_code=last_code.python_code,
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
        await cl.Message(content=f"Error during new optimization round: {e}").send()
        return state

    # Parse the full response
    try:
        response = output_parser.parse(full_response)
    except Exception as e:
        await cl.Message(content=f"Error parsing new code response: {e}").send()
        return state

    state["code"] = response

    # Output the final result
    current_step.output = response

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

    return state
