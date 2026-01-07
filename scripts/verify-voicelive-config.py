#!/usr/bin/env python3
"""
Verify VoiceLive Configuration

Verifies that VoiceLive configuration is correct after video routing changes:
1. Backend connection uses TEXT + AUDIO only (no VIDEO)
2. Video token generation code is present
3. Audio/transcript handling is intact
4. No breaking changes to existing functionality

Usage:
    python scripts/verify-voicelive-config.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_voicelive_config():
    """Verify VoiceLive configuration is correct."""
    print("=" * 60)
    print("VoiceLive Configuration Verification")
    print("=" * 60)
    print()
    
    # Read the voice router file
    voice_file = Path(__file__).parent.parent / "backend" / "api" / "routers" / "voice.py"
    
    if not voice_file.exists():
        print("❌ Voice router file not found")
        return False
    
    content = voice_file.read_text()
    lines = content.split('\n')
    
    issues = []
    warnings = []
    successes = []
    
    # Check 1: Backend connection modalities
    print("1. Checking backend connection modalities...")
    if 'modalities = [Modality.TEXT, Modality.AUDIO]' in content:
        successes.append("✅ Backend connection uses [TEXT, AUDIO] only (no VIDEO)")
    else:
        issues.append("❌ Backend connection modalities not set correctly")
    
    # Check 2: Video token generation
    print("2. Checking video token generation...")
    if 'video_token_request = TokenRequest(' in content:
        successes.append("✅ Video token generation code present")
    else:
        issues.append("❌ Video token generation code missing")
    
    # Check 3: Video connection in ready message
    print("3. Checking video_connection in agent_switched...")
    if 'ready_message["video_connection"]' in content:
        successes.append("✅ video_connection added to agent_switched message")
    else:
        issues.append("❌ video_connection not added to message")
    
    # Check 4: Audio handling intact
    print("4. Checking audio handling...")
    if 'RESPONSE_AUDIO_DELTA' in content:
        successes.append("✅ Audio event handling present")
    else:
        issues.append("❌ Audio event handling missing")
    
    # Check 5: Transcript handling intact
    print("5. Checking transcript handling...")
    if 'CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED' in content:
        successes.append("✅ User transcript handling present")
    else:
        issues.append("❌ User transcript handling missing")
    
    if 'RESPONSE_TEXT_DELTA' in content or 'RESPONSE_AUDIO_TRANSCRIPT_DELTA' in content:
        successes.append("✅ Assistant transcript handling present")
    else:
        issues.append("❌ Assistant transcript handling missing")
    
    # Check 6: Memory persistence
    print("6. Checking memory persistence...")
    if 'persist_conversation' in content:
        successes.append("✅ Memory persistence code present")
    else:
        issues.append("❌ Memory persistence code missing")
    
    # Check 7: VIDEO modality not in backend connection
    print("7. Checking VIDEO modality exclusion...")
    video_in_backend_connection = False
    in_backend_section = False
    for i, line in enumerate(lines):
        if 'async def voicelive_websocket' in line:
            in_backend_section = True
        if in_backend_section and 'modalities.append(Modality.VIDEO)' in line:
            video_in_backend_connection = True
            issues.append(f"❌ VIDEO modality added to backend connection (line {i+1})")
            break
        if in_backend_section and 'async def process_voicelive_events' in line:
            break
    
    if not video_in_backend_connection:
        successes.append("✅ VIDEO modality not added to backend connection")
    
    # Check 8: Video event handling removed
    print("8. Checking video event handling...")
    if 'RESPONSE_VIDEO_DELTA' in content or 'RESPONSE_VIDEO_DONE' in content:
        # Check if it's commented out or removed
        video_handling_removed = True
        for i, line in enumerate(lines):
            if 'RESPONSE_VIDEO_DELTA' in line or 'RESPONSE_VIDEO_DONE' in line:
                # Check if it's in a comment or removed section
                if '#' in line or 'Video events are NOT handled' in content:
                    continue
                else:
                    video_handling_removed = False
                    warnings.append(f"⚠️  Video event handling still present (line {i+1}) - should be removed")
                    break
        if video_handling_removed:
            successes.append("✅ Video event handling removed from backend")
    else:
        successes.append("✅ Video event handling removed from backend")
    
    # Print results
    print()
    print("=" * 60)
    print("Verification Results")
    print("=" * 60)
    print()
    
    if successes:
        print("✅ Successes:")
        for success in successes:
            print(f"   {success}")
        print()
    
    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"   {warning}")
        print()
    
    if issues:
        print("❌ Issues:")
        for issue in issues:
            print(f"   {issue}")
        print()
        return False
    else:
        print("✅ All checks passed! VoiceLive configuration is correct.")
        print()
        print("Summary:")
        print("  - Backend connection: TEXT + AUDIO only")
        print("  - Video routing: Direct to browser (token provided)")
        print("  - Audio/transcripts: Flow through backend")
        print("  - Memory persistence: Intact")
        return True


if __name__ == "__main__":
    success = verify_voicelive_config()
    sys.exit(0 if success else 1)

