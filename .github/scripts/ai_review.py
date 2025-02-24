import os
import requests
import base64
from openai import OpenAI

# GitHub API details
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PR_NUMBER = os.getenv("PR_NUMBER")
REPO = os.getenv("GITHUB_REPOSITORY")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# OpenAI client initialization
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_pr_files():
    """Fetches the changed files in the PR."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Error fetching PR files: {response.text}")
        return []

    return [file["filename"] for file in response.json()]

def get_file_content(file_path):
    """Fetches the content of a file from the PR."""
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        try:
            data = response.json()
            return base64.b64decode(data["content"]).decode('utf-8')
        except Exception as e:
            print(f"Error decoding file content: {e}")
    return None

def review_code(file_name, file_content):
    """Sends the code to OpenAI for AI-powered review."""
    prompt = f"""
    You are a senior software engineer reviewing a pull request.
    The following file was modified: {file_name}

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

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert code reviewer."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

def post_pr_comment(comment):
    """Posts a single comment on the PR."""
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    response = requests.post(url, headers=HEADERS, json={"body": comment})
    return response.status_code == 201

def main():
    files = get_pr_files()
    if not files:
        print("No files to review")
        return

    reviews = []
    for file in files:
        content = get_file_content(file)
        if content:
            review = review_code(file, content)
            if review:
                reviews.append(f"### Review for `{file}`\n{review}")

    if reviews:
        full_review = "\n\n".join(reviews)
        if post_pr_comment(full_review):
            print("Successfully posted review comment")
        else:
            print("Failed to post review comment")

if __name__ == "__main__":
    main()