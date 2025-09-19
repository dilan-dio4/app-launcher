on run argv
	set appName to item 1 of argv
  tell application "System Events"
    tell process appName
      click menu bar item 1 of menu bar 2
    end tell
  end tell
end run