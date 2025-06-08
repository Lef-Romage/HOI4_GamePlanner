#!/bin/bash

# Define the main file and output file
MAIN_FILE="app.py"
OUTPUT_FILE="combined_app.py"
MODULE_DIR="src"  # Directory containing other .py files

# Check if main file exists
if [ ! -f "$MAIN_FILE" ]; then
    echo "Error: Main file $MAIN_FILE not found!"
    exit 1
fi

# Check if module directory exists
if [ ! -d "$MODULE_DIR" ]; then
    echo "Error: Module directory $MODULE_DIR not found!"
    exit 1
fi

# Create or clear the output file
> "$OUTPUT_FILE"

# Add shebang line if present in main file
if grep -q "^#!/.*python" "$MAIN_FILE"; then
    grep "^#!/.*python" "$MAIN_FILE" > "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

# Function to check if a line is an import statement
is_import_line() {
    local line="$1"
    echo "$line" | grep -E '^(import|from[[:space:]]+[a-zA-Z0-9_]+[[:space:]]+import)' > /dev/null
}

# Track included imports to avoid duplicates
declare -A included_imports

# Process the main file
while IFS= read -r line; do
    if is_import_line "$line"; then
        # Store import lines to check for duplicates later
        if [ -z "${included_imports["$line"]}" ]; then
            included_imports["$line"]=1
            echo "$line" >> "$OUTPUT_FILE"
        fi
    else
        echo "$line" >> "$OUTPUT_FILE"
    fi
done < "$MAIN_FILE"

# Add a newline for separation
echo "" >> "$OUTPUT_FILE"

# Process all .py files in the module directory
for file in "$MODULE_DIR"/*.py; do
    if [ -f "$file" ] && [ "$file" != "$MAIN_FILE" ]; then
        echo "# Contents of $file" >> "$OUTPUT_FILE"
        while IFS= read -r line; do
            if is_import_line "$line"; then
                # Only include import if not already included
                if [ -z "${included_imports["$line"]}" ]; then
                    included_imports["$line"]=1
                    echo "$line" >> "$OUTPUT_FILE"
                fi
            else
                echo "$line" >> "$OUTPUT_FILE"
            fi
        done < "$file"
        echo "" >> "$OUTPUT_FILE"
    fi
done

echo "Combined Python files into $OUTPUT_FILE"