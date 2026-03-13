"""Deploy Skill Match Hub to HuggingFace Spaces."""
import os
from huggingface_hub import HfApi, create_repo

REPO_ID = "Lazerai/skill-match-hub"
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

api = HfApi()

# Create the Space (Docker SDK)
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
    print(f"Space creation: {e}")

# Add GROQ_API_KEY as a secret — reads from .env file
groq_key = os.getenv("GROQ_API_KEY", "")
if groq_key:
    try:
        api.add_space_secret(
            repo_id=REPO_ID,
            key="GROQ_API_KEY",
            value=groq_key,
        )
        print("Secret GROQ_API_KEY set.")
    except Exception as e:
        print(f"Secret: {e}")
else:
    print("No GROQ_API_KEY found in environment. Set it manually in Space settings.")

# Upload everything
print("Uploading files to Space...")
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
        "src/*",
    ],
)
print(f"Done! Space live at: https://huggingface.co/spaces/{REPO_ID}")
