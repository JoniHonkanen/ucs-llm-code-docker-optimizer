from schemas import AgentState
from .common import cl, os
import re
import subprocess


def cap_pulp(requirements: str) -> str:
    """Keep an unpinned PuLP below version 4.

    Generated programs use the PuLP API that models know (LpVariable(lowBound=...),
    PULP_CBC_CMD). PuLP 4 (September 2026, Python >= 3.12) removed both, and it imports numpy
    without depending on it, so an unpinned "PuLP" in a Python 3.12 image now fails at import
    or at the first variable. A version the program pins itself is left as it is.
    """
    lines = requirements.splitlines()
    for i, line in enumerate(lines):
        spec = line.strip()
        name = re.split(r"[<>=!~\[; ]", spec, maxsplit=1)[0].lower()
        if name == "pulp" and not re.search(r"==|<|;", spec):
            lines[i] = spec + (",<4" if re.search(r"[>~!]", spec) else "<4")
    return "\n".join(lines) + ("\n" if requirements.endswith("\n") else "")


# Start Docker container agent
# Executes the generated code in a Docker container - output results
@cl.step(name="Start Docker Container Agent")
async def start_docker_container_agent(state: AgentState):
    print("*** START DOCKER CONTAINER AGENT ***")
    current_step = cl.context.current_step
    current_step.input = "Starting Docker container to execute the generated code."

    os.chdir("generated")
    full_output = ""
    error_output = ""  # To capture the entire traceback if an error occurs

    if os.path.exists("requirements.txt"):
        with open("requirements.txt", encoding="utf-8") as f:
            reqs = f.read()
        if cap_pulp(reqs) != reqs:
            with open("requirements.txt", "w", encoding="utf-8") as f:
                f.write(cap_pulp(reqs))

    try:
        # Build the Docker image
        print("Building Docker image...")
        build_command = ["docker", "compose", "build"]
        build_process = subprocess.Popen(
            build_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )

        for line in build_process.stdout:
            print(line, end="")
            full_output += line
            await current_step.stream_token(line)

        build_process.wait()
        if build_process.returncode != 0:
            raise Exception("Docker image build failed")

        # Run the Docker container
        print("Running Docker container...")
        up_command = [
            "docker",
            "compose",
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

        error_capture = []
        traceback_started = False

        for line in up_process.stdout:
            print(line, end="")
            full_output += line
            await current_step.stream_token(line)

            # Check for the "File ..." pattern first
            if re.match(r'\s*File\s+".+",\s+line\s+\d+', line):
                traceback_started = True
                error_capture.append(line)
            elif traceback_started:
                error_capture.append(line)
            elif "Traceback" in line or "SyntaxError" in line:
                traceback_started = True
                error_capture.append(line)

            if "exited with code" in line:
                error_output = "".join(error_capture)
                break

        up_process.wait()
        if up_process.returncode != 0:
            raise Exception("Docker container execution failed")

        state["docker_output"] = full_output
        state["proceed"] = "continue"

    except Exception as e:
        print(f"An error occurred: {e}")
        # Combine exception message with captured traceback output
        state["docker_output"] = f"{str(e)}\n{error_output.strip()}"
        print(state["docker_output"])
        state["proceed"] = "fix"
        await cl.Message(
            content=f"An error occurred: {e}\nDetails:\n{error_output.strip()}"
        ).send()

    finally:
        # Clean up Docker resources
        subprocess.run(["docker", "compose", "down"])
        subprocess.run(["docker", "image", "prune", "-f"])
        os.chdir("..")

    return state
