import os
import subprocess
import logging
from typing import Dict, Any
import chainlit as cl
import docker
from prompts.prompts import (
    CODE_PROMPT,
    DOCKER_FILES_PROMPT,
    TASK_ANALYSIS_PROMPT,
    CODE_OUTPUT_ANALYSIS_PROMPT,
)
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from schemas import AgentState, DockerFiles, Purpose, Code, OutputOfCode
from docker.errors import DockerException

# .env file is used to store the api key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(
    api_key=api_key,
    model="gpt-4o-mini",
)


async def problem_analyzer_agent(state: AgentState):
    print("*** PROBLEM ANALYZER AGENT ***")
    userInput = state["userInput"]
    prompt_files = state["promptFiles"]

    structured_llm = llm.with_structured_output(Purpose)

    prompt = TASK_ANALYSIS_PROMPT.format(user_input=userInput, data=prompt_files)
    print(f"Prompt: {prompt}")

    response = structured_llm.invoke(prompt)
    print("\nRESPONSE:")
    print(response)

    state["purpose"] = response

    chatbot_response = response.chatbot_response
    next_steps = response.next_steps
    print("\nCHATBOT RESPONSE:")
    print(chatbot_response)

    # Just use the next_steps text as it is, since it's already numbered
    formatted_next_steps = next_steps.replace("\n", "\n\n")

    # Send the message with the chatbot response and the formatted next steps
    await cl.Message(
        content=f"{chatbot_response}\n\n**Next Steps:**\n\n{formatted_next_steps}"
    ).send()

    res = await cl.AskActionMessage(
        content="Sounds good, proceed?!",
        actions=[
            cl.Action(name="continue", value="continue", label="✅ Continue"),
            cl.Action(name="new", value="new", label="❌ create new plan"),
            cl.Action(
                name="cancel", value="cancel", label="❌ let's cancel and start over"
            ),
        ],
    ).send()

    if res and res.get("value") == "continue":
        state["proceed"] = "continue"
        await cl.Message(
            content="Lets proceed with this plan!",
        ).send()
    elif res and res.get("value") == "cancel":
        state["proceed"] = "cancel"
        await cl.Message(
            content="Alright, let's cancel this and start over!",
        ).send()
    else:
        state["proceed"] = "new"
        await cl.Message(
            content="Alright, let's create a new plan!",
        ).send()

    # Return the response
    return state


async def code_generator_agent(state: AgentState):
    print("*** CODE GENERATOR AGENT ***")
    inputs = state["purpose"]
    structured_llm = llm.with_structured_output(Code)
    prompt = CODE_PROMPT.format(
        user_summary=inputs.user_summary,
        problem_type=inputs.problem_type,
        optimization_focus=inputs.optimization_focus,
        next_steps=inputs.next_steps,
        data=state["promptFiles"],
    )
    response = structured_llm.invoke(prompt)
    state["code"] = response
    print("\nKOODI: " + response.python_code)
    print("\nPAKETIT: " + response.requirements)
    # check if optional resources are present
    print(
        "\nRESURSSIT: " + response.resources
        if response.resources
        else "No resources provided"
    )

    # write the code to a file and save it to generated/
    with open("generated/generated.py", "w", encoding="utf-8") as f:
        f.write(response.python_code)

    with open("generated/requirements.txt", "w", encoding="utf-8") as f:
        f.write(response.requirements)

    return state


async def docker_environment_files_agent(state: AgentState):
    # Add code here to set up the Docker environment
    print("*** DOCKER ENVIRONMENT AGENT ***")
    inputs = state["code"]
    structured_llm = llm.with_structured_output(DockerFiles)
    prompt = DOCKER_FILES_PROMPT.format(
        python_code=inputs.python_code,
        requirements=inputs.requirements,
        resources=inputs.resources,
    )
    response = structured_llm.invoke(prompt)
    print(response.dockerfile)
    print(response.compose_file)
    # write the dockerFile and compose.yaml then save it to generated/
    with open("generated/Dockerfile", "w", encoding="utf-8") as f:
        f.write(response.dockerfile)

    with open("generated/compose.yaml", "w", encoding="utf-8") as f:
        f.write(response.compose_file)

    return state


