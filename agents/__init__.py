from .problem_analyzer_agent import problem_analyzer_agent
from .code_generator_agent import code_generator_agent
from .docker_environment_agent import docker_environment_files_agent
from .docker_execution_agent import start_docker_container_agent
from .code_output_agent import code_output_analyzer_agent
from .final_report_agent import final_report_agent
from .new_loop_agent import new_loop_agent
from .code_fixer_agent import code_fixer_agent

# Exporting all agents in a list for easy import and access
all_agents = {
    "problem_analyzer_agent": problem_analyzer_agent,
    "code_generator_agent": code_generator_agent,
    "docker_environment_files_agent": docker_environment_files_agent,
    "start_docker_container_agent": start_docker_container_agent,
    "code_output_analyzer_agent": code_output_analyzer_agent,
    "final_report_agent": final_report_agent,
    "new_loop_agent": new_loop_agent,
    "code_fixer_agent": code_fixer_agent,
}
