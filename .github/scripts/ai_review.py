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

def check_github_permissions():
    """Checks if the token has the necessary permissions."""
    # First check the token's validity and scope
    url = "https://api.github.com/user"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"GitHub token validation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    # Check repository access
    url = f"https://api.github.com/repos/{REPO}"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Repository access check failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    # Check pull request access
    if PR_NUMBER:
        url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"Pull request access check failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    return True

def get_pr_files():
    """Fetches the changed files in the PR."""
    if not PR_NUMBER:
        print("Error: PR_NUMBER environment variable is not set")
        return []

    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    response = requests.get(url, headers=HEADERS)

    print(f"GitHub API Response Status: {response.status_code}")
    print(f"GitHub API Response: {response.text}")

    if response.status_code != 200:
        print(f"GitHub API Error: {response.text}")
        return []

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
        try:
            data = response.json()
            return base64.b64decode(data["content"]).decode('utf-8')
        except Exception as e:
            print(f"Error decoding file content: {e}")
            return None
    
    print(f"Failed to fetch {file_path}: {response.status_code}")
    print(f"Response: {response.text}")
    return None

def review_code(file_name, file_content):
    """Sends the code to OpenAI for AI-powered review."""
    if not file_content:
        return None

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

def comment_on_pr(review_text):
    """Posts a comment on the PR."""
    if not PR_NUMBER:
        print("Error: PR_NUMBER environment variable is not set")
        return False

    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    payload = {"body": review_text}
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        
        if response.status_code == 201:
            print("Successfully posted comment to PR")
            return True
        elif response.status_code == 403:
            print("Error: GitHub token lacks necessary permissions to post comments")
            print(f"Response: {response.text}")
            print("\nPlease ensure the GitHub token has the following permissions:")
            print("- repo (for private repositories)")
            print("- public_repo (for public repositories)")
            print("- write access to pull requests")
        else:
            print(f"Failed to post comment: {response.status_code}")
            print(f"Response: {response.text}")
        
        return False
    except Exception as e:
        print(f"Error posting comment: {e}")
        return False

def main():
    """Main execution function."""
    # First check if we have valid GitHub token and permissions
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable is not set")
        return

    if not check_github_permissions():
        print("Error: GitHub token validation failed")
        return

    print(f"Processing PR #{PR_NUMBER} in repository {REPO}")
    
    files = get_pr_files()
    if not files:
        print("No files found to review")
        return

    review_comments = []
    for file in files:
        print(f"Reviewing file: {file}")
        content = get_file_content(file)
        if content:
            review = review_code(file, content)
            if review:
                review_comments.append(f"### Review for `{file}`\n{review}")
        else:
            print(f"Skipping {file} due to missing content")

    if review_comments:
        if comment_on_pr("\n\n".join(review_comments)):
            print("Code review completed successfully")
        else:
            print("Failed to post review comments")
            # Write to a file instead
            with open("code_review.md", "w") as f:
                f.write("\n\n".join(review_comments))
            print("Review comments have been saved to code_review.md")
    else:
        print("No reviews were generated")

if __name__ == "__main__":
    main()