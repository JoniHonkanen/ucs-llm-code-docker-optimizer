from .common import cl, PydanticOutputParser, llm
from schemas import AgentState, Code
from prompts.prompts import CODE_FIXER_PROMPT


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
