from typing import List, Dict, Any, Pattern

def parse_chat_with_pattern(
    file_path: str, 
    pattern: Pattern, 
    columns: List[str]
) -> List[Dict[str, Any]]:
    """
    Reads a chat file and extracts components using the provided regex pattern.
    """
    
    parsed_data = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue 

                match = pattern.match(line)
                
                if match:
                    # Use zip to dynamically create the dict from the column names
                    # and the captured groups from the regex
                    record = dict(zip(columns, match.groups()))
                    
                    # Clean up the data (e.g., stripping whitespace)
                    for key, value in record.items():
                        if isinstance(value, str):
                            record[key] = value.strip()
                            
                    parsed_data.append(record)
                
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
    return parsed_data