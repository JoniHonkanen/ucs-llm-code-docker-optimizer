import os
import pandas as pd
import chainlit as cl
from langgraph.graph import StateGraph, END
from agents.agents import (
    docker_environment_files_agent,
    problem_analyzer_agent,
    code_generator_agent,
    start_docker_container_agent,
    code_output_analyzer_agent,
    new_loop_agent,
)
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
    ]  # This should return either 'continue', 'new', 'done' or 'cancel'


# Create the graph.
workflow = StateGraph(AgentState)
workflow.add_node("problem_analyzer", problem_analyzer_agent)
workflow.add_node("code_generator", code_generator_agent)
workflow.add_node("docker_files", docker_environment_files_agent)
workflow.add_node("start_docker", start_docker_container_agent)
workflow.add_node("output_analyzer", code_output_analyzer_agent)
workflow.add_node("new_loop", new_loop_agent)
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
workflow.add_edge("start_docker", "output_analyzer")
workflow.add_conditional_edges(
    source="output_analyzer",
    path=decide_next_step,  # The function that determines the next step
    path_map={
        "continue": "new_loop",  # start new optimization round
        "done": END,  # THIS WILL BE CHANGED -> GENERATE FINAL REPORT OR SOMETHING LIKE THAT
    },
)
workflow.add_edge(
    "new_loop", "docker_files"
)  # Loop back to docker_files for a new optimization round
# workflow.add_edge("output_analyzer", END)
workflow.set_entry_point("problem_analyzer")
app = workflow.compile()


@cl.on_message
async def main(message: cl.Message):
    # Initialize a dictionary to store file data
    file_data = {}

    # Check if there are any elements in the message
    if message.elements:
        for element in message.elements:
            # Check if the element is a File
            if isinstance(element, cl.File):
                file_name = element.name  # Original filename
                file_path = element.path  # Path to stored file

                # Define the new file path in the generated directory
                new_file_path = os.path.join(generated_dir, file_name)
                # Save the file to the 'generated' directory
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

                # Check file extension
                if file_name.endswith((".xlsx", ".xls")):
                    # Process Excel file
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
        await cl.Message(
            content="Tiedostot käsitelty ja tallennettu onnistuneesti."
        ).send()
    else:
        print("Ei liitettyjä tiedostoja.")
        await cl.Message(content="Ei liitettyjä tiedostoja.").send()

    await cl.Message(content="Aletaan ratkomaan ongelmaa... hetkinen....").send()

    # Print user's message and loaded files
    print("Käyttäjän syöte:")
    print("Viesti: " + message.content)
    print("Tiedostot: " + str(file_data))

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
    results = await app.ainvoke(state)

    # Send the results back to the user
    await cl.Message(content=f"Tässä ovat tulokset:\n{results}").send()
