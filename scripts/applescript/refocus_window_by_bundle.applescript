on run argv
	set bundleId to item 1 of argv
	try
		tell application id bundleId
			activate
		end tell
	on error
		return false
	end try
end run