from langchain_core.prompts import ChatPromptTemplate

TASK_ANALYSIS_PROMPT = ChatPromptTemplate.from_template(
    """
    Your job is the figure how to use given data to solve a problem. Here is the data you have:
    User message: 
    {user_input}
    
    Given data: 
    {data}
    """
)