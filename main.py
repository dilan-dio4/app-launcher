import subprocess
from typing import TypedDict
from pynput import keyboard
from enum import Enum
import atexit
import threading
import queue
import os


class ActionType(Enum):
    APP = "app"
    URL = "url"


class LauncherItem(TypedDict):
    action_type: ActionType
    target: str


MENU_APP_NAME = "MenuApp"
HOTKEY = "<ctrl>+/"

LAUNCHER_ITEMS: dict[str, LauncherItem] = {
    "gmail": LauncherItem(
        action_type=ActionType.URL,
        target="https://mail.google.com/mail/u/0/#inbox",
    ),
    "vscode": LauncherItem(
        action_type=ActionType.APP,
        target="Visual Studio Code",
    ),
    "youtube": LauncherItem(
        action_type=ActionType.APP,
        target="YouTube",
    ),
    "xcode": LauncherItem(
        action_type=ActionType.APP,
        target="Xcode-26.0.0",
    ),
    "edge": LauncherItem(
        action_type=ActionType.APP,
        target="Microsoft Edge",
    ),
    "messages": LauncherItem(
        action_type=ActionType.APP,
        target="Messages",
    ),
    "warp": LauncherItem(
        action_type=ActionType.APP,
        target="Warp",
    ),
    "spotify": LauncherItem(
        action_type=ActionType.APP,
        target="Spotify",
    ),
    "claude": LauncherItem(
        action_type=ActionType.APP,
        target="Claude",
    ),
    "orbstack": LauncherItem(
        action_type=ActionType.APP,
        target="OrbStack",
    ),
    "todoist": LauncherItem(
        action_type=ActionType.APP,
        target="Todoist",
    ),
    "x": LauncherItem(
        action_type=ActionType.URL,
        target="https://x.com/home",
    ),
    "github": LauncherItem(
        action_type=ActionType.URL,
        target="https://github.com",
    ),
}

# Lock to prevent concurrent launcher executions
launcher_lock = threading.Lock()

# Queue for launcher requests (maxsize=1 to ignore rapid requests)
launcher_queue: queue.Queue[None] = queue.Queue(maxsize=1)


def run_compiled_script(
    script_name: str, args: list[str] | None = None
) -> tuple[str, int]:
    script_path = f"scripts/compiled/{script_name}.scpt"
    cmd = ["osascript", script_path]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"Error running compiled script {script_name}: {e}")
        return "", 1


def run_compiled_script_nonblocking(
    script_name: str, args: list[str] | None = None
) -> None:
    script_path = f"scripts/compiled/{script_name}.scpt"
    cmd = ["osascript", script_path]
    if args:
        cmd.extend(args)

    try:
        subprocess.Popen(
            args=cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"Error starting compiled script {script_name}: {e}")


def _run_launcher_impl():
    if not launcher_lock.acquire(blocking=False):
        print("Launcher is already running. Ignoring request.")
        return

    try:
        run_compiled_script("focus_menu_app", [MENU_APP_NAME])
    finally:
        launcher_lock.release()


def launcher_worker():
    while True:
        try:
            # Blocks
            launcher_queue.get()

            # Process the launcher request
            _run_launcher_impl()

            # Mark task as done
            launcher_queue.task_done()

        except Exception as e:
            print(f"Error in launcher worker thread: {e}")


def on_activate():
    try:
        # Try to queue the launcher request (non-blocking)
        launcher_queue.put_nowait(None)
    except queue.Full:
        # Launcher request is already queued or running, ignore this one
        pass


# Define the hotkey for activating the launcher
hotkey = keyboard.HotKey(keyboard.HotKey.parse(keys=HOTKEY), on_activate)


def on_press(key: keyboard.Key | keyboard.KeyCode | None):
    assert key
    hotkey.press(listener.canonical(key))


def on_release(key: keyboard.Key | keyboard.KeyCode | None):
    assert key
    hotkey.release(listener.canonical(key))


def make_menu_app_items() -> str:
    # Sort launcher items alphabetically by key name
    sorted_items = []
    for name in sorted(LAUNCHER_ITEMS.keys()):
        item = LAUNCHER_ITEMS[name]
        sorted_items.append(
            {
                "name": name,
                "action_type": item["action_type"].value,
                "target": item["target"],
            }
        )

    string_delimited_items = [
        f'{item["name"]};{item["action_type"]};{item["target"]}'
        for item in sorted_items
    ]
    return "\n".join(string_delimited_items)


def start_menu_app():
    process_env = os.environ.copy()
    process_env["LAUNCHER_ITEMS"] = make_menu_app_items()

    # Start the menu app
    try:
        subprocess.run(
            ["open", "./scripts/compiled/MenuApp.app"],
            check=True,
            env=process_env,
        )
    except Exception as e:
        print(f"Error starting menu app: {e}")


def on_exit():
    print("Exiting...")
    run_compiled_script("kill_menu_app", [MENU_APP_NAME])


launcher_worker_thread = threading.Thread(target=launcher_worker, daemon=True)
launcher_worker_thread.start()

atexit.register(on_exit)

if __name__ == "__main__":
    start_menu_app()
    with keyboard.Listener(
        on_press=on_press,
        on_release=on_release,
    ) as listener:
        print(f"Listening for '{HOTKEY}' to run your launcher.")
        print("Press 'escape' to kill a running launcher.")
        listener.join()
