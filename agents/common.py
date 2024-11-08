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
llm = ChatOpenAI(api_key=api_key, model="gpt-4o-mini", disable_streaming=False)
llm_code = ChatOpenAI(api_key=api_key, model="gpt-4o", disable_streaming=False)

# Export common objects or functions
__all__ = ["cl", "PydanticOutputParser", "llm", "llm_code"]
