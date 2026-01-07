---
layout: default
title: Microsoft 365 Integration Research - Teams & Outlook
parent: Architecture
nav_order: 17
---

# Microsoft 365 Integration Research - Teams & Outlook

> **Status**: Research Complete  
> **Last Updated**: January 2026  
> **Priority**: High  
> **Timeline**: 3-4 weeks for implementation

---

## Executive Summary

Azure AI Foundry enables **native integration** with Microsoft 365, allowing Engram agents (especially Elena) to be published as Teams bots and Outlook add-ins. This provides seamless access to Teams, Outlook, and SharePoint, enhancing user productivity and expanding Engram's reach.

**Key Findings**:
- ✅ Foundry supports publishing agents to Microsoft Teams
- ✅ Outlook add-in integration available
- ✅ SharePoint connector for document access
- ✅ Simplified Graph API usage through Foundry
- ✅ Native Microsoft 365 user experience

---

## Current Microsoft 365 Integration

### Existing Implementation

**Elena's Microsoft Graph Integration**:
- ✅ Email sending and management (`send_email`, `list_emails`)
- ✅ OneDrive file operations (`list_files`, `save_file`)
- ✅ Uses `elena@zimax.net` Entra ID account
- ✅ Custom Graph client implementation
- ✅ OAuth2 authentication flow

**Current Capabilities**:
```python
# Elena's Microsoft Graph tools
- send_email(to, subject, body, attachments)
- list_emails(folder, limit)
- list_files(path)
- save_file(path, content)
```

**Limitations**:
- ⚠️ Requires explicit tool calls
- ⚠️ No native Teams integration
- ⚠️ No Outlook add-in
- ⚠️ No SharePoint direct access
- ⚠️ User must be in Engram interface

---

## Azure AI Foundry Microsoft 365 Integration

### Available Integrations

#### 1. **Microsoft Teams Bot**

**What It Is**:
- Publish Foundry agents as Teams bots
- Native Teams chat interface
- Direct access to Teams channels and chats
- Teams-specific features (mentions, reactions, cards)

**Capabilities**:
- ✅ Chat with Elena in Teams
- ✅ Access Teams channels and conversations
- ✅ Respond to Teams messages
- ✅ Use Teams adaptive cards
- ✅ Teams-specific authentication

**Use Cases**:
1. **Team Collaboration**: Elena helps with requirements in Teams channels
2. **Project Management**: Marcus tracks projects via Teams
3. **Documentation**: Sage shares stories in Teams
4. **Quick Questions**: Users ask Elena directly in Teams chat

#### 2. **Outlook Add-in**

**What It Is**:
- Outlook add-in for email assistance
- Compose emails with AI help
- Analyze email content
- Schedule and manage emails

**Capabilities**:
- ✅ Email composition assistance
- ✅ Email analysis and summarization
- ✅ Smart replies
- ✅ Meeting scheduling
- ✅ Email organization

**Use Cases**:
1. **Email Composition**: Elena helps draft professional emails
2. **Email Analysis**: Summarize long email threads
3. **Smart Replies**: Suggest responses based on context
4. **Meeting Coordination**: Schedule meetings from emails

#### 3. **SharePoint Integration**

**What It Is**:
- Direct access to SharePoint documents
- Document search and retrieval
- Document analysis and summarization
- Version control integration

**Capabilities**:
- ✅ Access SharePoint sites and libraries
- ✅ Search documents across SharePoint
- ✅ Read and analyze documents
- ✅ Create and update documents
- ✅ Version history access

**Use Cases**:
1. **Document Access**: Elena reads SharePoint documents
2. **Knowledge Base**: Search enterprise documents
3. **Documentation**: Sage creates docs in SharePoint
4. **Compliance**: Access controlled documents

#### 4. **BizChat Integration**

**What It Is**:
- Business chat interface
- Unified communication platform
- Cross-platform messaging

**Capabilities**:
- ✅ Unified chat interface
- ✅ Cross-platform access
- ✅ Business-focused features

---

## Integration Architecture

### Current Architecture

```
┌─────────────┐
│   Engram    │
│  Frontend   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Engram API │
│  (FastAPI)  │
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│   Foundry   │   │  Microsoft  │
│   Agent     │───┤    Graph    │
│   Service   │   │     API     │
└─────────────┘   └─────────────┘
```

