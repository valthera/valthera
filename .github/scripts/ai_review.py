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

def get_pr_details():
    """Fetches both PR description and changed files."""
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Error fetching PR details: {response.text}")
        return None, []
    
    pr_data = response.json()
    
    # Get files
    files_url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    files_response = requests.get(files_url, headers=HEADERS)
    
    if files_response.status_code != 200:
        print(f"Error fetching PR files: {files_response.text}")
        return pr_data["body"], []

    return pr_data["body"], [file["filename"] for file in files_response.json()]

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

def review_description(description):
    """Reviews the PR description for completeness."""
    prompt = f"""
    Review this Pull Request description and provide a very brief assessment (max 2 sentences).
    Focus on whether it clearly explains:
    - What changes are being made
    - Why the changes are needed
    - Any testing done
    - Any important notes or considerations
    
    If the description is missing important information, briefly state what's missing.
    If the description is good, simply confirm it's well documented.

    PR Description:
    ```
    {description or "No description provided"}
    ```
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a concise PR reviewer. Focus on description completeness."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

def review_code(file_name, file_content):
    """Sends the code to OpenAI for AI-powered review."""
    prompt = f"""
    Review this code file ({file_name}) and provide a very brief summary (max 3 sentences) focusing ONLY on potential issues or improvements needed.
    If no significant issues are found, simply state that the code looks good.
    If issues are found, briefly explain the main problems and their potential impact.

    Code:
    ```
    {file_content}
    ```
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a concise code reviewer. Focus only on significant issues."},
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
    # Get both PR description and files
    description, files = get_pr_details()
    
    reviews = []
    
    # Review PR description first
    desc_review = review_description(description)
    if desc_review:
        reviews.append("### PR Description Review\n" + desc_review)
    
    # Review each file
    for file in files:
        content = get_file_content(file)
        if content:
            review = review_code(file, content)
            if review:
                reviews.append(f"### `{file}`\n{review}")

    if reviews:
        full_review = "\n\n".join(reviews)
        if post_pr_comment(full_review):
            print("Successfully posted review comment")
        else:
            print("Failed to post review comment")
    else:
        print("No reviews generated")

if __name__ == "__main__":
    main()