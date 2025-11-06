import re
from typing import List,  Optional, Tuple, Pattern


def auto_generate_pattern(
    file_path: str, 
    lines_to_sample: int = 20
) -> Tuple[Optional[Pattern], Optional[List[str]]]:
    """
    Reads a sample of a file to find a consistent chat pattern and generate a regex.

    Returns a tuple of (compiled_regex_pattern, column_names) or (None, None) if no pattern is found.
    """
    
    print(f"🔬 Analyzing first {lines_to_sample} lines to find a pattern...")
    
    sample_lines = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for i in range(lines_to_sample):
                line = f.readline().strip()
                if line:  # Only add non-empty lines
                    sample_lines.append(line)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None, None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None, None

    if not sample_lines:
        print("File is empty or no valid lines found in sample.")
        return None, None

    # --- Define known chat structures to test ---
    # We will test them in order of priority.
    # Each entry is a (test_regex, (capture_regex, [column_names]))
    
    patterns_to_try = {
        # 1. Format: [Date, Time] User: Message
        "bracket_datetime_user": (
            re.compile(r"^\[.+?,\s*.+?\]\s*[^:]+:\s*.*"), # Test: Does it look like this?
            (
                re.compile(r"^\[([^,]+),\s*(.+?)\]\s*([^:]+):\s*(.*)$"), # Capture Regex
                ["Date", "Time", "User", "Message"]                     # Columns
            )
        ),
        
        # 2. Format: Date, Time - User: Message
        "date_time_dash_user": (
            re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{1,2}\s*-\s*[^:]+:\s*.*"), # Test
            (
                re.compile(r"^([^,]+),\s*([^-]+)\s*-\s*([^:]+):\s*(.*)$"), # Capture
                ["Date", "Time", "User", "Message"]                     # Columns
            )
        ),
        
        # 3. Format: [Timestamp] User: Message
        "bracket_timestamp_user": (
             re.compile(r"^\[.+?\]\s*[^:]+:\s*.*"), # Test
            (
                re.compile(r"^\[(.+?)\]\s*([^:]+):\s*(.*)$"), # Capture
                ["Timestamp", "User", "Message"]                     # Columns
            )
        ),

        # 4. Format: Timestamp - User: Message (Common WhatsApp/Telegram)
        "timestamp_dash_user": (
            re.compile(r"^.+?\s*-\s*[^:]+:\s*.*"), # Test
            (
                re.compile(r"^(.+?)\s*-\s*([^:]+):\s*(.*)$"), # Capture
                ["Timestamp", "User", "Message"]             # Columns
            )
        )
    }

    # Find the first matching pattern that is consistent
    for pattern_name, (test_re, (capture_re, cols)) in patterns_to_try.items():
        # Check if the *first* line matches this general structure
        if test_re.match(sample_lines[0]):
            print(f"Found potential pattern: '{pattern_name}'")
            
            # Test it against the rest of the sample for consistency
            match_count = 0
            for line in sample_lines:
                if capture_re.match(line):
                    match_count += 1
            
            # If it matches > 90% of the sample, we'll use it
            if match_count / len(sample_lines) > 0.9:
                print(f"✅ Consistent pattern found! Using '{pattern_name}'.")
                print(f"   Regex: {capture_re.pattern}")
                return capture_re, cols
            else:
                print(f"Pattern '{pattern_name}' was inconsistent. Trying next...")

    print("😔 No consistent pattern was found in the sample.")
    return None, None


# --- 2. The Modified Parsing Function ---

