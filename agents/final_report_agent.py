from .common import cl, PydanticOutputParser, llm
from schemas import AgentState, FinalReport
from prompts.prompts import FINAL_REPORT_PROMPT


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
