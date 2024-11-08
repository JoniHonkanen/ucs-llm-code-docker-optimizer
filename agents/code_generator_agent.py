from prompts.prompts import CODE_PROMPT_NO_DATA, CODE_PROMPT
from schemas import AgentState, Code
from .common import cl, llm_code


# Code generator agent
# Generates Python code based on the user's problem analysis
#TODO: there is streamed version in archive, check it and try to get it work... it sometimes fails (error in json structure)
@cl.step(name="Code Generator Agent")
async def code_generator_agent(state: AgentState):
    print("*** CODE GENERATOR AGENT ***")
    current_step = cl.context.current_step
    inputs = state["purpose"]

    if state["promptFiles"] == "":
        prompt = CODE_PROMPT_NO_DATA.format(
            user_summary=inputs.user_summary,
            problem_type=inputs.problem_type,
            optimization_focus=inputs.optimization_focus,
            resource_requirements=inputs.resource_requirements,
        )
    else:
        prompt = CODE_PROMPT.format(
            user_summary=inputs.user_summary,
            problem_type=inputs.problem_type,
            optimization_focus=inputs.optimization_focus,
            data=state["promptFiles"],
            resource_requirements=inputs.resource_requirements,
        )

    # Display input in the Chainlit interface
    current_step.input = (
        f"Generating code based on the following inputs:\n\n"
        f"User Summary: {inputs.user_summary}\n"
        f"Problem Type: {inputs.problem_type}\n"
        f"Optimization Focus: {inputs.optimization_focus}\n"
        f"Data: {state['promptFiles']}"
    )

    structured_llm = llm_code.with_structured_output(Code)
    res = structured_llm.invoke(prompt)

    state["code"] = res
    current_step.output = f"Generated Python code:\n```python\n{res.python_code}\n```"

    # Save the generated code and requirements to files
    with open("generated/generated.py", "w", encoding="utf-8") as f:
        # f.write(clean_text(res.python_code))
        f.write(res.python_code)

    with open("generated/requirements.txt", "w", encoding="utf-8") as f:
        # f.write(clean_text(res.requirements))
        f.write(res.requirements)

    return state
