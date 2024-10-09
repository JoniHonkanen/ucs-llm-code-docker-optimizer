import os
import pandas as pd
import chainlit as cl
from langgraph.graph import StateGraph, END
from agents.agents import problem_analyzer_agent
from schemas import AgentState


# Starting message
@cl.on_chat_start
async def on_chat_start():
    await cl.Message(
        content="Hei! Voit ladata Excel- tai Python-tiedoston, niin koitan optimoida ja ratkoa ongelman syötteesi perusteella."
    ).send()


# Create the graph.
workflow = StateGraph(AgentState)
workflow.add_node("problem_analyzer", problem_analyzer_agent)
workflow.add_edge("problem_analyzer", END)
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
