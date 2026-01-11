#!/usr/bin/env python3
"""
Documentation Standardizer
Enforces standards on all Markdown files in the docs directory.
1. Checks/Adds Front Matter (layout, title, parent).
2. Cleans up manual breadcrumbs.
3. Ensures index.md exists for navigation.
"""

import os
from pathlib import Path
import re

DOCS_DIR = Path("docs")

# Map folder names to Display Titles for 'parent' field
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

def clean_title(text):
    """Extract clean title from filename or header"""
    text = text.replace(".md", "").replace("-", " ").title()
    # Fix common acronyms
    for acronym in ["Ai", "Api", "Ui", "Iac", "Poc", "Sop"]:
        text = text.replace(acronym, acronym.upper())
    return text

def standardize_file(file_path: Path, parent_section: str = None):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Check for Front Matter
    has_fm = content.startswith("---\n")
    fm_lines = []
    body = content
    
    existing_fm = {}
    
    if has_fm:
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_raw = parts[1]
            body = parts[2].lstrip()
            
            # Parse existing simple YAML
            for line in fm_raw.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    existing_fm[k.strip()] = v.strip()
    
    # 2. Determine Title
    title = existing_fm.get("title")
    if not title:
        # Try to find first H1
        h1_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
            # Remove H1 from body if we move it to metadata? 
            # Prefer keeping H1 for rendering, but title tags need it too.
            # Let's clean the H1 if it contains breadcrumbs
            if "[" in title and "]" in title: # e.g. [Home] > Architecture
                 title = clean_title(file_path.name)
        else:
            title = clean_title(file_path.name)
            
    # Clean up title characters
    title = title.replace('"', '').strip()

    # 3. Build New Front Matter
    new_fm = ["---"]
    new_fm.append("layout: default")
    new_fm.append(f'title: "{title}"')
    
    if parent_section and parent_section != title:
        new_fm.append(f'parent: "{parent_section}"')
        
    # Preserve other keys?
    for k, v in existing_fm.items():
        if k not in ["layout", "title", "parent", "nav_order", "has_children"]:
            new_fm.append(f"{k}: {v}")
            
    # Add nav info for Index files
    if file_path.name == "index.md":
        if file_path.parent.name in NAVIGATION_ORDER:
            new_fm.append(f"nav_order: {NAVIGATION_ORDER[file_path.parent.name]}")
        new_fm.append("has_children: true")
        
    new_fm.append("---\n\n")
    
    # 4. Clean Body
    # Remove manual breadcrumbs like "# [Home] > Architecture"
    body = re.sub(r'^#\s+\[Home\].*?\n', '', body, flags=re.MULTILINE)
    
    # 5. Write Back
    final_content = "\n".join(new_fm) + body
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    print(f"Standardized {file_path}")

def ensure_index_files():
    """Ensure every section folder has an index.md"""
    for folder_name, title in SECTION_TITLES.items():
        folder = DOCS_DIR / folder_name
        if not folder.exists():
            continue
            
        index_file = folder / "index.md"
        if not index_file.exists():
            # If README.md exists, rename it
            readme = folder / "README.md"
            if readme.exists():
                readme.rename(index_file)
                print(f"Renamed README.md to index.md in {folder_name}")
            else:
                # Create empty index
                with open(index_file, "w") as f:
                    f.write(f"# {title}\n\nSection Overview.\n")
                print(f"Created index.md in {folder_name}")

def main():
    ensure_index_files()
    
    # Walk docs
    for folder_name, section_title in SECTION_TITLES.items():
        folder = DOCS_DIR / folder_name
        if not folder.exists():
            continue
            
        for file in folder.glob("*.md"):
            standardize_file(file, parent_section=section_title)
            
    # Root files
    for file in DOCS_DIR.glob("*.md"):
        if file.name != "index.md": # Skip root index as it has no parent
            standardize_file(file, parent_section=None)

if __name__ == "__main__":
    main()
