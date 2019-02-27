import subprocess
import sys

if __name__ == "__main__":
    interpreter = sys.executable  # Fetch python executable path
    cmd = (interpreter, "main.py")  # Create main.py execution command

    print("Executing Bot initialisation.")
    while True:
        code = subprocess.call(cmd)  # Execute bot initialisation, return code
        if not code == 0x78:  # 0x78 == 01111000 == x, eXit
            if code == 0x79:
                subprocess.call(["git", "pull"])
            print(f'\nRe-executing Bot initialisation. Exit code {code}')
            continue
        else:  # Exit if bot script returns special shutdown code 0x78
            print(f'\nShutting down. Exit code {code}')
            break
