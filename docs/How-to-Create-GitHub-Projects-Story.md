# How to Create GitHub Projects Story via Agent Delegation

## Overview

The story about GitHub Projects Integration should be created by **delegating to Sage** through either **Elena** (Business Analyst) or **Marcus** (Project Manager) agents. This follows the proper agent workflow pattern where agents coordinate and delegate tasks.

## Method: Agent Delegation

### Via Elena (Business Analyst)

**Recommended for:** Requirements-focused stories, documentation narratives

**Steps:**
1. Open the Engram chat interface
2. Select **Elena** as your agent
3. Send this message:

```
Elena, please delegate to Sage to create a comprehensive story about GitHub Projects Integration for the Engram Context Engine. The story should cover:

1. How GitHub Projects applies to each of the seven layers of agentic AI systems
2. The progress tracking mechanism and task lifecycle  
3. Agent capabilities and workflows (Elena, Marcus, Sage)
4. System awareness of progress through recursive self-awareness
5. Benefits for agents, system, and users

The story should be engaging, technical but accessible, and highlight how agents track their own work. Please include an architecture diagram and visual.
```

**What happens:**
- Elena will use her `delegate_to_sage` tool
- This triggers a Temporal workflow (`StoryWorkflow`)
- Sage generates the story with Claude
- Sage creates an architecture diagram with Gemini
- Sage generates a visual representation
- All artifacts are saved to `docs/stories/` folder
- Story and visual are automatically ingested into Zep memory
- You'll receive a story ID and link to view it

### Via Marcus (Project Manager)

**Recommended for:** Project management narratives, timeline-focused stories

**Steps:**
1. Open the Engram chat interface
2. Select **Marcus** as your agent
3. Send this message:

```
Marcus, please delegate to Sage to create a story about our GitHub Projects integration. I need a comprehensive narrative that explains how we're tracking the Production-Grade Agentic System implementation across all seven layers. Include details about progress tracking, agent workflows, and system awareness. Make it engaging and include visuals.
```

**What happens:**
- Marcus will use his `delegate_to_sage` tool
- Same workflow as above - Temporal `StoryWorkflow` execution
- Story, diagram, and visual generated
- Artifacts saved and ingested into memory

## Why Agent Delegation?

### Benefits

1. **Proper Workflow**: Follows the established agent coordination pattern
2. **Context Awareness**: Agents have full context of the project and can provide better instructions to Sage
3. **Memory Integration**: The delegation conversation itself is stored in memory
4. **Traceability**: Full workflow trace in Temporal for observability
5. **Recursive Self-Awareness**: Agents are aware they're delegating and can track the result

### Agent Roles

- **Elena**: Best for requirements-focused, compliance-oriented stories
- **Marcus**: Best for project management, timeline, and execution-focused narratives
- **Sage**: Receives delegation and creates the actual story/visual artifacts

## Expected Output

When delegation is successful, you'll receive:

```
✅ Delegated to Sage. He has created:

**Story ID**: story-abc123def456

[Story preview text...]

[View Full Story & Visual](/stories/story-abc123def456)
```

## Artifacts Created

1. **Story Markdown**: `docs/stories/{story_id}.md`
   - Full narrative about GitHub Projects integration
   - Covers all seven layers
   - Includes progress tracking details

2. **Architecture Diagram**: `docs/stories/{story_id}-diagram.json`
   - Nano Banana Pro diagram specification
   - Shows integration architecture
   - Visual representation of seven layers

3. **Visual Image**: `docs/stories/{story_id}-visual.png`
   - Generated visual representation
   - Complements the story narrative

4. **Memory Ingestion**: 
   - Story content stored in Zep memory
   - Session ID: `sess-story-{story_id}`
   - Available for future agent queries

## Verification

After delegation, verify the story was created:

1. **Check Story Files**:
   ```bash
   ls -la docs/stories/ | grep github-projects
   ```

2. **View in Frontend**:
   - Navigate to `/stories/{story_id}` in the Engram UI

3. **Query Memory**:
   - Ask an agent: "What story did Sage create about GitHub Projects?"
   - Agent will search Zep memory and retrieve the story

4. **Check Temporal Workflow**:
   - View workflow in Temporal UI
   - Check workflow status and progress

## Troubleshooting

### Agent Doesn't Delegate

**Issue**: Agent responds but doesn't use `delegate_to_sage` tool

**Solution**: 
- Be more explicit: "Please use your delegate_to_sage tool to..."
- Or: "Delegate this storytelling task to Sage Meridian"

### Workflow Fails

**Issue**: Delegation succeeds but workflow fails

**Solution**:
- Check Temporal worker is running in Azure
- Verify Claude and Gemini API keys are configured
- Check Temporal workflow logs

### Story Not Ingested

**Issue**: Story created but not in memory

**Solution**:
- Story workflow automatically ingests - check Zep logs
- Verify Zep service is running
- Check memory session was created

## Alternative: Direct API Call

If you need to create the story programmatically (not recommended for normal use):

```bash
# Set endpoint
export ENGRAM_API_URL=https://your-endpoint.azurecontainerapps.io

# Call API
curl -X POST "$ENGRAM_API_URL/api/v1/story/create" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "topic": "GitHub Projects Integration for Engram Context Engine",
    "context": "...",
    "include_diagram": true,
    "diagram_type": "architecture"
  }'
```

**Note**: This bypasses agent coordination and doesn't create the delegation context in memory.

## Best Practice

**Always use agent delegation** for story creation. This ensures:
- Proper workflow orchestration
- Full observability
- Memory integration
- Agent awareness of the created artifacts

---

*Last Updated: December 20, 2024*

