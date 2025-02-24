import os
import openai
import requests

# GitHub API details
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PR_NUMBER = os.getenv("GITHUB_REF").split("/")[-1]
REPO = os.getenv("GITHUB_REPOSITORY")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def get_pr_files():
    """Fetches the changed files in the PR."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=HEADERS)
    return [file["filename"] for file in response.json()]

def get_file_content(file_path):
    """Fetches the content of a file."""
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("content", "").encode('utf-8').decode('utf-8')
    return None

def review_code(file_name, file_content):
    """Sends the code to OpenAI for review."""
    prompt = f"""
    You are a senior software engineer reviewing a pull request.
    The following file was modified: {file_name}.
    
    Review this code based on:
    1. Code structure and readability
    2. Naming conventions
    3. Documentation clarity
    4. Performance improvements
    5. Potential bugs
    6. Testing recommendations

    Code:
    ```
    {file_content}
    ```

    Provide a structured review with bullet points.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "You are a professional code reviewer."},
                  {"role": "user", "content": prompt}]
    )
    
    return response["choices"][0]["message"]["content"]

def comment_on_pr(review_text):
    """Posts a comment on the PR."""
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    payload = {"body": review_text}
    requests.post(url, headers=HEADERS, json=payload)

# Main Execution
files = get_pr_files()
review_comments = []

for file in files:
    content = get_file_content(file)
    if content:
        review = review_code(file, content)
        review_comments.append(f"### Review for `{file}`\n{review}")

if review_comments:
    comment_on_pr("\n\n".join(review_comments))
