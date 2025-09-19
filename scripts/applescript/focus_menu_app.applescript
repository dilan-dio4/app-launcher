on run argv
	set appName to item 1 of argv
  tell application "System Events"
    tell process appName
      tell menu bar item 1 of menu bar 2
        perform action "AXPress"
      end tell
    end tell
  end tell
end run