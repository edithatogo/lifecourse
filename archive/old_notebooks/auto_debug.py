import subprocess
import traceback
import google.generativeai as genai
import os
import re  # For parsing Gemini's response

# --- Configuration ---
# IMPORTANT: Replace 'YOUR_GEMINI_API_KEY' with your actual Gemini API key
# It's safer to load this from an environment variable:
# os.environ.get("GOOGLE_API_KEY")
# If you don't have it as an environment variable, uncomment the line below and set your key:
# os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY_HERE"

# Ensure API key is set
if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError(
        "GOOGLE_API_KEY environment variable not set. Please set it or uncomment and set your key in the script."
    )

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# You can choose a different model if needed, 'gemini-pro' is a good general-purpose model.
model = genai.GenerativeModel("gemini-pro")

# The file containing the Python code you want to debug
CODE_FILE_PATH = "life_course_model.py"
MAX_DEBUG_ATTEMPTS = 5  # Maximum number of times to try fixing the code

# --- Functions for Code Execution and Gemini Interaction ---


def run_python_code_from_file(file_path):
    """
    Runs a Python script from a given file path and captures its output.
    Returns 'SUCCESS:\n' + stdout or 'ERROR:\n' + stderr.
    """
    # Create a copy of the current environment variables
    # and add your custom variable to signal automated debugging
    env_vars = os.environ.copy()
    env_vars["IS_AUTOMATED_DEBUGGING"] = "true"  # Set a flag for the child process

    try:
        # Use subprocess to run the code in a separate Python interpreter
        # Pass the modified environment variables to the subprocess
        process = subprocess.run(
            ["python", file_path],
            capture_output=True,
            text=True,
            check=False,  # Don't raise an exception immediately on non-zero exit code
            env=env_vars,
            timeout=300,  # Timeout in seconds (e.g., 5 minutes)
        )

        if process.returncode != 0:
            return "ERROR:\n" + process.stderr
        else:
            return "SUCCESS:\n" + process.stdout
    except subprocess.TimeoutExpired:
        return f"ERROR:\nScript timed out after {300} seconds. It might be hanging or running too long."
    except Exception as e:
        return f"CRITICAL ERROR IN EXECUTION SCRIPT:\n{e}\n{traceback.format_exc()}"


def get_gemini_fix(code_content, error_message):
    """
    Sends the code and error message to Gemini and asks for a corrected version.
    Returns the corrected code string or an error message if parsing fails.
    """
    prompt = f"""
    I am trying to run the following Python code:

    ```python
    {code_content}
    ```

    It resulted in the following error:

    ```
    {error_message}
    ```

    Please analyze the error and provide a corrected version of the Python code.
    Only provide the corrected Python code, enclosed in a triple backtick code block (```python ... ```).
    Do not include any other explanatory text unless the error is unfixable or requires more information from me.
    """
    print("Gemini prompt:\n", prompt)  # For debugging/visibility

    try:
        response = model.generate_content(prompt)
        # Extract the code block from Gemini's response
        match = re.search(r"```python\n(.*?)```", response.text, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            print(
                f"Warning: Gemini did not return a Python code block. Full response:\n{response.text}"
            )
            return f"Gemini could not extract a valid Python code block from its response. Please inspect the full response:\n{response.text}"
    except Exception as e:
        return f"Error interacting with Gemini API or parsing response: {e}\nResponse text:\n{response.text}"


# --- Main Automation Loop ---


def main():
    print(f"Starting automated debugging for {CODE_FILE_PATH}")

    # Read the initial code
    try:
        with open(CODE_FILE_PATH, "r") as f:
            current_code = f.read()
    except FileNotFoundError:
        print(
            f"Error: Code file not found at {CODE_FILE_PATH}. Please ensure it exists."
        )
        return

    print("\n--- Initial Code Content (first 200 chars) ---")
    print(current_code[:200] + "..." if len(current_code) > 200 else current_code)
    print("---------------------------------------------")

    for attempt in range(MAX_DEBUG_ATTEMPTS):
        print(f"\n--- Attempt {attempt + 1} of {MAX_DEBUG_ATTEMPTS} ---")

        # Run the code
        result = run_python_code_from_file(CODE_FILE_PATH)

        if result.startswith("SUCCESS:"):
            print("\n✅ Code ran successfully!")
            print(result[len("SUCCESS:\n") :])
            print("Automated debugging complete.")
            break
        elif result.startswith("ERROR:"):
            error_message = result[len("ERROR:\n") :]
            print("\n❌ Error encountered:")
            print(error_message)
            print("\nSending error to Gemini for a fix...")

            # Get fixed code from Gemini
            fixed_code = get_gemini_fix(current_code, error_message)

            if fixed_code.startswith(
                "Gemini could not extract"
            ) or fixed_code.startswith("Error interacting with"):
                print(fixed_code)
                print("Could not get a valid code fix from Gemini. Aborting.")
                break
            else:
                current_code = fixed_code  # Update the code content in memory

                # Write the updated code back to the file
                try:
                    with open(CODE_FILE_PATH, "w") as f:
                        f.write(current_code)
                    print(f"\n✨ Code updated in {CODE_FILE_PATH}. Retrying...")
                except IOError as e:
                    print(f"Error writing updated code to file: {e}")
                    print("Aborting as file cannot be updated.")
                    break
        else:  # Critical error in execution script (e.g., Python not found)
            print("\n❗ Critical execution error:")
            print(result)
            print("Aborting due to critical execution error.")
            break
    else:
        print(f"\n🚫 Failed to fix the code after {MAX_DEBUG_ATTEMPTS} attempts.")
        print(
            f"The last attempted code is in {CODE_FILE_PATH}. Please review manually."
        )


if __name__ == "__main__":
    main()
