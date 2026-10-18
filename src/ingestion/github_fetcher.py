import os
from github import Github
from dotenv import load_dotenv

load_dotenv()


ALLOWED_EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.css', '.html', '.json', '.md'}
EXCLUDED_DIRS = {'node_modules', '.git', '.next', 'dist', 'build', '__pycache__', 'venv', '.venv', '.github', 'target'}
EXCLUDED_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'poetry.lock', 'pipfile.lock', 'composer.lock', 'cargo.lock', 'go.sum'
}
MAX_FILE_SIZE = 50 * 1024  # 50 KB limit per file to save credits

def fetch_repo_files(repo_full_name: str, github_token: str | None = None):
    """
    Fetches all relevant code files from a GitHub repo.
    repo_full_name: e.g. 'username/reponame'
    Returns: list of dicts with {path, content}
    """
    token = github_token or os.getenv("GITHUB_TOKEN")
    g = Github(token)
    repo = g.get_repo(repo_full_name)

    files_data = []
    root_contents = repo.get_contents("")
    contents: list = root_contents if isinstance(root_contents, list) else [root_contents]

    while contents:
        file_item = contents.pop(0)
        if file_item.type == "dir":
            if file_item.name in EXCLUDED_DIRS:
                continue
            sub_contents = repo.get_contents(file_item.path)
            if isinstance(sub_contents, list):
                contents.extend(sub_contents)
            else:
                contents.append(sub_contents)
        else:
            file_name_lower = file_item.name.lower()
            
            # Skip lockfiles and minified files (major credit drainers)
            if file_name_lower in EXCLUDED_FILES or file_name_lower.endswith('.min.js') or file_name_lower.endswith('.min.css'):
                continue

            # Skip large files > 50KB
            if hasattr(file_item, 'size') and file_item.size and file_item.size > MAX_FILE_SIZE:
                continue

            ext = os.path.splitext(file_item.name)[1]
            if ext in ALLOWED_EXTENSIONS:
                try:
                    content = file_item.decoded_content.decode('utf-8')
                    if len(content) > MAX_FILE_SIZE:
                        continue
                    files_data.append({
                        "path": file_item.path,
                        "content": content
                    })
                except Exception:
                    pass

    return files_data
