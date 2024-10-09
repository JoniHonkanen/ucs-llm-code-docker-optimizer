import os
from prompts.prompts import TASK_ANALYSIS_PROMPT
from schemas import AgentState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# .env file is used to store the api key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(
    api_key=api_key,
    model="gpt-4o-mini",
)


async def problem_analyzer_agent(state: AgentState):
    userInput = state["userInput"]
    prompt_files = state["promptFiles"]

    prompt = TASK_ANALYSIS_PROMPT.format(user_input=userInput, data=prompt_files)
    print(f"Prompt: {prompt}")

    # Call the LLM with the constructed prompt
    response = llm.invoke(prompt)
    print(response)

    # Return the response
    return state
