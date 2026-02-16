import os

CODE_EXTENSIONS = [".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp"]

IGNORE_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    "dist",
    "build"
}

def scan_repository(repo_path: str):
    repo_map = []

    for root, dirs, files in os.walk(repo_path):

        # 🔥 Skip heavy folders
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if any(file.endswith(ext) for ext in CODE_EXTENSIONS):
                full_path = os.path.join(root, file)

                repo_map.append({
                    "file": file,
                    "path": full_path,
                    "size_kb": round(os.path.getsize(full_path)/1024,2)
                })

    return repo_map
