"""
Microsoft Graph API Client

Provides email, OneDrive, and calendar integration for AI agents.
Enables Elena to send/receive emails and read/write documents.

Required Azure AD App Registration:
- Application (not delegated) permissions:
  - Mail.Send
  - Mail.Read  
  - Files.ReadWrite.All
  - Calendars.ReadWrite
  - User.Read.All
- Admin consent required for all permissions

Environment Variables:
- MS_GRAPH_TENANT_ID: Azure AD tenant ID
- MS_GRAPH_CLIENT_ID: Application (client) ID
- MS_GRAPH_CLIENT_SECRET: Client secret value
- MS_GRAPH_USER_EMAIL: Target user email (elena@zimax.net)
"""

import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GraphClient:
    """
    Microsoft Graph API client for AI agent operations.
    
    Uses application permissions (client credentials flow) for
    daemon/service scenarios where no user is signed in.
    """
    
    def __init__(self):
        from backend.core import get_settings
        
        self.settings = get_settings()
        self.tenant_id = getattr(self.settings, 'ms_graph_tenant_id', None)
        self.client_id = getattr(self.settings, 'ms_graph_client_id', None)
        self.client_secret = getattr(self.settings, 'ms_graph_client_secret', None)
        self.user_email = getattr(self.settings, 'ms_graph_user_email', 'elena@zimax.net')
        
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        
        if self.tenant_id and self.client_id and self.client_secret:
            logger.info(f"GraphClient initialized for user: {self.user_email}")
        else:
            logger.warning("GraphClient: Missing credentials - MS Graph features disabled")
    
    @property
    def is_configured(self) -> bool:
        """Check if Graph API is properly configured."""
        return all([self.tenant_id, self.client_id, self.client_secret])
    
    async def _get_access_token(self) -> str:
        """Get OAuth2 access token using client credentials flow."""
        import httpx
        from datetime import timezone
        
        # Return cached token if still valid
        if self._access_token and self._token_expires:
            if datetime.now(timezone.utc) < self._token_expires:
                return self._access_token
        
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            self._access_token = data["access_token"]
            # Token typically valid for 1 hour, cache for 55 min
            from datetime import timedelta
            self._token_expires = datetime.now(timezone.utc) + timedelta(minutes=55)
            
            return self._access_token
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make authenticated request to Graph API."""
        import httpx
        
        if not self.is_configured:
            raise RuntimeError("GraphClient not configured - missing credentials")
        
        token = await self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        
        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
    
    # =========================================================================
    # Email Operations
    # =========================================================================
    
    async def send_email(
        self,
        to: list[str],
        subject: str,
        body: str,
        body_type: str = "HTML",
        cc: list[str] = None,
        importance: str = "normal",
    ) -> dict:
        """
        Send an email from Elena's mailbox.
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            body_type: "HTML" or "Text"
            cc: Optional list of CC recipients
            importance: "low", "normal", or "high"
            
        Returns:
            Empty dict on success (Graph API returns 202 Accepted)
        """
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": body_type,
                    "content": body,
                },
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
                "importance": importance,
            },
            "saveToSentItems": True,
        }
        
        if cc:
            message["message"]["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in cc
            ]
        
        await self._request(
            "POST",
            f"/users/{self.user_email}/sendMail",
            json=message,
        )
        
        logger.info(f"Email sent from {self.user_email} to {to}, subject: {subject}")
        return {"success": True, "to": to, "subject": subject}
    
    async def list_emails(
        self,
        folder: str = "inbox",
        limit: int = 10,
        unread_only: bool = False,
    ) -> list[dict]:
        """
        List emails from Elena's mailbox.
        
        Args:
            folder: Mail folder (inbox, sentitems, drafts, etc.)
            limit: Maximum emails to return
            unread_only: If True, only return unread emails
            
        Returns:
            List of email summaries
        """
        params = {
            "$top": limit,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
        }
        
        if unread_only:
            params["$filter"] = "isRead eq false"
        
        result = await self._request(
            "GET",
            f"/users/{self.user_email}/mailFolders/{folder}/messages",
            params=params,
        )
        
        return [
            {
                "id": msg["id"],
                "subject": msg.get("subject", "(no subject)"),
                "from": msg.get("from", {}).get("emailAddress", {}).get("address", "unknown"),
                "received": msg.get("receivedDateTime"),
                "is_read": msg.get("isRead", False),
                "preview": msg.get("bodyPreview", "")[:200],
            }
            for msg in result.get("value", [])
        ]
    
    async def read_email(self, email_id: str) -> dict:
        """Read full email content by ID."""
        result = await self._request(
            "GET",
            f"/users/{self.user_email}/messages/{email_id}",
        )
        
        return {
            "id": result["id"],
            "subject": result.get("subject", "(no subject)"),
            "from": result.get("from", {}).get("emailAddress", {}).get("address", "unknown"),
            "to": [r["emailAddress"]["address"] for r in result.get("toRecipients", [])],
            "received": result.get("receivedDateTime"),
            "body": result.get("body", {}).get("content", ""),
            "body_type": result.get("body", {}).get("contentType", "text"),
        }
    
    # =========================================================================
    # OneDrive Operations
    # =========================================================================
    
    async def list_files(
        self,
        folder_path: str = "/",
        limit: int = 20,
    ) -> list[dict]:
        """
        List files in Elena's OneDrive.
        
        Args:
            folder_path: Path to folder (/ for root)
            limit: Maximum items to return
            
        Returns:
            List of file/folder items
        """
        if folder_path == "/" or folder_path == "":
            endpoint = f"/users/{self.user_email}/drive/root/children"
        else:
            # URL encode the path
            import urllib.parse
            encoded_path = urllib.parse.quote(folder_path.strip("/"))
            endpoint = f"/users/{self.user_email}/drive/root:/{encoded_path}:/children"
        
        result = await self._request(
            "GET",
            endpoint,
            params={"$top": limit},
        )
        
        return [
            {
                "id": item["id"],
                "name": item["name"],
                "type": "folder" if "folder" in item else "file",
                "size": item.get("size", 0),
                "modified": item.get("lastModifiedDateTime"),
                "web_url": item.get("webUrl"),
            }
            for item in result.get("value", [])
        ]
    
    async def read_file(self, file_path: str) -> bytes:
        """
        Read file content from OneDrive.
        
        Args:
            file_path: Path to file (e.g., /Documents/report.docx)
            
        Returns:
            File content as bytes
        """
        import urllib.parse
        import httpx
        
        encoded_path = urllib.parse.quote(file_path.strip("/"))
        
        # Get download URL
        result = await self._request(
            "GET",
            f"/users/{self.user_email}/drive/root:/{encoded_path}",
            params={"$select": "@microsoft.graph.downloadUrl,name,size"},
        )
        
        download_url = result.get("@microsoft.graph.downloadUrl")
        if not download_url:
            raise ValueError(f"No download URL for file: {file_path}")
        
        # Download content
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(download_url)
            response.raise_for_status()
            return response.content
    
    async def write_file(
        self,
        file_path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> dict:
        """
        Write/upload a file to OneDrive.
        
        Args:
            file_path: Destination path (e.g., /Documents/report.md)
            content: File content as bytes
            content_type: MIME type of the content
            
        Returns:
            Created file metadata
        """
        import urllib.parse
        import httpx
        
        encoded_path = urllib.parse.quote(file_path.strip("/"))
        
        token = await self._get_access_token()
        
        url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/drive/root:/{encoded_path}:/content"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.put(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": content_type,
                },
                content=content,
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"File written to OneDrive: {file_path}")
        return {
            "id": result["id"],
            "name": result["name"],
            "web_url": result.get("webUrl"),
            "size": result.get("size", len(content)),
        }
    
    async def create_folder(self, folder_path: str) -> dict:
        """
        Create a folder in OneDrive.
        
        Args:
            folder_path: Full path including new folder name
            
        Returns:
            Created folder metadata
        """
        import urllib.parse
        
        # Split path into parent and new folder name
        parts = folder_path.strip("/").rsplit("/", 1)
        if len(parts) == 1:
            parent_path = ""
            folder_name = parts[0]
        else:
            parent_path = parts[0]
            folder_name = parts[1]
        
        if parent_path:
            encoded_parent = urllib.parse.quote(parent_path)
            endpoint = f"/users/{self.user_email}/drive/root:/{encoded_parent}:/children"
        else:
            endpoint = f"/users/{self.user_email}/drive/root/children"
        
        result = await self._request(
            "POST",
            endpoint,
            json={
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "fail",
            },
        )
        
        logger.info(f"Folder created in OneDrive: {folder_path}")
        return {
            "id": result["id"],
            "name": result["name"],
            "web_url": result.get("webUrl"),
        }


# Singleton instance
graph_client = GraphClient()
