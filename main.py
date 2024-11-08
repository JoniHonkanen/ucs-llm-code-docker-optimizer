import os
import pandas as pd
import chainlit as cl
from langgraph.graph import StateGraph, END

""" from agents.agents import (
    docker_environment_files_agent,
    code_generator_agent,
    start_docker_container_agent,
    code_output_analyzer_agent,
    new_loop_agent,
    final_report_agent,
) """
from agents import all_agents
from schemas import AgentState

# Ensure the 'generated' directory exists
generated_dir = "generated"
os.makedirs(generated_dir, exist_ok=True)


# Starting message
@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content="Hei! Voit ladata Excel- tai Python-tiedoston, niin koitan optimoida ja ratkoa ongelman syötteesi perusteella."
    ).send()


# Define a function to determine the next step based on 'proceed'
def decide_next_step(state: AgentState):
    return state[
        "proceed"
    ]  # This should return either 'continue', 'new', 'done', 'fix' or 'cancel'


# Create the graph.
workflow = StateGraph(AgentState)
workflow.add_node("problem_analyzer", all_agents["problem_analyzer_agent"])
workflow.add_node("code_generator", all_agents["code_generator_agent"])
workflow.add_node("docker_files", all_agents["docker_environment_files_agent"])
workflow.add_node("start_docker", all_agents["start_docker_container_agent"])
workflow.add_node("output_analyzer", all_agents["code_output_analyzer_agent"])
workflow.add_node("new_loop", all_agents["new_loop_agent"])
workflow.add_node("final_report", all_agents["final_report_agent"])
workflow.add_node("code_fixer", all_agents["code_fixer_agent"])
# Use add_conditional_edges for cleaner transitions based on the proceed value
workflow.add_conditional_edges(
    source="problem_analyzer",
    path=decide_next_step,  # The function that determines the next step
    path_map={
        "continue": "code_generator",  # Proceed to the next node (replace with actual node name)
        "new": "problem_analyzer",  # Loop back to problem_analyzer for a new plan
        "cancel": END,  # End the workflow
    },
)
workflow.add_edge("code_generator", "docker_files")
workflow.add_edge("docker_files", "start_docker")
# if error occurs during code execution in the Docker container, use code_fixer_agent
workflow.add_conditional_edges(
    source="start_docker",
    path=decide_next_step,  # The function that determines the next step
    path_map={
        "fix": "code_fixer",  # Fix the code
        "continue": "output_analyzer",  # Proceed to the next node
    },
)
workflow.add_edge("code_fixer", "start_docker")  # Try to execute the fixed code again
# workflow.add_edge("start_docker", "output_analyzer")
workflow.add_conditional_edges(
    source="output_analyzer",
    path=decide_next_step,  # The function that determines the next step
    path_map={
        "continue": "new_loop",  # start new optimization round
        "done": "final_report",  # write final report
    },
)
workflow.add_edge(
    "new_loop", "docker_files"
)  # Loop back to docker_files for a new optimization round
workflow.add_edge("final_report", END)  # After final report, end the workflow
workflow.set_entry_point("problem_analyzer")
app = workflow.compile()


@cl.on_message
async def main(message: cl.Message):
    # Initialize a dictionary to store file data
    file_data = {}

    # Check if there are any elements in the message
    # Check if there are any elements in the message
    if message.elements:
        for element in message.elements:
            # Check if the element is a File
            if isinstance(element, cl.File):
                file_name = element.name  # Original filename
                file_path = element.path  # Path to stored file

                # Define the new file path in the generated directory
                new_file_path = os.path.join(generated_dir, file_name)

                # Check file extension first to decide handling
                if file_name.endswith((".xlsx", ".xls")):
                    # Process Excel file as binary
                    try:
                        # Read Excel file from the file path
                        dfs = pd.read_excel(file_path, sheet_name=None)
                        file_data[file_name] = dfs
                        print(
                            f"Excel-sheetit tiedostosta {file_name} ladattu onnistuneesti."
                        )
                    except Exception as e:
                        await cl.Message(
                            content=f"Virhe Excel-tiedoston {file_name} käsittelyssä: {str(e)}"
                        ).send()

                elif file_name.endswith(".py"):
                    # Process Python code file
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            python_code = f.read()
                        file_data[file_name] = python_code
                        print(f"Python-koodi {file_name} ladattu onnistuneesti.")
                    except Exception as e:
                        await cl.Message(
                            content=f"Virhe Python-tiedoston {file_name} käsittelyssä: {str(e)}"
                        ).send()

                else:
                    print(f"Tuntematon tiedostotyyppi: {file_name}")
                    await cl.Message(
                        content=f"Tuntematon tiedostotyyppi: {file_name}"
                    ).send()

                # Now save the file to the 'generated' directory after processing
                try:
                    with open(file_path, "rb") as f_in, open(
                        new_file_path, "wb"
                    ) as f_out:
                        f_out.write(f_in.read())
                    print(f"Tiedosto {file_name} tallennettu /generated-hakemistoon.")
                except Exception as e:
                    await cl.Message(
                        content=f"Virhe tiedoston {file_name} tallentamisessa: {str(e)}"
                    ).send()

    # Construct promptFiles
    prompt_files = []
    for filename, content in file_data.items():
        if isinstance(content, dict):
            # It's an Excel file with sheets
            for sheet_name, df in content.items():
                # Convert DataFrame to JSON string
                json_string = df.to_json(orient="records", force_ascii=False, indent=2)
                prompt_files.append(
                    f"File: {filename}, Sheet: {sheet_name}\nData:\n{json_string}"
                )
        else:
            # It's code (e.g., Python code)
            # Wrap the code in triple backticks to preserve formatting
            prompt_files.append(f"File: {filename}\nCode:\n```python\n{content}\n```")

    formatted_data = "\n\n".join(prompt_files)

    # Create the AgentState
    state = AgentState(
        userInput=message.content,
        messages=[message.content],
        iterations=0,
        promptFiles=formatted_data,
    )

    # Invoke the agent with the state
    await app.ainvoke(state)
