use scripting additions
use framework "AppKit"
use framework "Foundation"

property myApp : a reference to current application

property statusBar : missing value
property statusItem : missing value
property statusItemImage : missing value
property launcherItems : {}

on run {}
	my setLauncherItems()

	-- Set the app to run in the background (No dock item)
	myApp's NSApplication's sharedApplication()'s setActivationPolicy:(myApp's NSApplicationActivationPolicyAccessory)
	
	-- Create the status item
	my createStatusItem()
end run

-- This handler will read the environment variable and return a list of records
on setLauncherItems()
	set launcherItemsString to (system attribute "LAUNCHER_ITEMS")
	
	-- AppleScript's 'paragraphs' is the easiest way to split a string by newlines
	set allItemRows to paragraphs of launcherItemsString
	
	-- Loop through each line (e.g., "ItemName;ACTION_TYPE;ItemTarget")
	repeat with aRow in allItemRows
		-- Ensure the row is not just an empty line
		if length of aRow is greater than 0 then
			
			-- Save AppleScript's current delimiter to avoid side effects
			set oldDelimiters to AppleScript's text item delimiters
			
			-- Set the delimiter to the semicolon used in your Python script
			set AppleScript's text item delimiters to ";"
			
			-- Split the row into a list of its parts
			set itemParts to text items of aRow
			
			-- IMPORTANT: Restore the original delimiters immediately
			set AppleScript's text item delimiters to oldDelimiters
			
			-- 5. Check if we have the expected number of parts (3)
			if (count of itemParts) is equal to 3 then
				-- 6. Create a record (dictionary) and add it to our main list
				set theRecord to {¬
					name: (item 1 of itemParts), ¬
					action_type: (item 2 of itemParts), ¬
					target: (item 3 of itemParts) ¬
				}
				set end of launcherItems to theRecord
			end if
			
		end if
	end repeat
end setLauncherItems


on createStatusItem()
	-- Get the systems Status Bar object
	set my statusBar to myApp's NSStatusBar's systemStatusBar()
	
	-- Use an SFSymbol instead of a standard macOS image
	set my statusItemImage to myApp's NSImage's imageWithSystemSymbolName:"app.badge" accessibilityDescription:(missing value)
	
	set statusBarThickness to statusBar's thickness() -- Get thickness of the Status Bar
	
	-- Set the Image size to be 4 pixels less that the thickness of the Status Bar, and square.
	statusItemImage's setSize:(myApp's NSMakeSize((statusBarThickness - 4), (statusBarThickness - 4)))
	
	-- Create the Status Item with just an image
	set my statusItem to statusBar's statusItemWithLength:(myApp's NSVariableStatusItemLength)
	statusItem's button's setImage:statusItemImage
	
	my createMenuItems()
end createStatusItem

on createMenuItems()
	set statusItemMenu to myApp's NSMenu's alloc()'s initWithTitle:""

	-- Add menu items for each launcher item
	repeat with aLauncherItem in launcherItems
		set itemName to aLauncherItem's name
		set launcherMenuItem to myApp's NSMenuItem's alloc()'s initWithTitle:itemName action:"launchItem:" keyEquivalent:""
		launcherMenuItem's setTarget:me
		statusItemMenu's addItem:launcherMenuItem
	end repeat

	-- set sepMenuItem to myApp's NSMenuItem's separatorItem()
	-- statusItemMenu's addItem:sepMenuItem
	-- set quitMenuItem to myApp's NSMenuItem's alloc()'s initWithTitle:"Quit" action:"quitStatusItem:" keyEquivalent:""
	-- quitMenuItem's setTarget:me
	-- statusItemMenu's addItem:quitMenuItem

	statusItem's setMenu:statusItemMenu
end createMenuItems

on openApplication(appName)
	try
		tell application appName
			activate
		end tell
	on error errMsg
		display notification "Failed to open application: " & appName with title "App Launcher Error"
	end try
end openApplication

on openURL(urlString)
	try
		open location urlString
	on error errMsg
		display notification "Failed to open URL: " & urlString with title "App Launcher Error"
	end try
end openURL

on launchItem:(sender)
	try
		-- Get the title of the clicked menu item
		set clickedItemName to sender's title() as string

		-- Find the corresponding launcher item
		repeat with aLauncherItem in launcherItems
			if aLauncherItem's name is equal to clickedItemName then
				-- Found matching item, launch it based on action type
				if aLauncherItem's action_type is "app" then
					my openApplication(aLauncherItem's target)
				else if aLauncherItem's action_type is "url" then
					my openURL(aLauncherItem's target)
				end if
				return -- Exit after launching
			end if
		end repeat

		-- If we get here, no matching item was found
		display notification "Launcher item not found: " & clickedItemName with title "App Launcher Error"

	on error errMsg
		display notification "Error launching item: " & errMsg with title "App Launcher Error"
	end try
end launchItem:

-- on quitStatusItem:(sender)
	-- my removeStatusItem()
	-- tell me to quit
-- end quitStatusItem:

-- on removeStatusItem()
	-- statusBar's removeStatusItem:statusItem
-- end removeStatusItem

on idle {}
	return 30.0
end idle

on quit {}
	continue quit
end quit