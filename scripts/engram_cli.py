#!/usr/bin/env python3
"""
Engram CLI Tool
Unified interface for Engram operations: enrichment, authentication, and status.

Usage:
  engram enrich --message "Commit message" --diff-stat "..."
  engram auth --check
  engram status
"""

import argparse
import base64
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("engram-cli")

# Configuration Defaults (can be overridden by params or env)
DEFAULT_API_URL = os.getenv("ENGRAM_API_URL", "https://engram.work")
CLIENT_ID = os.getenv("ENGRAM_CLIENT_ID", "a1ad61ce-387b-4043-ad08-68f7b5391da4")  # Default or Env


class EngramCLI:
    def __init__(self, api_url: str = DEFAULT_API_URL, client_id: str = CLIENT_ID):
        self.api_url = api_url.rstrip("/")
        self.client_id = client_id

    def _get_azure_token(self) -> str:
        """
        Get Access Token using Azure CLI.
        This relies on the developer being logged in via 'az login'.
        """
        try:
            # We request a token for the Engram API scope
            # Ensure resource ID matches what is expected by the backend (api://<client-id>)
            resource = f"api://{self.client_id}"
            
            logger.debug(f"Requesting Azure token for resource: {resource}")
            
            result = subprocess.run(
                [
                    "az", "account", "get-access-token",
                    "--resource", resource,
                    "--query", "accessToken",
                    "--output", "tsv"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error("Failed to get Azure token via CLI. Run 'az login' first.")
            logger.debug(f"Error details: {e.stderr}")
            sys.exit(1)
        except FileNotFoundError:
            logger.error("Azure CLI ('az') not found. Please install it.")
            sys.exit(1)

    def _call_api(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Execute authenticated API call"""
        token = self._get_azure_token()
        url = f"{self.api_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Client": "engram-cli/1.0"
        }
        
        try:
            body = json.dumps(data).encode("utf-8") if data else None
            request = Request(url, data=body, headers=headers, method=method)
            
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            logger.error(f"API Error ({e.code}): {error_body}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            sys.exit(1)

    def auth_check(self):
        """Verify authentication and connectivity"""
        logger.info("Checking Azure CLI authentication...")
        token = self._get_azure_token()
        logger.info("✅ Azure CLI token acquired successfully.")
        
        # Decode token to show user (locally only)
        try:
            # JWT parts are base64 encoded
            payload_part = token.split(".")[1]
            # Add padding
            payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_part))
            
            logger.info(f"   User: {payload.get('name', 'Unknown')}")
            logger.info(f"   OID:  {payload.get('oid')}")
            logger.info(f"   Exp:  {datetime.fromtimestamp(payload.get('exp'))}")
        except Exception as e:
            logger.warning(f"Could not decode token locally: {e}")

        logger.info(f"Verifying API connectivity to {self.api_url}...")
        # Try a health check or simple echo
        try:
            self._call_api("/api/v1/health")
            logger.info("✅ API connection verified.")
        except:
             logger.warning("⚠️ Could not verify API health, but token acquisition worked.")

    def enrich(self, message: str, diff_stat: Optional[str] = None):
        """enrich memory with commit context"""
        logger.info("Enriching memory with commit context...")
        
        payload = {
            "text": message,
            "session_id": f"git-{int(time.time())}", 
            "metadata": {
                "source": "git-commit",
                "diff_stat": diff_stat
            }
        }
        
        # Use existing endpoint or dedicated git one?
        # Using generic /enrich for now
        response = self._call_api("/api/v1/memory/enrich", method="POST", data=payload)
        
        if response.get("success"):
            logger.info("✅ Context pushed to Engram successfully.")
        else:
            logger.error(f"❌ Failed to push context: {response}")


def get_git_info() -> Dict[str, str]:
    """Capture validation info from current git repo"""
    try:
        # Get last commit message if not provided?
        # Actually for 'post-commit' hook, HEAD is the new commit
        msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True).strip()
        stat = subprocess.check_output(["git", "diff", "HEAD~1", "--stat"], text=True).strip()
        return {"message": msg, "stat": stat}
    except Exception as e:
        logger.warning(f"Could not read git info: {e}")
        return {"message": "Manual Enrichment", "stat": ""}

def main():
    parser = argparse.ArgumentParser(description="Engram Enterprise CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Auth Command
    subparsers.add_parser("auth", help="Verify authentication status")
    
    # Enrich Command
    enrich_parser = subparsers.add_parser("enrich", help="Push context to memory")
    enrich_parser.add_argument("--message", help="Context message (default: last git commit)")
    enrich_parser.add_argument("--source", default="manual", help="Source identifier")
    
    args = parser.parse_args()
    
    cli = EngramCLI()
    
    if args.command == "auth":
        cli.auth_check()
    
    elif args.command == "enrich":
        message = args.message
        diff_stat = None
        
        if not message and args.source == "git-commit":
            # Auto-detect from git
            git_info = get_git_info()
            message = git_info["message"]
            diff_stat = git_info["stat"]
            
        if not message:
             logger.error("Message is required for manual enrichment.")
             sys.exit(1)
             
        cli.enrich(message, diff_stat)
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
