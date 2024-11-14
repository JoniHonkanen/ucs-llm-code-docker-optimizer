import difflib
import colorama
from colorama import Fore

colorama.init(autoreset=True)


def print_colored_diff(
    original_code, modified_code, fromfile="Original Code", tofile="Modified Code"
):
    diff = difflib.unified_diff(
        original_code.splitlines(),
        modified_code.splitlines(),
        fromfile=fromfile,
        tofile=tofile,
        lineterm="",
    )
    print("\n\n**Differences between original and modified code:")

    for line in diff:
        if line.startswith("---"):
            print(Fore.YELLOW + line)  # File label for "from" file
        elif line.startswith("+++"):
            print(Fore.YELLOW + line)  # File label for "to" file
        elif line.startswith("@@"):
            print(Fore.CYAN + line)  # Location in the code
        elif line.startswith("+") and not line.startswith("+++"):
            print(Fore.GREEN + line)  # Added lines
        elif line.startswith("-") and not line.startswith("---"):
            print(Fore.RED + line)  # Removed lines
        else:
            print(line)  # Unchanged lines
