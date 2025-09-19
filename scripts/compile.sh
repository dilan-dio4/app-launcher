#!/bin/bash

# Create the compiled directory if it doesn't exist
mkdir -p scripts/compiled

# Compile all AppleScript files
echo "Compiling AppleScript files..."

for script in scripts/applescript/*.applescript; do
    if [ -f "$script" ]; then
        filename=$(basename "$script" .applescript)
        echo "Compiling $filename..."
        osacompile -o "scripts/compiled/${filename}.scpt" "$script"

        if [ $? -eq 0 ]; then
            echo "✓ $filename compiled successfully"
        else
            echo "✗ Failed to compile $filename"
            exit 1
        fi
    fi
done

osacompile -o "scripts/compiled/MenuApp.app" -s "scripts/menu_app.applescript"

if [ $? -eq 0 ]; then
    echo "✓ MenuApp compiled successfully"
else
    echo "✗ Failed to compile MenuApp"
    exit 1
fi

echo "All AppleScript files compiled successfully!"