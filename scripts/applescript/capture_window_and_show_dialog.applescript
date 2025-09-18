on run argv
	-- Parameters: dialogTitle, dialogPrompt, windowDelimiter, nilValue, items...
	set dialogTitle to item 1 of argv
	set dialogPrompt to item 2 of argv
	set windowDelimiter to item 3 of argv
	set nilValue to item 4 of argv

	-- Build items list from remaining arguments (item 5 onwards)
	set itemList to {}
	repeat with i from 5 to count of argv
		set end of itemList to item i of argv
	end repeat

	tell application "System Events"
		-- Capture current focused window first
		set frontApp to name of first application process whose frontmost is true
		set frontAppID to bundle identifier of first application process whose frontmost is true
		try
			set windowTitle to name of front window of application process frontApp
			set windowInfo to frontApp & windowDelimiter & windowTitle & windowDelimiter & frontAppID
		on error
			set windowInfo to frontApp & windowDelimiter & nilValue & windowDelimiter & frontAppID
		end try

		-- Now show the selection dialog
		activate
		set chosenItem to choose from list itemList with prompt dialogPrompt with title dialogTitle
		if chosenItem is false then
			return windowInfo & windowDelimiter & windowDelimiter
		else
			return windowInfo & windowDelimiter & windowDelimiter & (item 1 of chosenItem)
		end if
	end tell
end run