"""Deploy Skill Match Hub to HuggingFace Spaces."""
import os
from huggingface_hub import HfApi, create_repo, CommitOperationDelete
from dotenv import load_dotenv

load_dotenv()

# Configuration
REPO_ID = "Lazerai/skill-match-hub"
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

# Read from environment or .env
HF_TOKEN = os.getenv("HF_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not HF_TOKEN:
    print("Error: HF_TOKEN not found in environment. Please set it in .env file.")
    exit(1)

# Initialize API
api = HfApi(token=HF_TOKEN)

# Create/Verify the Space
try:
    create_repo(
        repo_id=REPO_ID,
        repo_type="space",
        space_sdk="docker",
        exist_ok=True,
        private=False,
    )
    print(f"Space created/verified: {REPO_ID}")
except Exception as e:
    print(f"Space creation error: {e}")

# Set Secrets
if GROQ_KEY:
    try:
        api.add_space_secret(repo_id=REPO_ID, key="GROQ_API_KEY", value=GROQ_KEY)
        print("GROQ_API_KEY secret set.")
    except Exception as e:
        print(f"Secret set error: {e}")
else:
    print("Warning: GROQ_API_KEY not found. Skipping secret setting.")

# Cleanup remote repository first to ensure only current structure exists
print("Cleaning up remote repository...")
current_files = api.list_repo_files(repo_id=REPO_ID, repo_type="space")
unwanted_dirs = ["full_code", "src"]
unwanted_files = ["implementation_plan.md", "task.md", "walkthrough.md", "scratchpad_kwtj8s7b.md"]

operations = []
for file in current_files:
    if any(file.startswith(d + "/") for d in unwanted_dirs) or file in unwanted_files:
        operations.append(CommitOperationDelete(path_in_repo=file))

if operations:
    try:
        api.create_commit(
            repo_id=REPO_ID,
            repo_type="space",
            operations=operations,
            commit_message="Cleanup old structure"
        )
        print(f"Deleted {len(operations)} unwanted files from remote.")
    except Exception as e:
        print(f"Cleanup commit error: {e}")

# Upload current directory
print("Uploading local files...")
api.upload_folder(
    folder_path=LOCAL_DIR,
    repo_id=REPO_ID,
    repo_type="space",
    ignore_patterns=[
        ".git/*",
        ".env",
        "__pycache__/*",
        "*.pyc",
        "deploy_hf.py",
        ".venv/*",
        "Include/*",
        "Lib/*",
        "Scripts/*",
        "share/*",
        "plans/*",
    ],
)
print(f"Done! Space live at: https://huggingface.co/spaces/{REPO_ID}")
