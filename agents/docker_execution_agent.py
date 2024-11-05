from schemas import AgentState
from .common import cl, os
import subprocess


# Start Docker container agent
# Executes the generated code in a Docker container - output results
@cl.step(name="Start Docker Container Agent")
async def start_docker_container_agent(state: AgentState):
    print("*** START DOCKER CONTAINER AGENT ***")
    current_step = cl.context.current_step

    # Display input in the Chainlit interface
    current_step.input = "Starting Docker container to execute the generated code."

    os.chdir("generated")
    full_output = ""

    try:
        # Build the Docker image
        print("Building Docker image...")
        build_command = ["docker-compose", "build"]
        build_process = subprocess.Popen(
            build_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        # Loops through each line of stdout from the build process
        for line in build_process.stdout:
            print(line, end="")
            full_output += line
            await current_step.stream_token(line)

        build_process.wait()

        # check if the build process was successful (0 is success)
        if build_process.returncode != 0:
            raise Exception("Docker image build failed")

        # Run the Docker container
        print("Running Docker container...")
        up_command = [
            "docker-compose",
            "up",
            "--abort-on-container-exit",
            "--no-log-prefix",
        ]
        up_process = subprocess.Popen(
            up_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        for line in up_process.stdout:
            print(line, end="")
            full_output += line
            await current_step.stream_token(line)

        up_process.wait()
        if up_process.returncode != 0:
            raise Exception("Docker container execution failed")

        state["docker_output"] = full_output

    except Exception as e:
        print(f"An error occurred: {e}")
        state["docker_output"] = str(e)
        await cl.Message(content=f"An error occurred: {e}").send()

    finally:
        # Clean up Docker resources
        down_command = ["docker-compose", "down"]
        subprocess.run(down_command)
        # Prune dangling images (those with the same name but unused)
        prune_command = ["docker", "image", "prune", "-f"]
        subprocess.run(prune_command)
        os.chdir("..")

    return state
