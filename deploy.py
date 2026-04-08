"""Deploy SQL Arena to Hugging Face Spaces."""
from huggingface_hub import HfApi, create_repo

HF_USERNAME = "rahul2124"
REPO_NAME = "sql-arena"
REPO_ID = f"{HF_USERNAME}/{REPO_NAME}"

api = HfApi()

# Step 1: Create the Space
print(f"Creating Space: {REPO_ID}...")
try:
    create_repo(
        repo_id=REPO_ID,
        repo_type="space",
        space_sdk="docker",
        exist_ok=True,
    )
    print("Space created successfully!")
except Exception as e:
    print(f"Note: {e}")
    print("Continuing with upload...")

# Step 2: Upload all files
print(f"\nUploading files to {REPO_ID}...")
api.upload_folder(
    folder_path=".",
    repo_id=REPO_ID,
    repo_type="space",
    ignore_patterns=[
        "__pycache__",
        ".pytest_cache",
        "*.pyc",
        ".git",
        "test_*.py",
        "deploy.py",
        "validate.py",
        "test_graders.py",
        "test_environment.py",
        "test_quick.py",
    ],
)

print("\n" + "=" * 50)
print("DEPLOYMENT COMPLETE!")
print("=" * 50)
print(f"\nYour Space URL: https://huggingface.co/spaces/{REPO_ID}")
print(f"API URL: https://{HF_USERNAME}-{REPO_NAME}.hf.space")
print("\nWait 3-5 minutes for the Space to build.")