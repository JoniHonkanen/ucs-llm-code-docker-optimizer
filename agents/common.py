# agents/common.py
# This file contains common objects and functions that can be shared across multiple agents or modules.
# Just for reducing redundacy
import os
import chainlit as cl
from langchain.output_parsers import PydanticOutputParser
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables once
load_dotenv()

# Shared LLM instance
api_key = os.getenv("OPENAI_API_KEY")
# Model settings. The defaults are the models this project was developed with; set the
# variables in .env to use others (see README).
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_CODE_MODEL = os.getenv("LLM_CODE_MODEL", "gpt-4o")
# stream_usage: streamed replies report their token usage too
llm = ChatOpenAI(api_key=api_key, model=LLM_MODEL, disable_streaming=False, stream_usage=True)
llm_code = ChatOpenAI(api_key=api_key, model=LLM_CODE_MODEL, disable_streaming=False, stream_usage=True)

# Temperature of both models; unset keeps LangChain's default (0.7). Reasoning models accept
# only their own default and reject any value, so an empty LLM_TEMPERATURE sends none (null).
_temperature = os.getenv("LLM_TEMPERATURE")
if _temperature is not None:
    for _m in (llm, llm_code):
        _m.temperature = float(_temperature) if _temperature.strip() else None

# Export common objects or functions
__all__ = ["cl", "PydanticOutputParser", "llm", "llm_code"]
