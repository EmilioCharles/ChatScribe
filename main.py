import uvicorn
import re
import os  # <-- NEW: For file path operations and cleanup
import tempfile  # <-- NEW: To create a temporary file
import shutil    # <-- NEW: To copy the uploaded file contents
from fastapi import FastAPI, HTTPException, UploadFile, File
from typing import List, Dict, Any  # <-- NEW: For response type hinting

# Import your existing functions
from models.auto_generate_pattern import auto_generate_pattern
from models.parse_chat_with_pattern import parse_chat_with_pattern

app = FastAPI()


@app.get("/")
def hello_world():
    return {"message": "Server is running! Go to /docs to test the parser."}


# --- NEW API ENDPOINT ---

@app.post("/parse/", response_model=List[Dict[str, Any]])
async def parse_chat_file(
    lines_to_sample: int = 20, 
    file: UploadFile = File(...)
):
    """
    Uploads a chat .txt file, auto-detects its pattern, 
    parses it, and returns the structured data.
    """

    # 1. Basic file validation
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Please upload a .txt file."
        )

    # 2. Save UploadFile to a temporary file on disk.
    # We must do this because your functions `auto_generate_pattern`
    # and `parse_chat_with_pattern` are built to read from a file *path*,
    # not an in-memory file object.
    
    temp_file_path = None
    try:
        # Create a named temporary file
        # 'delete=False' means we are responsible for deleting it in the 'finally' block
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name  # Get the path of the saved file

        # 3. Run the pattern generator
        print(f"Analyzing file at temp path: {temp_file_path}")
        GENERATED_PATTERN, DATA_COLUMNS = auto_generate_pattern(
            temp_file_path, 
            lines_to_sample=lines_to_sample
        )

        # 4. Run the parser ONLY if a pattern was found
        if GENERATED_PATTERN and DATA_COLUMNS:
            chat_records = parse_chat_with_pattern(
                temp_file_path, 
                GENERATED_PATTERN, 
                DATA_COLUMNS
            )
            print(f"\nSuccessfully parsed {len(chat_records)} records.")
            return chat_records  # Success! Return the data
        else:
            # If no pattern was found, return a 400 error
            print("Could not parse file as no pattern was generated.")
            raise HTTPException(
                status_code=400, 
                detail="Could not determine a consistent chat pattern from the uploaded file."
            )

    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"An internal server error occurred: {str(e)}"
        )
    
    finally:
        # --- CRITICAL CLEANUP ---
        # 5. Always close the uploaded file resource
        await file.close()
        
        # 6. Always delete the temporary file from disk
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            print(f"Cleaned up temp file: {temp_file_path}")

# --------------------------


def main():
    print("Hello from apis-chart-import!")


if __name__ == "__main__":
    print("Starting Uvicorn server...")
    print("Go to http://127.0.0.1:8000/docs to test the API.")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )