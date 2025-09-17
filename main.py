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


HOTKEY = "<cmd>+<shift>+<space>"
SELECTION_DIALOG_TITLE = "Launcher Selection Dialog"
SELECTION_DIALOG_PROMPT = "Choose"
FOCUSED_WINDOW_DELIMITER = "§§§"

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


def get_focused_window() -> WindowInfo | None:
    script = f"""
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        set frontAppID to bundle identifier of first application process whose frontmost is true
        try
            set windowTitle to name of front window of application process frontApp
            return frontApp & "{FOCUSED_WINDOW_DELIMITER}" & windowTitle & "{FOCUSED_WINDOW_DELIMITER}" & frontAppID
        on error
            return frontApp & "{FOCUSED_WINDOW_DELIMITER}{FOCUSED_WINDOW_DELIMITER}" & frontAppID
        end try
    end tell
    """

    output, returncode = run_osascript(script)

    if returncode == 0 and output:
        parts = output.split(FOCUSED_WINDOW_DELIMITER)
        return WindowInfo(
            app_name=parts[0] if len(parts) > 0 else None,
            window_title=parts[1] if len(parts) > 1 and parts[1] else None,
            bundle_id=parts[2] if len(parts) > 2 else None,
        )
    return None


def show_selection_dialog(items: list[str]):
    items_str = ", ".join(f'"{item}"' for item in items)

    script = f"""
    tell application "System Events"
        activate
        set itemList to {{{items_str}}}
        set chosenItem to choose from list itemList with prompt "{SELECTION_DIALOG_PROMPT}" with title "{SELECTION_DIALOG_TITLE}"
        if chosenItem is false then
            return ""
        else
            return item 1 of chosenItem
        end if
    end tell
    """

    output, returncode = run_osascript(script)

    if returncode == 0:
        return output if output else None
    return None


def capture_window_and_show_dialog(
    items: list[str],
) -> tuple[WindowInfo | None, str | None]:
    items_str = ", ".join(f'"{item}"' for item in items)

    script = f"""
    tell application "System Events"
        -- Capture current focused window first
        set frontApp to name of first application process whose frontmost is true
        set frontAppID to bundle identifier of first application process whose frontmost is true
        try
            set windowTitle to name of front window of application process frontApp
            set windowInfo to frontApp & "|" & windowTitle & "|" & frontAppID
        on error
            set windowInfo to frontApp & "||" & frontAppID
        end try

        -- Now show the selection dialog
        activate
        set itemList to {{{items_str}}}
        set chosenItem to choose from list itemList with prompt "{SELECTION_DIALOG_PROMPT}" with title "{SELECTION_DIALOG_TITLE}"
        if chosenItem is false then
            return windowInfo & "||"
        else
            return windowInfo & "||" & (item 1 of chosenItem)
        end if
    end tell
    """

    output, returncode = run_osascript(script)

    if returncode == 0 and output:
        # Parse the combined result: windowInfo||chosenItem
        parts = output.split("||")

        # Parse window info
        window_parts = parts[0].split("|") if len(parts) > 0 else []
        window_info = None
        if len(window_parts) >= 3:
            window_info = WindowInfo(
                app_name=window_parts[0] if window_parts[0] else None,
                window_title=window_parts[1] if window_parts[1] else None,
                bundle_id=window_parts[2] if window_parts[2] else None,
            )

        # Parse chosen item
        chosen_item = parts[1] if len(parts) > 1 and parts[1] else None

        return window_info, chosen_item

    return None, None


def is_selection_dialog_active() -> bool:
    script = f"""
    tell application "System Events"
        try
            set dialogExists to exists (first window of application process "System Events" whose name is "{SELECTION_DIALOG_TITLE}")
            return dialogExists
        on error
            return false
        end try
    end tell
    """

    output, returncode = run_osascript(script)
    return returncode == 0 and output.strip() == "true"


def close_selection_dialog():
    script = f"""
    tell application "System Events"
        try
            set dialogWindow to first window of application process "System Events" whose name is "{SELECTION_DIALOG_TITLE}"
            click button "Cancel" of dialogWindow
            return true
        on error
            return false
        end try
    end tell
    """

    output, returncode = run_osascript(script)
    return returncode == 0 and output.strip() == "true"


def refocus_window(window_info: WindowInfo):
    if not window_info or not window_info["app_name"]:
        return False

    app_name = window_info["app_name"]
    window_title = window_info["window_title"]

    # First, activate the application
    script = f"""
    tell application "{app_name}"
        activate
    end tell
    """

    _, returncode = run_osascript(script)

    if returncode != 0:
        # Try using bundle ID if app name didn't work
        if window_info["bundle_id"]:
            script = f"""
            tell application id "{window_info['bundle_id']}"
                activate
            end tell
            """
            _, returncode = run_osascript(script)

    # If we have a specific window title, try to bring it to front
    if returncode == 0 and window_title:
        script = f"""
        tell application "System Events"
            tell process "{app_name}"
                set frontmost to true
                try
                    set theWindow to first window whose name is "{window_title}"
                    perform action "AXRaise" of theWindow
                end try
            end tell
        end tell
        """
        run_osascript(script)

    return returncode == 0


def open_application(app_name: str):
    script = f"""
    tell application "{app_name}"
        activate
    end tell
    """

    run_osascript_nonblocking(script)


def open_url(url: str):
    script = f"""
    open location "{url}"
    """

    run_osascript_nonblocking(script)


def _run_launcher_impl():
    global original_window

    if not launcher_lock.acquire(blocking=False):
        print("Launcher is already running. Ignoring request.")
        return

    # Generate options from launcher items
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
        # Check if there's an active selection dialog and close it
        if is_selection_dialog_active():
            close_selection_dialog()
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
