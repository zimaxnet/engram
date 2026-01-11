#!/usr/bin/env python3
"""
Navigation Fixer
Ensures the top-level section folder indices (00-05) are widely confirmed as Root Nav Items.
"""

from pathlib import Path

SECTION_TITLES = {
    "00-strategy": "Strategy",
    "01-architecture": "Architecture",
    "02-developer": "Developer Guide",
    "03-operations": "Operations",
    "04-features": "Feature Specs",
    "05-knowledge-base": "Knowledge Base"
}

NAVIGATION_ORDER = {
    "00-strategy": 1,
    "01-architecture": 2,
    "02-developer": 3,
    "03-operations": 4,
    "04-features": 5,
    "05-knowledge-base": 6
}

def fix_index(folder_name, title):
    folder = Path("docs") / folder_name
    index_file = folder / "index.md"
    
    if not index_file.exists():
        print(f"Skipping {folder_name}: No index.md")
        return

    with open(index_file, "r") as f:
        content = f.read()

    # Split FM
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]
            
            # Reconstruct FM perfectly
            new_fm = [
                "---",
                "layout: default",
                f'title: "{title}"',
                f"nav_order: {NAVIGATION_ORDER[folder_name]}",
                "has_children: true",
                "---",
                "\n"
            ]
            
            # Write back
            with open(index_file, "w") as f:
                f.write("\n".join(new_fm) + body)
            print(f"Fixed {index_file}")
            return

    print(f"Skipping {index_file}: No Front Matter found to replace")

if __name__ == "__main__":
    for folder, title in SECTION_TITLES.items():
        fix_index(folder, title)
