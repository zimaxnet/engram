"""
Metrics and telemetry endpoints

Provides API for:
- Evidence telemetry snapshots
- System alerts
- Operational metrics
"""

import logging
from datetime import datetime, timedelta
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.api.middleware.auth import get_current_user
from backend.core import SecurityContext

logger = logging.getLogger(__name__)

router = APIRouter()


class MetricCard(BaseModel):
    """Single metric card"""
    label: str
    value: str
    status: Literal["ok", "warn", "bad"]
    note: Optional[str] = None


class AlertItem(BaseModel):
    """Alert/incident item"""
    id: str
    severity: Literal["P0", "P1", "P2", "P3"]
    title: str
    detail: str
    time_label: str
    status: Literal["open", "closed"]


class EvidenceTelemetrySnapshot(BaseModel):
    """Complete evidence telemetry snapshot"""
    range_label: Literal["15m", "1h", "24h", "7d"]
    reliability: List[MetricCard]
    ingestion: List[MetricCard]
    memory_quality: List[MetricCard]
    alerts: List[AlertItem]
    narrative: dict[str, str]  # elena, marcus
    changes: List[dict[str, str]]


@router.get("/evidence", response_model=EvidenceTelemetrySnapshot)
async def get_evidence_telemetry(
    range: Literal["15m", "1h", "24h", "7d"] = Query("15m", alias="range"),
    user: SecurityContext = Depends(get_current_user),
):
    """
    Get evidence telemetry snapshot for the specified time range.

    Returns operational metrics, alerts, and agent narratives.
    """
    try:
        # In production, this would query:
        # - Application Insights / OpenTelemetry metrics
        # - Recent alerts from monitoring system
        # - Agent-generated narratives from recent analysis
        
        # For now, return deterministic mock data
        # In production, aggregate from:
        # - Azure Monitor metrics (API p95, error rate)
        # - Temporal workflow metrics (success rate, stuck workflows)
        # - ETL processor metrics (parse success, queue depth)
        # - Memory metrics (retrieval hit-rate, provenance coverage)
        
        snapshot = EvidenceTelemetrySnapshot(
            range_label=range,
            reliability=[
                MetricCard(label="API p95", value="420ms", status="ok"),
                MetricCard(label="Error rate", value="0.6%", status="ok"),
                MetricCard(label="Workflow success", value="99.2%", status="ok", note="Warn if < 98%"),
                MetricCard(label="Stuck workflows", value="0", status="ok"),
            ],
            ingestion=[
                MetricCard(label="Parse success", value="97.8%", status="warn", note="Warn if < 98%"),
                MetricCard(label="Queue depth", value="14", status="ok"),
                MetricCard(label="Time-to-searchable p95", value="2.1m", status="ok"),
            ],
            memory_quality=[
                MetricCard(label="Retrieval hit-rate", value="92%", status="ok"),
                MetricCard(label="Provenance coverage", value="88%", status="warn"),
                MetricCard(label="Tenant violations", value="0", status="ok"),
            ],
            alerts=[
                AlertItem(
                    id="a-1",
                    severity="P2",
                    title="Parse failures elevated",
                    detail="SharePoint source showing increased PDF parse failures; validate OCR strategy and credentials.",
                    time_label="8m ago",
                    status="open",
                ),
                AlertItem(
                    id="a-2",
                    severity="P3",
                    title="Provenance coverage drifting",
                    detail="Some memory results missing filename/source metadata; verify ingestion metadata normalization.",
                    time_label="1h ago",
                    status="open",
                ),
            ],
            narrative={
                "elena": "Impact: ingest drift reduces confidence in policy Q&A and increases hallucination risk. Hypothesis: connector auth expiry or filetype drift. Verify: run Golden Thread and compare metadata contracts.",
                "marcus": "Plan: pause SharePoint polling, sample failing docs, confirm credentials. ETA: 45m. If Golden Thread fails, rollback last deploy.",
            },
            changes=[
                {"label": "Deploy", "value": "backend@0461f71 → cfed567"},
                {"label": "Config", "value": "chunk_profile: auto → tables"},
                {"label": "SLO", "value": "parse warn threshold 98%"},
            ],
        )
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Failed to get evidence telemetry: {e}")
        # Return minimal snapshot on error
        return EvidenceTelemetrySnapshot(
            range_label=range,
            reliability=[],
            ingestion=[],
            memory_quality=[],
            alerts=[],
            narrative={"elena": "Error loading telemetry", "marcus": "Error loading telemetry"},
            changes=[],
        )


@router.get("/alerts", response_model=List[AlertItem])
async def get_alerts(
    severity: Optional[Literal["P0", "P1", "P2", "P3"]] = None,
    status: Optional[Literal["open", "closed"]] = Query(None, alias="status"),
    user: SecurityContext = Depends(get_current_user),
):
    """
    Get active alerts.

    Can be filtered by severity and status.
    """
    try:
        # In production, query alerting system (e.g., Azure Monitor Alerts)
        # For now, return mock alerts
        alerts = [
            AlertItem(
                id="a-1",
                severity="P2",
                title="Parse failures elevated",
                detail="SharePoint source showing increased PDF parse failures",
                time_label="8m ago",
                status="open",
            ),
            AlertItem(
                id="a-2",
                severity="P3",
                title="Provenance coverage drifting",
                detail="Some memory results missing filename/source metadata",
                time_label="1h ago",
                status="open",
            ),
        ]
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        return alerts
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        return []

