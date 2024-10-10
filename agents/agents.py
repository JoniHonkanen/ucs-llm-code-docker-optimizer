import os
import subprocess
import chainlit as cl
from prompts.prompts import CODE_PROMPT, DOCKER_FILES_PROMPT, TASK_ANALYSIS_PROMPT
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from schemas import AgentState, DockerFiles, Purpose, Code

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
    print(response.python_code)
    print(response.requirements)

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
        python_code=inputs.python_code, requirements=inputs.requirements
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

async def start_docker_container(state: AgentState):
    print("*** START DOCKER CONTAINER AGENT ***")

    # Navigate to the 'generated' directory where the Dockerfile is located
    os.chdir('generated')

    try:
        # Build the Docker image
        build_command = ["docker", "build", "-t", "generated_image", "."]
        print(f"Running command: {' '.join(build_command)}")
        build_process = subprocess.run(build_command, capture_output=True, text=True)
        
        if build_process.returncode != 0:
            print("Docker build failed:")
            print(build_process.stderr)
            state['docker_output'] = build_process.stderr
            return state

        # Run the Docker container
        run_command = ["docker", "run", "--rm", "generated_image"]
        print(f"Running command: {' '.join(run_command)}")
        run_process = subprocess.run(run_command, capture_output=True, text=True)
        
        if run_process.returncode != 0:
            print("Docker run failed:")
            print(run_process.stderr)
            state['docker_output'] = run_process.stderr
            return state

        # Capture the output
        print("Docker run output:")
        print(run_process.stdout)
        state['docker_output'] = run_process.stdout

    except Exception as e:
        print(f"An error occurred: {e}")
        state['docker_output'] = str(e)

    finally:
        # Change back to the original directory
        os.chdir('..')

    return state
