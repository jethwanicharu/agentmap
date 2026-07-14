import os
from github import Github
from dotenv import load_dotenv

load_dotenv()

# File extensions we care about (skip binaries, images, etc.)
ALLOWED_EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.css', '.html', '.json', '.md'}

def fetch_repo_files(repo_full_name: str):
    """
    Fetches all relevant code files from a GitHub repo.
    repo_full_name: e.g. 'username/reponame'
    Returns: list of dicts with {path, content}
    """
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)
    repo = g.get_repo(repo_full_name)

    files_data = []
    contents = repo.get_contents("")

    while contents:
        file_item = contents.pop(0)
        if file_item.type == "dir":
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
                except Exception as e:
                    print(f"Skipping {file_item.path}: {e}")

    return files_data


if __name__ == "__main__":
    # quick test
    files = fetch_repo_files("your-username/your-test-repo")
    print(f"Fetched {len(files)} files")
    for f in files[:3]:
        print(f["path"])