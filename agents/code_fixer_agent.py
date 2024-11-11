from .common import cl, PydanticOutputParser, llm_code
from schemas import AgentState, Code
from prompts.prompts import CODE_FIXER_PROMPT

# Code is split into two functions to allow for easier testing
async def fix_code_logic(code: Code, docker_output: str) -> Code:
    """
    Core logic to fix code using the LLM.

    Parameters:
    - code: Code object containing the code to be fixed.
    - docker_output: The error message from the docker execution.

    Returns:
    - A new Code object with the fixed code.
    """
    prompt = CODE_FIXER_PROMPT.format(
        code=code.python_code,
        requirements=code.requirements,
        resources=code.resources,
        docker_output=docker_output,
    )

    output_parser = PydanticOutputParser(pydantic_object=Code)
    format_instructions = output_parser.get_format_instructions()
    prompt += f"\n\n{format_instructions}"

    full_response = ""

    # Interact with the LLM
    try:
        async for chunk in llm_code.astream(prompt):
            if hasattr(chunk, "content"):
                full_response += chunk.content
    except Exception as e:
        raise RuntimeError(f"Error during code generation: {e}")

    # Parse the LLM's response
    try:
        response = output_parser.parse(full_response)
    except Exception as e:
        raise ValueError(f"Error parsing code response: {e}")

    return response


@cl.step(name="Code Fixer Agent")
async def code_fixer_agent(state: AgentState):
    print("*** CODE FIXER AGENT ***")

    current_step = cl.context.current_step

    code = state["code"]
    docker_output = state["docker_output"]

    current_step.input = (
        "Fixing the code based on the error encountered during execution."
    )
    print("\n*******\n")
    print("the code is:", code)
    print("\n\nthe docker output is:", docker_output)
    print("\n*******\n:")

    try:
        # Call the core logic function
        response = await fix_code_logic(code, docker_output)
    except Exception as e:
        await cl.Message(content=str(e)).send()
        return state

    state["code"] = response

    print("the response is:", response)

    # Save the generated code and requirements to files
    def clean_text(text):
        return text.encode("utf-8", "replace").decode("utf-8")

    with open("generated/generated.py", "w", encoding="utf-8") as f:
        f.write(clean_text(response.python_code))

    return state