### Proposed Architecture with M365 Integration

```
┌─────────────────┐
│  Microsoft 365  │
│                 │
│  ┌───────────┐ │
│  │  Teams    │ │
│  │   Bot     │ │
│  └─────┬─────┘ │
│        │       │
│  ┌─────▼─────┐ │
│  │  Outlook  │ │
│  │   Add-in  │ │
│  └─────┬─────┘ │
│        │       │
│  ┌─────▼─────┐ │
│  │ SharePoint│ │
│  │ Connector │ │
│  └─────┬─────┘ │
└────────┼───────┘
         │
         ▼
┌─────────────────┐
│  Azure AI       │
│  Foundry        │
│                 │
│  ┌───────────┐ │
│  │  Elena    │ │
│  │  Agent    │ │
│  └─────┬─────┘ │
└────────┼───────┘
         │
         ▼
┌─────────────────┐
│  Engram Tools   │
│  API            │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Microsoft      │
│  Graph API      │
└─────────────────┘
```

---

## Implementation Plan

### Phase 1: Teams Bot Integration (Week 1-2)

#### Step 1: Create Teams Bot in Foundry

**Tasks**:
1. Configure Elena agent for Teams
2. Set up Teams bot registration
3. Configure authentication
4. Test basic Teams interaction

**Configuration**:
```json
{
  "agent": {
    "id": "elena",
    "name": "Dr. Elena Vasquez",
    "description": "Business Analyst Assistant"
  },
  "teams": {
    "enabled": true,
    "bot_id": "elena-teams-bot",
    "app_id": "<teams-app-id>",
    "scopes": ["chat", "channel", "team"]
  },
  "authentication": {
    "type": "entra_id",
    "tenant_id": "<tenant-id>",
    "client_id": "<client-id>"
  }
}
```

#### Step 2: Integrate with Engram Tools

**Tasks**:
1. Ensure tool endpoints are accessible from Teams
2. Configure CORS for Teams requests
3. Test tool execution from Teams
4. Handle Teams-specific message formatting

**Implementation**:
```python
# backend/api/routers/teams.py
@router.post("/teams/messages")
async def handle_teams_message(
    request: TeamsMessageRequest,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Handle incoming Teams message.
    """
    # Route to Elena agent
    response = await agent_router.route_and_execute(
        query=request.text,
        context=create_context_from_teams(request, user),
        agent_id="elena"
    )
    
    # Format response for Teams
    return format_teams_response(response)
```

#### Step 3: Teams-Specific Features

**Tasks**:
1. Implement adaptive cards for rich responses
2. Handle Teams mentions and reactions
3. Support channel vs. chat contexts
4. Implement Teams file sharing

**Example Adaptive Card**:
```json
{
  "type": "AdaptiveCard",
  "version": "1.4",
  "body": [
    {
      "type": "TextBlock",
      "text": "Requirements Analysis Complete",
      "weight": "Bolder",
      "size": "Medium"
    },
    {
      "type": "FactSet",
      "facts": [
        {
          "title": "Stakeholders:",
          "value": "5 identified"
        },
        {
          "title": "Requirements:",
          "value": "12 documented"
        }
      ]
    }
  ],
  "actions": [
    {
      "type": "Action.OpenUrl",
      "title": "View Details",
      "url": "https://engram.work/projects/123"
    }
  ]
}
```

### Phase 2: Outlook Add-in (Week 2-3)

#### Step 1: Create Outlook Add-in

**Tasks**:
1. Create Outlook add-in manifest
2. Register add-in in Microsoft 365
3. Configure add-in permissions
4. Test basic add-in loading

