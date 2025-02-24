import os
import openai
import requests
import base64

# GitHub API details
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PR_NUMBER = os.getenv("PR_NUMBER")
REPO = os.getenv("GITHUB_REPOSITORY")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def get_pr_files():
    """Fetches the changed files in the PR."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=HEADERS)

    print(f"GitHub API Response Status: {response.status_code}")
    print(f"GitHub API Response: {response.text}")

    if response.status_code != 200:
        raise Exception(f"GitHub API Error: {response.text}")

    try:
        return [file["filename"] for file in response.json()]
    except Exception as e:
        print("Error parsing JSON response:", e)
        return []

def get_file_content(file_path):
    """Fetches the content of a file from the PR."""
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        return base64.b64decode(data["content"]).decode('utf-8')
    
    print(f"Failed to fetch {file_path}: {response.status_code}")
    return None

def review_code(file_name, file_content):
    """Sends the code to OpenAI for AI-powered review."""
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
        messages=[{"role": "system", "content": "You are an expert code reviewer."},
                  {"role": "user", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"]

def comment_on_pr(review_text):
    """Posts a comment on the PR."""
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    payload = {"body": review_text}
    response = requests.post(url, headers=HEADERS, json=payload)

    if response.status_code != 201:
        print(f"Failed to post comment: {response.text}")

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
