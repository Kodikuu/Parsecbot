import subprocess
import sys


def start():
    # 0x78 == 01111000 == x, eXit
    return subprocess.call((sys.executable, "main.py")) == 0x78


if __name__ == "__main__":
    print("Executing Bot initialisation.")
    while True:
        # Start the bot
        print("Starting Bot;")
        code = start()
        if not code == 0x78:
            print(f'\nRe-executing Bot initialisation. Exit code {code}')
            continue
        else:  # Exit if bot script returns special shutdown code 0x78
            print(f'\nShutting down. Exit code {code}')
            break