**Manifest Structure**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp>
  <Id>engram-outlook-addin</Id>
  <Version>1.0.0</Version>
  <ProviderName>Engram</ProviderName>
  <DefaultLocale>en-US</DefaultLocale>
  <DisplayName DefaultValue="Engram AI Assistant" />
  <Description DefaultValue="AI-powered email assistance with Elena" />
  <IconUrl DefaultValue="https://engram.work/assets/icon.png" />
  <HighResolutionIconUrl DefaultValue="https://engram.work/assets/icon-128.png" />
  <SupportUrl DefaultValue="https://engram.work/support" />
  
  <Hosts>
    <Host Name="Mailbox" />
  </Hosts>
  
  <Requirements>
    <Sets>
      <Set Name="Mailbox" MinVersion="1.1" />
    </Sets>
  </Requirements>
  
  <FormSettings>
    <Form xsi:type="ItemRead">
      <DesktopSettings>
        <SourceLocation DefaultValue="https://engram.work/outlook/read.html" />
      </DesktopSettings>
    </Form>
    <Form xsi:type="ItemEdit">
      <DesktopSettings>
        <SourceLocation DefaultValue="https://engram.work/outlook/compose.html" />
      </DesktopSettings>
    </Form>
  </FormSettings>
  
  <Permissions>ReadWriteItem</Permissions>
  <Rule xsi:type="RuleCollection" Mode="Or">
    <Rule xsi:type="ItemIs" ItemType="Message" FormType="Read" />
    <Rule xsi:type="ItemIs" ItemType="Message" FormType="Edit" />
  </Rule>
</OfficeApp>
```

#### Step 2: Implement Add-in Features

**Tasks**:
1. Email composition assistance
2. Email analysis and summarization
3. Smart reply suggestions
4. Meeting scheduling integration

**Implementation**:
```javascript
// frontend/outlook/compose.js
Office.onReady((info) => {
  if (info.host === Office.HostType.Outlook) {
    document.getElementById("compose-button").onclick = composeEmail;
    document.getElementById("analyze-button").onclick = analyzeEmail;
  }
});

