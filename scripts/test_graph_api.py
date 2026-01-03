#!/usr/bin/env python
"""Test Microsoft Graph API integration for Elena."""

import asyncio
from backend.integrations.graph_client import graph_client


async def test():
    print("=" * 60)
    print("Microsoft Graph API Test for Elena")
    print("=" * 60)
    print()
    
    print(f"Configured: {graph_client.is_configured}")
    print(f"User Email: {graph_client.user_email}")
    print()
    
    if not graph_client.is_configured:
        print("❌ Graph client not configured - check MS_GRAPH_* env vars")
        return
    
    # Test 1: Get access token
    print("1. Testing OAuth Token...")
    try:
        token = await graph_client._get_access_token()
        print(f"   ✅ Token obtained: {token[:30]}...")
    except Exception as e:
        print(f"   ❌ Token Error: {e}")
        return
    
    # Test 2: List inbox
    print()
    print("2. Testing Email (List Inbox)...")
    try:
        emails = await graph_client.list_emails("inbox", limit=5)
        print(f"   ✅ Inbox has {len(emails)} emails")
        for e in emails[:3]:
            subj = e["subject"][:40] if len(e["subject"]) > 40 else e["subject"]
            print(f"      - From: {e['from']}, Subject: {subj}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Send test email (this will actually send!)
    print()
    print("3. Testing Send Email to derek@zimax.net...")
    try:
        result = await graph_client.send_email(
            to=["derek@zimax.net"],
            subject="Elena is Online - Test from Engram",
            body="""
            <h1>Hello from Elena!</h1>
            <p>This is a test email sent via Microsoft Graph API.</p>
            <p>Elena can now:</p>
            <ul>
                <li>Send and receive emails</li>
                <li>Access OneDrive documents</li>
                <li>Manage calendar (coming soon)</li>
            </ul>
            <p>Regards,<br/>
            <strong>Elena Vasquez</strong><br/>
            Business Analyst AI Agent<br/>
            Zimax Networks, LC</p>
            """,
            body_type="HTML",
        )
        print(f"   ✅ Email sent: {result}")
    except Exception as e:
        print(f"   ❌ Send Error: {e}")
    
    # Test 4: OneDrive
    print()
    print("4. Testing OneDrive...")
    try:
        files = await graph_client.list_files("/", limit=5)
        print(f"   ✅ OneDrive root has {len(files)} items")
        for f in files[:3]:
            print(f"      - {f['name']} ({f['type']})")
    except Exception as e:
        print(f"   ❌ OneDrive Error: {e}")
        print("      (This is normal if Elena hasn't accessed OneDrive yet)")
    
    print()
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test())
