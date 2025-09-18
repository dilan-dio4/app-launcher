on run argv
	set dialogTitle to item 1 of argv
	tell application "System Events"
		try
			set dialogWindow to first window of application process "System Events" whose name is dialogTitle
			click button "Cancel" of dialogWindow
			return true
		on error
			return false
		end try
	end tell
end run