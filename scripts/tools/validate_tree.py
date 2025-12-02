import re
from pathlib import Path


def validate_tree(root_path: str) -> None:
    """Validate directory tree for FFMP compliance."""
    root = Path(root_path)
    if not root.exists():
        print(f"Error: Path {root_path} does not exist.")
        return

    invalid_files = []
    for file_path in root.rglob("*"):
        if file_path.is_file():
            filename = file_path.name
            # Check for invalid characters (allow only A-Za-z0-9_-)
            if not re.match(r"^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)?$", filename):
                invalid_files.append(str(file_path))

    if invalid_files:
        print("Invalid filenames found:")
        for f in invalid_files:
            print(f"  - {f}")
    else:
        print("Tree is FFMP compliant.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validate_tree.py <root_path>")
        sys.exit(1)
    validate_tree(sys.argv[1])
    validate_tree(sys.argv[1])
