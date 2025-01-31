import json
import os

def split_json_file(input_file, output_prefix, max_chars=75000):
    """
    Splits a JSON file into smaller files, ensuring the JSON structure is maintained.
    
    Parameters:
    - input_file: Path to the input JSON file.
    - output_prefix: Prefix for the output files.
    - max_chars: Maximum number of characters per output file.
    """
    try:
        # Read and parse the JSON file
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)  # Parse JSON into a Python list
        
        # Initialize variables for splitting
        current_file_data = []
        current_file_size = 2  # Start with 2 for the opening and closing brackets []
        part_number = 1
        
        for item in data:
            # Convert the current item to a JSON string
            item_json = json.dumps(item, indent=4) + ",\n"
            
            # Check if adding this item would exceed the max_chars limit
            if current_file_size + len(item_json) > max_chars:
                # Write the current file and start a new one
                output_file = f"{output_prefix}_part_{part_number}.json"
                with open(output_file, 'w', encoding='utf-8') as output:
                    # Write the data as a proper JSON array
                    output.write("[\n")
                    output.write("".join(current_file_data).rstrip(",\n") + "\n")
                    output.write("]")
                print(f"Created: {output_file}")
                
                # Reset for the next file
                current_file_data = []
                current_file_size = 2  # Reset to account for []
                part_number += 1
            
            # Add the current item to the file's data
            current_file_data.append(item_json)
            current_file_size += len(item_json)
        
        # Write the remaining data to the last file
        if current_file_data:
            output_file = f"{output_prefix}_part_{part_number}.json"
            with open(output_file, 'w', encoding='utf-8') as output:
                output.write("[\n")
                output.write("".join(current_file_data).rstrip(",\n") + "\n")
                output.write("]")
            print(f"Created: {output_file}")
    
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
    except json.JSONDecodeError:
        print("Error: The input file is not valid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Usage example
# Replace 'input.json' with the path to your large JSON file
# Replace 'output' with the desired prefix for output files
split_json_file('Crafting Item Database.json', 'output')