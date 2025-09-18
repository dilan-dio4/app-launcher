on run argv
	set appName to item 1 of argv
	set windowTitle to item 2 of argv
	tell application "System Events"
		tell process appName
			set frontmost to true
			try
				set theWindow to first window whose name is windowTitle
				perform action "AXRaise" of theWindow
			end try
		end tell
	end tell
end run