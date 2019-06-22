import subprocess
import sys
import json
import os
import time


def verifyErrorData():
    # First, check for the existence of stored error data modifications.
    try:  # The data exists, so we try to read and decode it
        with open("errors.private", "r") as file:
                data = json.load(file)

    except json.decoder.JSONDecodeError:
        # We can't read the data, so we move it aside and start over.
        now = time.strftime("%Y%m%d-%H%M%S")
        os.rename("errors.private", f"errors-{now}.private")
        return False  # If we can't read it, we need to ditch it.

    except FileNotFoundError:
        return True  # If no file exists, then there's no bad data.

    # We've read and decoded the data, now to confirm the elements
    for element in data:
        pass  # NOT IMPLEMENTED
    else:
        return True  # We got to the end without issue, the data is good.


def start():
    # 0x78 == 01111000 == x, eXit
    return subprocess.call((sys.executable, "main.py")) == 0x78


if __name__ == "__main__":

    failures = 0

    print("Executing Bot initialisation.")
    while True:
        # Confirm data is valid
        if verifyErrorData():
            print("Passed Data Verification\n")
        else:
            failures += 1
            print(f"Failed Data Verification\nFailures: {failures}/3\n")

        # Start the bot
        print("Starting Bot;")
        code = start()
        if not code == 0x78:
            print(f'\nRe-executing Bot initialisation. Exit code {code}')
            continue
        else:  # Exit if bot script returns special shutdown code 0x78
            print(f'\nShutting down. Exit code {code}')
            break
