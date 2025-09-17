import subprocess
from typing import TypedDict
from pynput import keyboard
import threading

# Lock to prevent concurrent launcher executions
launcher_lock = threading.Lock()


def run_osascript(script) -> tuple[str, int]:
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, check=False
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"Error running osascript: {e}")
        return "", 1


class WindowInfo(TypedDict):
    app_name: str | None
    window_title: str | None
    bundle_id: str | None


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
    """Show a selection dialog with the given items."""
    # Convert list to AppleScript list format
    items_str = ", ".join(f'"{item}"' for item in items)

    script = f"""
    tell application "System Events"
        activate
        set itemList to {{{items_str}}}
        set chosenItem to choose from list itemList with prompt "Choose an option:" with title "Selection Dialog"
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


def refocus_window(window_info: WindowInfo):
    """Refocus the specified window."""
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


def run_launcher():
    # Try to acquire the lock without blocking
    if not launcher_lock.acquire(blocking=False):
        print("Launcher is already running. Ignoring request.")
        return

    # Step 1: Get the currently focused window
    print("Getting currently focused window...")
    original_window = get_focused_window()

    if original_window:
        print(f"Focused window: {original_window['app_name']}")
        if original_window["window_title"]:
            print(f"Window title: {original_window['window_title']}")
    else:
        print("No focused window detected")

    # Step 2: Present a list of options
    options = [
        "x: Hello",
        "y: World",
        "a: Python",
        "Option 4: macOS",
        "Option 5: Script",
    ]

    print("\nShowing selection dialog...")
    chosen = show_selection_dialog(options)

    # Step 3: Handle the choice
    if chosen:
        print(f"\nChosen item: {chosen}")
    else:
        print("\nNo item chosen (user cancelled)")

        # Refocus the original window
        if original_window:
            print("Refocusing original window...")
            if refocus_window(original_window):
                print(f"Refocused: {original_window['app_name']}")
            else:
                print("Failed to refocus window")

    # Always release the lock
    launcher_lock.release()


def on_activate():
    print("Hotkey activated!")
    # Run shortcut in a separate thread to avoid blocking
    threading.Thread(target=run_launcher, daemon=True).start()


# Define the hotkey for activating the shortcut
hotkey = keyboard.HotKey(keyboard.HotKey.parse("<cmd>+<shift>+<enter>"), on_activate)


def on_press(key: keyboard.Key | keyboard.KeyCode | None):
    """Handle key press events"""
    if key == None:
        return
    elif key == keyboard.Key.esc:
        # TODO
        pass
    else:
        hotkey.press(listener.canonical(key))


def on_release(key: keyboard.Key | keyboard.KeyCode | None):
    """Handle key release events"""
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