async function composeEmail() {
  const subject = await Office.context.mailbox.item.subject.getAsync();
  const body = await Office.context.mailbox.item.body.getAsync();
  
  // Call Engram API for email composition
  const response = await fetch('https://engram.work/api/v1/outlook/compose', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAccessToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      subject: subject.value,
      body: body.value,
      context: await getEmailContext()
    })
  });
  
  const suggestion = await response.json();
  
  // Insert suggestion into email body
  await Office.context.mailbox.item.body.setAsync(
    suggestion.composed_email,
    { coercionType: Office.CoercionType.Html }
  );
}
```

#### Step 3: Backend API for Outlook

**Tasks**:
1. Create Outlook-specific endpoints
2. Handle email context extraction
3. Implement email composition logic
4. Support email analysis

**Implementation**:
```python
# backend/api/routers/outlook.py
@router.post("/outlook/compose")
async def compose_email(
    request: OutlookComposeRequest,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Compose email with Elena's assistance.
    """
    # Get email context
    context = await extract_email_context(request)
    
    # Route to Elena for email composition
    response = await agent_router.route_and_execute(
        query=f"Help me compose an email: {request.prompt}",
        context=context,
        agent_id="elena"
    )
    
    # Format as email
    composed_email = format_email_response(response, request)
    
    return {"composed_email": composed_email}

@router.post("/outlook/analyze")
async def analyze_email(
    request: OutlookAnalyzeRequest,
    user: SecurityContext = Depends(get_current_user)
):
    """
    Analyze email content with Elena.
    """
    # Extract email content
    email_content = await extract_email_content(request.email_id)
    
    # Analyze with Elena
    analysis = await agent_router.route_and_execute(
        query=f"Analyze this email: {email_content}",
        context=create_context(user),
        agent_id="elena"
    )
    
    return {"analysis": analysis}
```

### Phase 3: SharePoint Integration (Week 3-4)

#### Step 1: Configure SharePoint Connector

**Tasks**:
1. Set up SharePoint connector in Foundry
2. Configure site access
3. Set up document indexing
4. Test document access

**Configuration**:
```json
{
  "sharepoint": {
    "enabled": true,
    "sites": [
      {
        "site_url": "https://zimax.sharepoint.com/sites/engram",
        "libraries": ["Documents", "Shared Documents"],
        "permissions": "read_write"
      }
    ],
    "indexing": {
      "enabled": true,
      "auto_index": true,
      "file_types": [".docx", ".pdf", ".xlsx", ".pptx"]
    }
  }
}
```

#### Step 2: Document Access Tools

**Tasks**:
1. Create SharePoint document access tools
2. Implement document search
3. Support document reading and analysis
4. Enable document creation

**Implementation**:
```python
# backend/agents/tools/sharepoint.py
@tool
async def search_sharepoint_documents(
    query: str,
    site_url: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Search SharePoint documents.
    """
    # Use Foundry SharePoint connector
    results = await foundry_client.search_sharepoint(
        query=query,
        site_url=site_url,
        limit=limit
    )
    
    return format_document_results(results)

@tool
async def read_sharepoint_document(
    document_url: str
) -> str:
    """
    Read and analyze SharePoint document.
    """
    # Access document via Foundry
    document = await foundry_client.get_sharepoint_document(document_url)
    
    # Analyze with Elena
    analysis = await analyze_document(document)
    
    return analysis
```

---

## Benefits

### ✅ Enhanced User Experience
- **Native Integration**: Agents available where users work
- **Context Awareness**: Access to Teams conversations and emails
- **Seamless Workflow**: No need to switch applications
- **Familiar Interface**: Users stay in Microsoft 365

### ✅ Increased Adoption
- **Lower Barrier**: No separate application to learn
- **Convenience**: Agents available in daily tools
- **Visibility**: Agents visible to entire organization
- **Accessibility**: Available on all Microsoft 365 platforms

### ✅ Expanded Capabilities
- **Teams Collaboration**: Agents participate in team discussions
- **Email Assistance**: Help with email composition and analysis
- **Document Access**: Direct access to SharePoint documents
- **Unified Experience**: Single agent across all M365 apps

### ✅ Operational Benefits
- **Simplified Authentication**: Uses existing M365 credentials
- **Reduced Maintenance**: Foundry manages integration
- **Better Observability**: M365-native logging and monitoring
- **Scalability**: Foundry handles infrastructure

---

## Challenges & Considerations

### ⚠️ Authentication & Permissions
- **Consent**: Users must consent to agent access
- **Permissions**: Need appropriate M365 permissions
- **Multi-Tenant**: Handle multiple tenant scenarios
- **Security**: Ensure secure access to sensitive data

### ⚠️ User Experience
- **Context Switching**: Agents need to understand M365 context
- **Message Formatting**: Different formats for Teams vs. Outlook
- **Error Handling**: Graceful handling of M365 API errors
- **Performance**: Ensure fast response times in M365

### ⚠️ Integration Complexity
- **Multiple Platforms**: Teams, Outlook, SharePoint each have different APIs
- **State Management**: Maintain context across M365 apps
- **Synchronization**: Keep Engram and M365 in sync
- **Testing**: Test across different M365 environments

---

## Success Metrics

### Adoption
- ✅ Teams bot active users
- ✅ Outlook add-in usage rate
- ✅ SharePoint document access frequency
- ✅ User engagement metrics

### Quality
- ✅ Response accuracy in M365 context
- ✅ User satisfaction scores
- ✅ Error rate < 2%
- ✅ Average response time < 3 seconds

### Business Impact
- ✅ Time saved on email composition
- ✅ Improved collaboration in Teams
- ✅ Faster document access
- ✅ Increased productivity

---

## Next Steps

### Immediate (This Week)
1. ✅ Complete research (this document)
2. 🔄 Review with team
3. 🔄 Prioritize integration order

### Short Term (Next 2 Weeks)
1. Create Teams bot in Foundry
2. Test basic Teams interaction
3. Design Outlook add-in
4. Plan SharePoint integration

### Medium Term (Next Month)
1. Implement Teams bot
2. Create Outlook add-in
3. Configure SharePoint connector
4. Test end-to-end workflows
5. Gather user feedback

---

## Related Documentation

- [Foundry Features Roadmap](./foundry-features-roadmap.md)
- [Foundry Additional Features](./foundry-additional-features.md)
- [Elena Foundry Migration](./elena-foundry-migration-complete.md)
- [Microsoft Graph Integration](../05-knowledge-base/elena/persona.md)

---

## References

- [Microsoft Teams Bot Framework](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/create-a-bot-for-teams)
- [Outlook Add-ins](https://learn.microsoft.com/en-us/office/dev/add-ins/outlook/)
- [SharePoint Connectors](https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/sharepoint-add-ins)
- [Azure AI Foundry M365 Integration](https://learn.microsoft.com/en-us/azure/ai-foundry)

---

*Last Updated: January 2026*

