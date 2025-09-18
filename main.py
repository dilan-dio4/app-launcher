import subprocess
from typing import TypedDict
from pynput import keyboard
import threading
import queue
from enum import Enum


class ActionType(Enum):
    APP = "app"
    URL = "url"


class LauncherItem(TypedDict):
    action_type: ActionType
    target: str


class WindowInfo(TypedDict):
    app_name: str | None
    window_title: str | None
    bundle_id: str | None


HOTKEY = "<cmd>+<shift>+\\"
SELECTION_DIALOG_TITLE = "Launcher Selection"
SELECTION_DIALOG_PROMPT = "Choose"
FOCUSED_WINDOW_DELIMITER = "§§§"
APPLESCRIPT_NIL = "NIL"

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

# Global variable to track the original window for escape handler
original_window: WindowInfo | None = None

# Queue for launcher requests (maxsize=1 to ignore rapid requests)
launcher_queue: queue.Queue[None] = queue.Queue(maxsize=1)


def run_osascript(script) -> tuple[str, int]:
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, check=False
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"Error running osascript: {e}")
        return "", 1


def run_osascript_nonblocking(script) -> None:
    try:
        subprocess.Popen(
            args=["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"Error starting osascript: {e}")


def run_compiled_script(script_name: str, args: list[str] | None = None) -> tuple[str, int]:
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


def run_compiled_script_nonblocking(script_name: str, args: list[str] | None = None) -> None:
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


def capture_window_and_show_dialog(
    items: list[str],
) -> tuple[WindowInfo | None, str | None]:
    # Prepare arguments: constants first, then items
    args = [
        SELECTION_DIALOG_TITLE,
        SELECTION_DIALOG_PROMPT,
        FOCUSED_WINDOW_DELIMITER,
        APPLESCRIPT_NIL,
    ]
    args.extend(items)

    output, returncode = run_compiled_script("capture_window_and_show_dialog", args)

    if returncode == 0 and output:
        # Parse the combined result: windowInfo||chosenItem
        parts = output.split(f"{FOCUSED_WINDOW_DELIMITER}{FOCUSED_WINDOW_DELIMITER}")

        # Parse window info
        window_parts = (
            parts[0].split(FOCUSED_WINDOW_DELIMITER) if len(parts) > 0 else []
        )
        window_info: WindowInfo | None = None

        def parse_script_value(value: str | None) -> str | None:
            if value == APPLESCRIPT_NIL:
                return None

            if value:
                return value

            return None

        if len(window_parts) >= 3:
            window_info = WindowInfo(
                app_name=parse_script_value(window_parts[0]),
                window_title=parse_script_value(window_parts[1]),
                bundle_id=parse_script_value(window_parts[2]),
            )

        # Parse chosen item
        chosen_item = parts[1] if len(parts) > 1 and parts[1] else None

        return window_info, chosen_item

    return None, None


def close_selection_dialog_if_active():
    run_compiled_script_nonblocking("close_selection_dialog", [SELECTION_DIALOG_TITLE])


def refocus_window(window_info: WindowInfo):
    if not window_info or not window_info["app_name"]:
        return False

    app_name = window_info["app_name"]
    window_title = window_info["window_title"]
    bundle_id = window_info["bundle_id"]

    # First, try using bundle ID (more reliable)
    returncode = 1
    if bundle_id:
        _, returncode = run_compiled_script("refocus_window_by_bundle", [bundle_id])

    # If bundle ID failed, try app name
    if returncode != 0:
        _, returncode = run_compiled_script("refocus_window_by_name", [app_name])

    # If we have a specific window title, try to bring it to front
    if returncode == 0 and window_title:
        run_compiled_script("refocus_window_specific", [app_name, window_title])

    return returncode == 0


def open_application(app_name: str):
    run_compiled_script_nonblocking("open_application", [app_name])


def open_url(url: str):
    run_compiled_script_nonblocking("open_url", [url])


def _run_launcher_impl():
    global original_window

    if not launcher_lock.acquire(blocking=False):
        print("Launcher is already running. Ignoring request.")
        return

    try:
        # Shouldn't throw an exception, but just in case
        options = sorted(LAUNCHER_ITEMS.keys())

        original_window, chosen = capture_window_and_show_dialog(options)

        # Handle the choice
        if chosen:
            # Find the corresponding launcher item
            selected_item = LAUNCHER_ITEMS.get(chosen, None)

            if selected_item:
                if selected_item["action_type"] == ActionType.APP:
                    open_application(selected_item["target"])
                elif selected_item["action_type"] == ActionType.URL:
                    open_url(selected_item["target"])
            else:
                print(f"Could not find launcher item for: {chosen}")
        else:
            print("\nNo item chosen (user cancelled)")

        # Always refocus the original window when no choice was made
        if not chosen and original_window:
            if not refocus_window(original_window):
                print("Failed to refocus window")
    finally:
        original_window = None
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


# Define the hotkey for activating the shortcut
hotkey = keyboard.HotKey(keyboard.HotKey.parse(HOTKEY), on_activate)


def on_press(key: keyboard.Key | keyboard.KeyCode | None):
    if key == None:
        return
    elif key == keyboard.Key.esc:
        # Only try to close selection dialog if launcher is currently running
        if launcher_lock.locked():
            # Launcher is running, so dialog might be active
            close_selection_dialog_if_active()
        # The normal flow in run_launcher() will handle refocusing
    else:
        hotkey.press(listener.canonical(key))


def on_release(key: keyboard.Key | keyboard.KeyCode | None):
    if key == None:
        return
    else:
        hotkey.release(listener.canonical(key))


# Start the launcher worker thread
launcher_worker_thread = threading.Thread(target=launcher_worker, daemon=True)
launcher_worker_thread.start()

if __name__ == "__main__":
    with keyboard.Listener(
        on_press=on_press,
        on_release=on_release,
    ) as listener:
        print(f"Listening for '{HOTKEY}' to run your shortcut.")
        print("Press 'escape' to kill a running shortcut.")
        listener.join()
