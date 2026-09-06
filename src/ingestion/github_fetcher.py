import os
from github import Github
from dotenv import load_dotenv

load_dotenv()


ALLOWED_EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.css', '.html', '.json', '.md'}
EXCLUDED_DIRS = {'node_modules', '.git', '.next', 'dist', 'build', '__pycache__', 'venv', '.venv'}

def fetch_repo_files(repo_full_name: str, github_token: str = None):
    """
    Fetches all relevant code files from a GitHub repo.
    repo_full_name: e.g. 'username/reponame'
    Returns: list of dicts with {path, content}
    """
    token = github_token or os.getenv("GITHUB_TOKEN")
    g = Github(token)
    repo = g.get_repo(repo_full_name)

    files_data = []
    contents = repo.get_contents("")

    while contents:
        file_item = contents.pop(0)
        if file_item.type == "dir":
            if file_item.name in EXCLUDED_DIRS:
                continue
            contents.extend(repo.get_contents(file_item.path))
        else:
            ext = os.path.splitext(file_item.name)[1]
            if ext in ALLOWED_EXTENSIONS:
                try:
                    content = file_item.decoded_content.decode('utf-8')
                    files_data.append({
                        "path": file_item.path,
                        "content": content
                    })
                except Exception:
                    pass

    return files_data
