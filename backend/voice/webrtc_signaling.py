"""
WebRTC Signaling Service

Handles WebRTC peer connection management for Avatar video streams.
Uses aiortc to create/manage RTCPeerConnection instances and handle SDP exchange.

Architecture:
- Frontend sends SDP offer via WebSocket ('avatar_connect' message)
- This service creates an RTCPeerConnection, sets remote description, generates answer
- Answer is sent back to frontend to complete the WebRTC handshake
- Video tracks received from Azure are forwarded to the browser
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCConfiguration

logger = logging.getLogger(__name__)


class WebRTCSession:
    """
    Manages a single WebRTC session for an avatar connection.
    
    Lifecycle:
    1. Created when frontend sends avatar_connect
    2. handle_offer() processes the SDP offer and returns answer
    3. add_ice_candidate() handles trickle ICE (if enabled)
    4. Tracks received via on_track callback are forwarded to frontend
    5. close() cleans up when session ends
    """
    
    def __init__(
        self, 
        session_id: str,
        on_track: Optional[Callable] = None,
        ice_servers: Optional[list] = None
    ):
        self.session_id = session_id
        self.on_track_callback = on_track
        
        # Configure ICE servers (STUN/TURN)
        if ice_servers:
            ice_server_objs = [
                RTCIceServer(urls=server.get("urls", []), 
                            username=server.get("username"),
                            credential=server.get("credential"))
                for server in ice_servers
            ]
            config = RTCConfiguration(iceServers=ice_server_objs)
        else:
            # Default to Google STUN for testing
            config = RTCConfiguration(iceServers=[
                RTCIceServer(urls=["stun:stun.l.google.com:19302"])
            ])
        
        self.pc = RTCPeerConnection(configuration=config)
        self._setup_handlers()
        
        logger.info(f"WebRTC session created: {session_id}")
    
    def _setup_handlers(self):
        """Set up event handlers for the peer connection"""
        
        @self.pc.on("track")
        def on_track(track):
            logger.info(f"📹 WebRTC track received: {track.kind} for session {self.session_id}")
            if self.on_track_callback:
                asyncio.create_task(self.on_track_callback(track))
            
            @track.on("ended")
            async def on_ended():
                logger.info(f"Track ended: {track.kind}")
        
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state: {self.pc.connectionState}")
            if self.pc.connectionState == "failed":
                await self.close()
        
        @self.pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.debug(f"ICE connection state: {self.pc.iceConnectionState}")
    
    async def handle_offer(self, sdp_offer: str) -> str:
        """
        Process an SDP offer from the client and generate an answer.
        
        Args:
            sdp_offer: The SDP offer string from the frontend
            
        Returns:
            The SDP answer string to send back to the frontend
        """
        logger.info(f"Processing SDP offer for session {self.session_id}")
        
        try:
            offer = RTCSessionDescription(sdp=sdp_offer, type="offer")
            await self.pc.setRemoteDescription(offer)
            
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            
            logger.info(f"Generated SDP answer for session {self.session_id}")
            return self.pc.localDescription.sdp
            
        except Exception as e:
            logger.error(f"Error handling SDP offer: {e}")
            raise
    
    async def add_ice_candidate(self, candidate: dict):
        """Add a remote ICE candidate (for trickle ICE)"""
        try:
            from aiortc import RTCIceCandidate
            ice_candidate = RTCIceCandidate(
                candidate=candidate.get("candidate"),
                sdpMid=candidate.get("sdpMid"),
                sdpMLineIndex=candidate.get("sdpMLineIndex")
            )
            await self.pc.addIceCandidate(ice_candidate)
            logger.debug(f"Added ICE candidate for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error adding ICE candidate: {e}")
    
    async def close(self):
        """Clean up the peer connection"""
        logger.info(f"Closing WebRTC session: {self.session_id}")
        await self.pc.close()


class WebRTCSignalingService:
    """
    Manages multiple WebRTC sessions for avatar video streaming.
    
    This service is used by the voice router to handle WebRTC signaling
    messages from the frontend.
    """
    
    def __init__(self):
        self.sessions: Dict[str, WebRTCSession] = {}
    
    def create_session(
        self, 
        session_id: str, 
        on_track: Optional[Callable] = None,
        ice_servers: Optional[list] = None
    ) -> WebRTCSession:
        """Create a new WebRTC session"""
        if session_id in self.sessions:
            # Clean up existing session
            asyncio.create_task(self.sessions[session_id].close())
        
        session = WebRTCSession(session_id, on_track, ice_servers)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[WebRTCSession]:
        """Get an existing WebRTC session"""
        return self.sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """Close and remove a WebRTC session"""
        if session_id in self.sessions:
            await self.sessions[session_id].close()
            del self.sessions[session_id]
    
    async def close_all(self):
        """Close all WebRTC sessions"""
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)


# Singleton instance
webrtc_signaling_service = WebRTCSignalingService()
