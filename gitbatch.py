import os
import sys
import shutil
import stat
import requests
from git import Repo
import json

GEMINI_API_KEY = ' '  # Replace with your Gemini API key

if(GEMINI_API_KEY==' '):
  GEMINI_API_KEY = input("Please input your gemini api key [Get it at: https://aistudio.google.com/app/apikey]: ")

def clone_repo(repo_url, clone_dir='temp_repo'):
    """Clone the GitHub repo to a temporary directory."""
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir, onerror=handle_remove_readonly)  # Clean up previous clone
    print(f"Cloning repository from {repo_url}...")
    try:
        Repo.clone_from(repo_url, clone_dir)
    except Exception as e:
        print(f"Failed to clone repository: {e}")
        sys.exit(1)

def generate_tree(directory, prefix=""):
    """Recursively generate a tree structure for directories and files."""
    tree_str = ""
    files = sorted([f for f in os.listdir(directory) if f != ".git"])  # Ignore .git directory
    for i, file in enumerate(files):
        path = os.path.join(directory, file)
        connector = "├──" if i < len(files) - 1 else "└──"
        tree_str += f"{prefix}{connector} {file}\n"
        
        if os.path.isdir(path):
            # Recursively print the tree for sub-directories
            new_prefix = prefix + ("│   " if i < len(files) - 1 else "    ")
            tree_str += generate_tree(path, new_prefix)
    
    return tree_str

def read_readme(directory):
    """Read README.md content from the repository if available."""
    readme_path = os.path.join(directory, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "README.md not found in the repository."

def handle_remove_readonly(func, path, exc_info):
    """Handle read-only file deletion on Windows by changing permissions."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def call_gemini_api(repo_url, api_key, repo_tree, readme_content):
    """
    Calls the Gemini API with repo tree and README content to generate a batch file.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"

    # Payload for the API
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"Create a Windows batch script to first of all clone repo then going to project directory by cd [project_name] then run the following project by running main file whatever it is based on this directory tree and README of github project. Don't provide any other comments or symbols or explaination no thing at all. Not even tilde symbols I want directly executable batch file. Assume user has newly purchased windows system with nothing else. So check if all dependencies and requirements are installed, if something is not then install them and then run till the end till its purpose is served. We need final thing be running. Do everything nicely in detail. Batch file should be best it can be.\n\nDirectory Tree:\n{repo_tree}\n\nREADME Content:\n{readme_content}\n\nREPOSITORY LINK:{repo_url}\n"}
                ]
            }
        ]
    }

    # Headers
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Send POST request to the Gemini API
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()

            # Extract the generated text from the response
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                print("Error: No candidates found in the response.")
                return None
        else:
            print(f"Error from Gemini API: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None



def save_batch_file(batch_content, file_name='setup.bat'):
    """Save the generated batch script to a file."""
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    print(f"Batch file saved as {file_name}.")

def execute_batch_file(file_name='setup.bat'):
    """Execute the batch file."""
    os.system(file_name)

def main(repo_url):
    clone_dir = "temp_repo"  # Temporary directory to clone the repo

    # Step 1: Clone the repo
    clone_repo(repo_url, clone_dir)

    # Step 2: Generate directory tree structure and read README.md content
    directory_tree = generate_tree(clone_dir)
    readme_content = read_readme(clone_dir)

    # Step 3: Send data to Gemini API to generate a batch script
    batch_script = call_gemini_api(repo_url, GEMINI_API_KEY, directory_tree, readme_content)

    if batch_script:
        # Step 4: Save the batch script
        save_batch_file(batch_script)

        # Step 5: Execute the batch script if needed
        execute_choice = input("Do you want to execute the generated batch file now? (y/n): ").strip().lower()
        if execute_choice == 'y':
            execute_batch_file()

    # Step 6: Clean up the cloned repository
    shutil.rmtree(clone_dir, onerror=handle_remove_readonly)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_batch.py <github_repo_url>")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    main(repo_url)
