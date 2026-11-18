from prompts.prompts import (
    DOCKER_FILES_PROMPT,
    EXECUTION_CONTRACT,
)
from schemas import AgentState, DockerFiles
from pathlib import Path
from .common import cl, PydanticOutputParser, llm


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

    # How the system builds and runs the program
    prompt += "\n\n" + EXECUTION_CONTRACT
    note = state.get("docker_fix_note")
    if note:  # the code fixer found the fault in the Docker files: correct the previous ones
        prev = ""
        for name in ("Dockerfile", "compose.yaml"):
            f = Path("generated") / name
            prev += f"\n--- {name} ---\n" + (f.read_text(encoding="utf-8", errors="replace") if f.exists() else "(missing)")
        prompt += ("\n\n### Correct the previous Docker files\nThe program failed to run with these files:"
                   f"\n```{prev}\n```\nError output:\n```\n{state.get('docker_full_log') or state.get('docker_output', '')}\n```"
                   f"\nThe code fixer's diagnosis: {note}\nReturn corrected files; keep what was right.")
        state["docker_fix_note"] = ""

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
