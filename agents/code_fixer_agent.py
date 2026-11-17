from .common import cl, PydanticOutputParser, llm_code
from schemas import AgentState, Code, CodeFix
from prompts.prompts import CODE_FIXER_PROMPT, EXECUTION_CONTRACT, FULL_LOGS_INSTRUCTIONS, FIXER_ROUTE_INSTRUCTIONS
from pathlib import Path


# Code is split into two functions to allow for easier testing
async def fix_code_logic(code: Code, docker_output: str, full_log: str = None, history=None) -> Code:
    """
    Core logic to fix code using the LLM.

    Parameters:
    - code: Code object containing the code to be fixed.
    - docker_output: The error message from the docker execution.
    - full_log: The tail of the full build and run log, when the fixer has asked for it.
    - history: Earlier fix attempts on the same program (error and action), oldest first.

    Returns:
    - A new Code object with the fixed code.
    """
    prompt = CODE_FIXER_PROMPT.format(
        code=code.python_code,
        requirements=code.requirements,
        resources=code.resources,
        docker_output=docker_output,
    )
    prompt += "\n\n" + EXECUTION_CONTRACT + "\n\n" + FIXER_ROUTE_INSTRUCTIONS
    if history:
        prompt += ("\n\n### Earlier fix attempts on this program (they did not solve it; do not repeat them)\n"
                   + "\n".join(f"{i}. {h}" for i, h in enumerate(history, 1)))
    if full_log is None:
        prompt += "\n\n" + FULL_LOGS_INSTRUCTIONS
    else:
        docker_files = ""
        for name in ("Dockerfile", "compose.yaml"):
            f = Path("generated") / name
            docker_files += f"\n--- {name} ---\n" + (f.read_text(encoding="utf-8", errors="replace") if f.exists() else "(missing)")
        prompt += ("\n\n### Full logs (you asked for them)\nLast part of the complete build and run log:\n"
                   f"```\n{full_log}\n```\nThe Docker files used:\n```{docker_files}\n```\n"
                   "Fix the code now; set need_full_logs to false.")

    output_parser = PydanticOutputParser(pydantic_object=CodeFix)
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
    print("\n*******\n")

    try:
        # Call the core logic function
        response = await fix_code_logic(code, docker_output, history=state.get("fix_history"))
        # The fixer asked for the full logs: ask again, in the same step, with them
        if response.need_full_logs:
            print("Code fixer asked for the full logs:", response.full_logs_reason)
            await cl.Message(content=f"Code fixer asked for the full Docker logs: {response.full_logs_reason}").send()
            response = await fix_code_logic(code, docker_output, full_log=state.get("docker_full_log") or "(no log recorded)",
                                            history=state.get("fix_history"))
    except Exception as e:
        await cl.Message(content=str(e)).send()
        return state

    # Where the fault is: "code" (the fixed program follows), "docker" (the Docker files agent
    # corrects the Docker files) or "give_up" (the round ends as a failed round)
    route = (response.route or "code").strip().lower()
    if route not in ("code", "docker", "give_up"):
        route = "code"
    state["fix_history"] = (state.get("fix_history") or []) + [
        f"error: {response.original_error} | action: "
        + (response.fix_description if route == "code" else f"{route}: {response.route_note}")
    ]
    print(f"Code fixer route: {route}: {response.route_note}")
    if route != "code":
        state["fixIterations"] = state.get("fixIterations", 0) + 1
        if route == "docker":
            # only while fix attempts remain (MAX_FIX_ATTEMPTS = 4 in main.py); after that a new
            # program gets new Docker files anyway
            state["docker_fix_note"] = response.route_note if state["fixIterations"] < 4 else ""
            await cl.Message(content=f"Code fixer: the Docker files need a correction: {response.route_note}").send()
        else:
            state["gave_up"] = response.route_note
            state["docker_output"] = (f"The program failed and the fix attempts were given up: {response.route_note}"
                                      f"\n\nLast program output:\n{state.get('docker_output', '')}")
            await cl.Message(content=f"Code fixer gave up on this program: {response.route_note}").send()
        current_step.output = f"route={route}: {response.route_note}"
        return state

    # Convert CodeFix back to Code
    updated_code = Code(
        python_code=response.fixed_python_code,
        requirements=response.requirements,
        resources=code.resources,  # Keep resources the same if they were not modified
    )

    state["code"] = updated_code

    print("the response is:", response)

    # Save the generated code to a Python file
    def clean_text(text):
        return text.encode("utf-8", "replace").decode("utf-8")

    with open("generated/generated.py", "w", encoding="utf-8") as f:
        f.write(clean_text(updated_code.python_code))

    # If requirements have changed, save to requirements.txt
    if response.requirements_changed:
        with open("generated/requirements.txt", "w", encoding="utf-8") as f:
            f.write(response.requirements)

    state["fixIterations"] = state.get("fixIterations", 0) + 1

    return state