async def start_docker_container_agent(state):
    print("*** START DOCKER CONTAINER AGENT ***")
    # Navigate to the 'generated' directory where the Dockerfile and docker-compose.yaml are located
    os.chdir("generated")

    try:
        # Build the Docker image using docker-compose
        print("Building Docker image...")
        # If there is same name image, it will be used as layer and shown as "unused (dangling)" in docker images
        build_command = ["docker-compose", "build"]
        build_process = subprocess.Popen(
            build_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        # Capture build output
        for line in build_process.stdout:
            print(line, end="")

        build_process.wait()
        if build_process.returncode != 0:
            raise Exception("Docker image build failed")

        # Run the container using docker-compose and capture the output
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

        full_output = ""
        for line in up_process.stdout:
            print(line, end="")
            full_output += line

        up_process.wait()
        if up_process.returncode != 0:
            raise Exception("Docker container execution failed")

        # Store the output in state
        state["docker_output"] = full_output

    except Exception as e:
        print(f"An error occurred: {e}")
        state["docker_output"] = str(e)

    finally:
        # Bring down the docker-compose services to clean up
        down_command = ["docker-compose", "down"]
        subprocess.run(down_command)
        # Change back to the original directory
        os.chdir("..")

    print("\nDOCKER OUTPUT:")
    print(state["docker_output"])

    return state


async def code_output_analyzer_agent(state: AgentState):
    print("*** CODE OUTPUT ANALYZER AGENT ***")
    # Analyze the output of the Docker container
    docker_output = state["docker_output"]

    structured_llm = llm.with_structured_output(OutputOfCode)
    prompt = CODE_OUTPUT_ANALYSIS_PROMPT.format(
        user_summary=state["purpose"].user_summary,
        next_steps=state["purpose"].next_steps,
        code_output=docker_output,
    )
    response = structured_llm.invoke(prompt)
    print("\nRESPONSE:")
    print(response)
    state["result"] = response

    return state


#
# async def start_docker_container_agent(state: AgentState):
#    print("*** START DOCKER CONTAINER AGENT ***")
#    # TODO:: Pitää käyttää subprocessia että saa watchin homman toimimaan!!!
#    # Navigate to the 'generated' directory where the Dockerfile and docker-compose.yaml are located
#    os.chdir("generated")
#
#    try:
#        # Initialize Docker client
#        client = docker.from_env()
#
#        # Build the image
#        print("Building Docker image...")
#        image, build_logs = client.images.build(path=".", tag="generated_image")
#
#        # Optionally print build logs if you want more detailed logging
#        for log in build_logs:
#            print(log.get("stream", ""))
#
#        # Run the container and capture stdout/stderr in real-time
#        print("Running Docker container...")
#        container = client.containers.run(
#            image="generated_image",
#            remove=True,  # Automatically remove the container after it exits
#            detach=True,  # Run the container in detached mode
#        )
#
#        # Capture and stream logs from the container in real-time
#        print("Streaming container logs:")
#        full_output = ""
#        for log in container.logs(stream=True, stdout=True, stderr=True):
#            log_output = log.decode("utf-8").strip()
#            print(log_output)  # Print each log line as it arrives
#            full_output += log_output + "\n"  # Capture all logs into full_output
#
#        # Wait for the container to finish
#        exit_code = container.wait()["StatusCode"]
#
#        if exit_code != 0:
#            print(f"Container exited with error code {exit_code}")
#            state["docker_output"] = (
#                f"Error: Container exited with code {exit_code}\n{full_output}"
#            )
#        else:
#            print("Container finished successfully")
#            state["docker_output"] = full_output
#
#    except DockerException as e:
#        print(f"An error occurred with Docker: {e}")
#        state["docker_output"] = str(e)
#
#    finally:
#        # Change back to the original directory
#        os.chdir("..")
#
#    print("\nDOCKER OUTPUT:")
#    print(state["docker_output"])
#
#    return state
