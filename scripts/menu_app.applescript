use scripting additions
use framework "AppKit"
use framework "Foundation"

property myApp : a reference to current application

property statusBar : missing value
property statusItem : missing value
property statusItemImage : missing value

on run {}
	-- Set the app to run in the background (No dock item)
	myApp's NSApplication's sharedApplication()'s setActivationPolicy:(myApp's NSApplicationActivationPolicyAccessory)
	
	-- Create the status item
	my createStatusItem()
end run

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
	
	set doStuffMenuItem to myApp's NSMenuItem's alloc()'s initWithTitle:"DoStuff" action:"doStuff" keyEquivalent:""
	doStuffMenuItem's setTarget:me
	statusItemMenu's addItem:doStuffMenuItem
	
	set sepMenuItem to myApp's NSMenuItem's separatorItem()
	statusItemMenu's addItem:sepMenuItem
	
	set quitMenuItem to myApp's NSMenuItem's alloc()'s initWithTitle:"Quit" action:"quitStatusItem" keyEquivalent:""
	quitMenuItem's setTarget:me
	statusItemMenu's addItem:quitMenuItem
	
	statusItem's setMenu:statusItemMenu
end createMenuItems

on doStuff()
	-- Do stuff here when the doStuffMenuItem is clicked
end doStuff

on quitStatusItem()
	-- Remove this Thread check code, once your stand alone App bundle is built and running. 
	my removeStatusItem()
	if name of myApp does not start with "Script" then
		tell me to quit
	end if
end quitStatusItem

on removeStatusItem()
	statusBar's removeStatusItem:statusItem
end removeStatusItem

on idle {}
	return 30.0
end idle

on quit {}
	continue quit
end quit