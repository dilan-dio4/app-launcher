on run argv
	set appName to item 1 of argv
	try
		tell application appName
			activate
		end tell
	on error
		return false
	end try
end run