from .common import cl, PydanticOutputParser, llm
from prompts.prompts import CODE_OUTPUT_ANALYSIS_PROMPT
from schemas import AgentState, OutputOfCode


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
        code_output=docker_output,
    )

    # Display input in the Chainlit interface
    current_step.input = (
        f"Analyzing the code output based on the following inputs:\n\n"
        f"User Summary: {state['purpose'].user_summary}\n"
        f"Original Goal: {state['purpose'].goal}\n"
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
