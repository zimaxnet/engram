import logging
import os
from pathlib import Path
from typing import List, Optional
from fastapi import BackgroundTasks

from backend.etl.ingestion_service import ingestion_service

logger = logging.getLogger(__name__)

class GitRepoConnector:
    """
    Connector for ingesting Git Repositories (Local).
    Walks a directory and ingests code files.
    """
    
    # Extensions to include
    INCLUDE_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".h", 
        ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".sh", ".css", ".html"
    }
    
    # Directories to exclude
    EXCLUDE_DIRS = {
        ".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist", 
        ".idea", ".vscode", "target", "bin", "obj"
    }

    def __init__(self):
        pass

    async def ingest_repository(
        self, 
        repo_path: str, 
        user_id: str, 
        background_tasks: BackgroundTasks,
        branch: str = "main",
        max_files: int = 100
    ) -> List[dict]:
        """
        Walk a local repository path and ingest valid source files.
        """
        base_path = Path(repo_path).resolve()
        if not base_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
            
        logger.info(f"GitRepoConnector: Scanning {base_path} (max {max_files} files)")
        
        ingested_docs = []
        files_processed = 0
        
        for root, dirs, files in os.walk(base_path):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            
            for file in files:
                if files_processed >= max_files:
                    break
                    
                file_path = Path(root) / file
                if file_path.suffix.lower() not in self.INCLUDE_EXTENSIONS:
                    continue
                
                # Calculate relative path for filename/metadata
                rel_path = file_path.relative_to(base_path)
                
                try:
                    # Read content
                    # Skip files that aren't valid UTF-8 text
                    try:
                        content = file_path.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        continue
                        
                    # Skip empty files
                    if not content.strip():
                        continue
                        
                    # Metadata
                    metadata = {
                        "source": "git_repo",
                        "repository": base_path.name,
                        "branch": branch,
                        "filepath": str(rel_path),
                        "extension": file_path.suffix,
                        "session_prefix": "code-repo"
                    }
                    
                    # Ingest
                    result = await ingestion_service.ingest_text(
                        text=content,
                        filename=str(rel_path),
                        user_id=user_id,
                        background_tasks=background_tasks,
                        metadata=metadata
                    )
                    
                    ingested_docs.append(result.dict())
                    files_processed += 1
                    logger.debug(f"Ingested {rel_path}")
                    
                except Exception as e:
                    logger.warning(f"Failed to ingest {rel_path}: {e}")
            
            if files_processed >= max_files:
                logger.info(f"Reached max file limit ({max_files})")
                break
                
        logger.info(f"GitRepoConnector: Completed ingestion of {len(ingested_docs)} files from {base_path.name}")
        return ingested_docs

# Singleton
git_repo_connector = GitRepoConnector()
