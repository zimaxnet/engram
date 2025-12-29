# Standard Operating Procedure: Sage Visual & Memory Capabilities

## 1. Nano Banana Pro (Gemini 3) Image Generation

Sage uses the **Nano Banana Pro** model (technically `gemini-3-pro-image-preview`) for high-fidelity image generation. This capability is integrated into the `GeminiClient`.

### 1.1 Model Configuration

- **Model ID**: `gemini-3-pro-image-preview`
- **Provider**: Google Vertex AI / AI Studio (via `google-genai` Python SDK).
- **Billing**: Requires a paid billing account (Pay-as-you-go). Free tier may return `403 Permission Denied`.

### 1.2 Technical Implementation (Python)

The `GeminiClient` in `backend/llm/gemini_client.py` handles the interaction.

```python
from google import genai

# Correct usage pattern (no strict MIME type config for this model version)
client = genai.Client(api_key="PAID_TIER_KEY")
response = client.models.generate_content(
    model="gemini-3-pro-image-preview", 
    contents="Prompt here..."
)

# Extracting Image Data
for part in response.candidates[0].content.parts:
    if part.inline_data:
         image_bytes = part.inline_data.data
```

### 1.3 Usage in Workflows

The `StoryGenerationWorkflow` automatically invokes this capability:

1. **Story Generation**: Claude generates the narrative.
2. **Image Prompting**: The workflow extracts/generates a prompt from the story.
3. **Visual Generation**: `GeminiClient` is called to generate the image.
4. **Artifact Storage**: Image is saved to `docs/images/` and linked in the story metadata.

## 2. Memory Enrichment Protocol

Sage does not just "forget" after a session. All interactions are enriched and stored in **Zep Memory** to build a persistent context.

### 2.1 The Enrichment Pipeline

After a story or chat session completes, the `enrich_story_memory_activity` is triggered.

1. **Session Creation**: A Zep session is created/updated (e.g., `story-YYYYMMDD-topic`).
2. **Transcript Storage**: The full story text and metadata are stored as "messages" in Zep.
3. **Fact Extraction**: Zep automatically extracts entities and facts (Semantic Memory) from the text.
4. **Vector Indexing**: The content is embedded and indexed for hybrid search.

### 2.2 Agent Retrieval

Agents (Sage, Elena, Marcus) can retrieve this information via:

- **Episodic Recall**: "What story did I write regarding AI Agents?" -> Searches `sess-*` and `story-*` sessions.
- **Semantic Query**: "What are the limitations of Nano Banana Pro?" -> Queries the Knowledge Graph and Vector Database.
- **Context Injection**: Relevant memory is automatically injected into the agent's context window based on the user's current query.

## 3. Best Practices for Agents

- **Prompting for Images**: When generating prompts for Nano Banana Pro, focus on lighting, style (e.g., "cinematic", "photorealistic"), and composition. Avoid text-heavy descriptions.
- **Memory Queries**: When asking about past stories, be specific about the *topic* to trigger high-ranking semantic search results.
