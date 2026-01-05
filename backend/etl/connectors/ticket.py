import logging
import json
from datetime import datetime
from fastapi import BackgroundTasks

from backend.etl.ingestion_service import ingestion_service

logger = logging.getLogger(__name__)

class TicketConnector:
    """
    Connector for ingesting Support Tickets (Jira, ServiceNow, Zendesk).
    Converts structured ticket data into a text transcript for RAG.
    """
    
    def __init__(self):
        pass

    def format_ticket_to_text(self, ticket: dict) -> str:
        """
        Convert ticket JSON to a readable text transcript.
        """
        lines = []
        
        # Header
        ticket_id = ticket.get("id", "UNKNOWN")
        title = ticket.get("title", "No Title")
        status = ticket.get("status", "Open")
        priority = ticket.get("priority", "Normal")
        created = ticket.get("created_at", "Unknown Date")
        
        lines.append(f"TICKET: {ticket_id} - {title}")
        lines.append(f"STATUS: {status} | PRIORITY: {priority} | CREATED: {created}")
        lines.append("-" * 40)
        
        # Description
        description = ticket.get("description", "")
        if description:
            lines.append("DESCRIPTION:")
            lines.append(description)
            lines.append("-" * 40)
            
        # Comments / Thread
        comments = ticket.get("comments", [])
        if comments:
            lines.append(f"COMMENTS ({len(comments)}):")
            for comment in comments:
                author = comment.get("author", "Unknown")
                timestamp = comment.get("timestamp", "")
                body = comment.get("body", "")
                
                lines.append(f"[{timestamp}] {author}:")
                lines.append(body)
                lines.append("")
                
        return "\n".join(lines)

    async def ingest_ticket(self, ticket_data: dict, user_id: str, background_tasks: BackgroundTasks) -> dict:
        """
        Ingest a ticket object.
        """
        ticket_id = ticket_data.get("id", "ticket-unknown")
        logger.info(f"TicketConnector: Processing {ticket_id}")
        
        # Format to text
        text_content = self.format_ticket_to_text(ticket_data)
        
        # Metadata
        metadata = {
            "source": "ticket_connector",
            "ticket_id": ticket_id,
            "title": ticket_data.get("title"),
            "status": ticket_data.get("status"),
            "session_prefix": "ticket"  # Use specific prefix for Zep sessions
        }
        
        # Ingest
        result = await ingestion_service.ingest_text(
            text=text_content,
            filename=f"ticket_{ticket_id}.txt",
            user_id=user_id,
            background_tasks=background_tasks,
            metadata=metadata
        )
        
        logger.info(f"TicketConnector: Ingested {ticket_id} as {result.document_id}")
        return result.dict()

# Singleton
ticket_connector = TicketConnector()
