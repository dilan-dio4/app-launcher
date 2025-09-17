import subprocess
from typing import TypedDict
from pynput import keyboard
import threading
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


SELECTION_DIALOG_TITLE = "Launcher Selection Dialog"
SELECTION_DIALOG_PROMPT = "Choose"

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


def run_osascript(script) -> tuple[str, int]:
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, check=False
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"Error running osascript: {e}")
        return "", 1


def get_focused_window() -> WindowInfo | None:
    script = """
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        set frontAppID to bundle identifier of first application process whose frontmost is true
        try
            set windowTitle to name of front window of application process frontApp
            return frontApp & "|" & windowTitle & "|" & frontAppID
        on error
            return frontApp & "||" & frontAppID
        end try
    end tell
    """

    output, returncode = run_osascript(script)

    if returncode == 0 and output:
        parts = output.split("|")
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
            set frontmost of application process "System Events" to true
            perform action "AXRaise" of dialogWindow
            delay 0.1
            key code 53
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


def open_application(app_name: str) -> bool:
    script = f"""
    tell application "{app_name}"
        activate
    end tell
    """

    output, returncode = run_osascript(script)

    if returncode != 0:
        print(f"Failed to open application: {app_name}")
        return False

    print(f"Opened application: {app_name}")
    return True


def open_url(url: str) -> bool:
    script = f"""
    open location "{url}"
    """

    output, returncode = run_osascript(script)

    if returncode != 0:
        print(f"Failed to open URL: {url}")
        return False

    print(f"Opened URL: {url}")
    return True


def run_launcher():
    global original_window

    if not launcher_lock.acquire(blocking=False):
        print("Launcher is already running. Ignoring request.")
        return

    print("Getting currently focused window...")
    original_window = get_focused_window()

    if original_window:
        print(f"Focused window: {original_window['app_name']}")
        if original_window["window_title"]:
            print(f"Window title: {original_window['window_title']}")
    else:
        print("No focused window detected")

    # Generate options from launcher items
    options = sorted(LAUNCHER_ITEMS.keys())

    print("\nShowing selection dialog...")
    chosen = show_selection_dialog(options)

    # Handle the choice
    if chosen:
        print(f"\nChosen item: {chosen}")

        # Find the corresponding launcher item
        selected_item = LAUNCHER_ITEMS.get(chosen, None)

        if selected_item:
            # Execute the action based on type
            success = False
            if selected_item["action_type"] == ActionType.APP:
                success = open_application(selected_item["target"])
            elif selected_item["action_type"] == ActionType.URL:
                success = open_url(selected_item["target"])

            if not success:
                print(f"Failed to execute action for: {chosen}")
        else:
            print(f"Could not find launcher item for: {chosen}")
    else:
        print("\nNo item chosen (user cancelled)")

    # Always refocus the original window when no choice was made
    if not chosen and original_window:
        print("Refocusing original window...")
        if refocus_window(original_window):
            print(f"Refocused: {original_window['app_name']}")
        else:
            print("Failed to refocus window")

    original_window = None
    launcher_lock.release()


def on_activate():
    print("Hotkey activated")
    # Run shortcut in a separate thread to avoid blocking
    threading.Thread(target=run_launcher, daemon=True).start()


# Define the hotkey for activating the shortcut
hotkey = keyboard.HotKey(keyboard.HotKey.parse("<cmd>+<shift>+<enter>"), on_activate)


def on_press(key: keyboard.Key | keyboard.KeyCode | None):
    if key == None:
        return
    elif key == keyboard.Key.esc:
        # Check if there's an active selection dialog and close it
        if is_selection_dialog_active():
            print("Closing active launcher dialog...")
            close_selection_dialog()
            # The normal flow in run_launcher() will handle refocusing
    else:
        hotkey.press(listener.canonical(key))


def on_release(key: keyboard.Key | keyboard.KeyCode | None):
    if key == None:
        return
    else:
        hotkey.release(listener.canonical(key))


if __name__ == "__main__":
    with keyboard.Listener(
        on_press=on_press,
        on_release=on_release,
    ) as listener:
        print("Listening for 'cmd+shift+enter' to run your shortcut.")
        print("Press 'escape' to kill a running shortcut.")
        listener.join()
