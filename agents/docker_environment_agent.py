from prompts.prompts import (
    DOCKER_FILES_PROMPT,
)
from schemas import AgentState, DockerFiles
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
