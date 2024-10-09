import os
import chainlit as cl
from prompts.prompts import TASK_ANALYSIS_PROMPT
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from schemas import AgentState, Purpose

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
    print("\CHATBOT RESPONSE:")
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
    print("*** PROBLEM ANALYZER AGENT ***")
    
    return state
