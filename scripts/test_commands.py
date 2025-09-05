import re
import subprocess
from pathlib import Path


def run_command(cmd: str) -> bool:
    print(f"Running command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True


def main():
    readme_files = list(Path.cwd().rglob("*.md"))
    all_commands = []

    for file in readme_files:
        with open(file, "r") as f:
            content = f.read()
            commands = re.findall(r"```bash\n(dockvirt .*?)\n```", content, re.DOTALL)
            all_commands.extend(cmd.strip() for cmd in commands)

    for cmd in all_commands:
        if not run_command(cmd):
            print(f"Command failed: {cmd}")


if __name__ == "__main__":
    main()
