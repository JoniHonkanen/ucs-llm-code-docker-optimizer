from .common import cl, PydanticOutputParser, llm
from schemas import AgentState, Code
from prompts.prompts import NEW_LOOP_CODE_PROMPT, NEW_LOOP_CODE_PROMPT_NO_DATA


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
            previous_results=last_output.answer_description,
            previous_code=last_code.python_code,
            resource_requirements=inputs.resource_requirements,
        )
    else:
        prompt = NEW_LOOP_CODE_PROMPT.format(
            user_summary=inputs.user_summary,
            problem_type=inputs.problem_type,
            optimization_focus=inputs.optimization_focus,
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
