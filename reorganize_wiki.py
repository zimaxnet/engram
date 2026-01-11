#!/usr/bin/env python3
"""
Documentation Reorganization Script
Migrates the flat/messy docs structure to a clean, persona-based Information Architecture.

New Structure:
- 00-strategy/        : Executive info, roadmaps, business plans
- 01-architecture/    : System design, diagrams, core concepts
- 02-developer/       : Dev guides, setup, IDE integration
- 03-operations/      : Deployment, auth, security, finops
- 04-features/        : Feature specs (Voice, Chat, Stories)
- 05-knowledge-base/  : SOPs, Troubleshooting, Post-mortems
- assets/             : Images/static files (kept as is)
"""

import os
import shutil
from pathlib import Path

# Mapping of file patterns/names to new directories
# Keys are destination directories (relative to docs root)
# Values are lists of glob patterns or filenames
MOVES = {
    "00-strategy": [
        "Executive_*", "Business_Plan*", "engram-pricing*", "engram-press*",
        "ai-periodic-table-roadmap*", "ai-periodic-table-business*",
        "Production-Grade-Agentic-System-Layers*", "milestones", 
        "next-steps.md", "Project-Tracking-Setup.md", "pricing.md",
        "Engram_Context_Engineering*", "UI_DESIGN_REFERENCE.md",
        "REORGANIZATION*"
    ],
    "01-architecture": [
        "architecture/*", "brain-spine*", "4-layer*", 
        "system-navigator.md", "concept/*", "diagrams/*",
        "Agentic-System-Maturity*", "enterprise-env-model*",
        "agents.md", "architecture.md", "architecture_summary.md",
        "ai-periodic-table-matrix.html", "ai-periodic-table-analysis.md"
    ],
    "02-developer": [
        "developer/*", "dev-guides/*", "getting-started/*", 
        "ide-context/*", "testing/*", "guides/*",
        "LOCAL-TESTING-GUIDE.md", "TESTING-GUIDE.md", "test-in-separate-terminal.md",
        "GitHub-Integration*", "How-to-Create-GitHub-Projects*",
        "IDE-Integration.md", "GitHub-Projects-Integration.md"
    ],
    "03-operations": [
        "deployment/*", "operations/*", "compliance/*", "configuration/*",
        "security/*", "finops*", "auth-*", "secrets-management.md",
        "azure-postgresql.md", "enterprise-auth*", "github-secrets.md",
        "storage-strategy.md", "vendor-monitoring.md", "setup-secrets-guide.md",
        "engram-enterprise-platform-deployment.html", "google_login_setup.md",
        "cors-configuration.md", "zep-enterprise-deployment.html",
        "unstructured-enterprise-deployment.html", "temporal-enterprise-deployment.html",
        "postgresql-blob-storage-enterprise-deployment.html", "navigation-ui-enterprise-deployment.html",
        "deployment.md", "enterprise_poc_guide.md", "config/*", "app-insights-guide.md",
        "data-plane-tagging.md", "development/*", "horizondb-testing.md", "local-testing.md",
        "stability/*"
    ],
    "04-features": [
        "features/*", "stories/*", "mobile-feature-specs/*",
        "voice-chat-integration.md", "visual-development*", 
        "knowledge-graph*", "document-ingestion-strategy*",
        "sage-visual-implementation-report.md", "connectors-plan.md"
    ],
    "05-knowledge-base": [
        "troubleshooting/*", "sop/*", "reference/*", "wiki/*", 
        "sessions/*", "memory/*",
        "bug-fixing-progress-report.md", "reorganize-docs.sh",
        "sop-*", "agents/*"
    ]
}

def reorganize():
    base_dir = Path("docs")
    if not base_dir.exists():
        print("Error: docs directory not found")
        return

    # Create new directories
    for dest_dir in MOVES.keys():
        (base_dir / dest_dir).mkdir(exist_ok=True)
        print(f"Created {dest_dir}")

    # Move files
    for dest, patterns in MOVES.items():
        dest_path = base_dir / dest
        
        for pattern in patterns:
            # Handle if pattern is a directory content copy vs folder move
            # For now, simplistic globbing
            
            # Check if source is a specific directory we want to merge contents of
            # or move entirely.
            # Strategy: Find all matches in base_dir (non-recursive to avoid moving already moved stuff)
            
            # We assume patterns match items directly in docs/ or subfolders referenced explicitly
            
            # Handle explicit subfolder references "architecture/*" means contents of architecture
            if "/" in pattern and "*" in pattern:
                 # e.g. "architecture/*" -> move contents of docs/architecture to docs/01-architecture
                 src_folder_name = pattern.split("/")[0]
                 src_folder = base_dir / src_folder_name
                 if src_folder.exists() and src_folder.is_dir():
                     for item in src_folder.iterdir():
                         target = dest_path / item.name
                         if not target.exists():
                             shutil.move(str(item), str(target))
                     print(f"Moved contents of {src_folder} to {dest}")
                     # Optionally remove empty dir
                     try:
                        src_folder.rmdir() 
                     except:
                        pass
                 continue
            
            # Handle direct file/dir matches in root
            for item in base_dir.glob(pattern):
                if item.parent == base_dir and item.name not in MOVES.keys():
                    target = dest_path / item.name
                    if not target.exists():
                        shutil.move(str(item), str(target))
                        print(f"Moved {item.name} -> {dest}")

if __name__ == "__main__":
    reorganize()
