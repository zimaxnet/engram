---
layout: default
title: "Enablement Report: Sage Visual Storytelling & Delegation"
parent: "Feature Specs"
---

# Enablement Report: Sage Visual Storytelling & Delegation

**Date:** December 29, 2025
**Status:** Implementation Complete / Verification Pending (Deployment)
**Author:** Antigravity (Agent)

## 1. Executive Summary

We have successfully implemented the ability for **Elena** (System Guide) to delegate visual storytelling tasks to **Sage** (Creative Agent). This feature leverages a durable Temporal workflow to generate a narrative (Claude), an architecture diagram (Gemini), and a visualization (Gemini/Imagen), saving all artifacts to Azure Files and enriching Zep memory.

## 2. Architecture

### Workflow (`StoryWorkflow`)

The process is orchestrated by `backend/workflows/story_workflow.py`, ensuring durability and retries.

1. **Generate Story**: Claude 3.5 Sonnet generates the narrative.
2. **Generate Visuals**:
    * **Diagram**: Gemini Pro 1.5 generates a JSON graph specification.
    * **Image**: Gemini/Imagen generates a PNG visualization.
3. **Save Artifacts**: Saves `.md`, `.json`, and `.png` files to `/app/docs` (mounted Azure File Share).
4. **Enrich Memory**: Ingests the story content and metadata into Zep for future recall.

### Delegation Flow

1. User asks Elena: *"Create a visual story..."*
2. Elena interprets request and calls `delegate_to_sage` tool.
3. Tool triggers `StoryWorkflow` via Temporal Client.
4. Tool constructs response with Story ID, snippet, and **inline image**.

## 3. Findings & Challenges

### 3.1 Zep User Management & Workflow Crashes

**Issue:** The workflow consistently failed at the final step ("Enrich Memory") with a `Zep API error: 400 - user does not exist`. This unhandled exception caused the Temporal Activity to fail, and in some cases, appeared to crash the worker process before the image file could be reliably synced/flushed to the `docs` volume.
**Finding:** The deployed version of Zep (Community/OSS) likely does not support dynamic user creation via the `/api/v1/users` endpoint, or requires strict prerequisite setup not present in our staging environment.
**Fix:** We modified `ZepMemoryClient.get_or_create_session` to automatically detect the "user does not exist" error. The client now logs a warning and **retries the session creation with `user_id=None`** (anonymous/system context). This ensures the workflow completes successfully even if the specific user profile (`elena-delegate`) is missing.

### 3.2 Visual Artifact Persistence

**Issue:** Although logs confirmed image generation (`941KB`), the file was missing from `docs/images/`.
**Finding:** The sequence of events (Image Generated -> Worker Crash due to Zep Error) suggests that the file write operation was either interrupted or the worker container terminated before the filesystem sync could complete. By fixing the root cause of the crash (the Zep error), we ensure the worker remains healthy to complete the file operations.

### 3.3 UX Feedback Loop

**Issue:** Initially, the user had to click a link to view the story/image.
**Fix:** We updated the `delegate_to_sage` tool in `backend/agents/elena/agent.py` to check for successful workflow completion and **append an inline Markdown image** (`![Visual](/api/v1/images/{id}.png)`) to the chat response. This provides immediate visual confirmation to the user.

## 4. Verification Plan (Pending Deployment)

We are currently awaiting the deployment of **Worker Revision > 0000046** and **API Revision**.
Once live, we will verify:

1. **End-to-End Success**: Workflow completes without Zep errors.
2. **Image Persistence**: `/api/v1/images/{story_id}.png` returns a valid image.
3. **Chat UI**: The image appears inline in the chat.
4. **Story Page**: The "Visual" tab displays the generated image.

## 5. Future Recommendations

- **Monitoring**: Add specific alerts for "Task not found" or worker crashes to identify infrastructure instability sooner.
* **Zep Enterprise**: Evaluate upgrading to Zep Enterprise if multi-user ephemeral context is a strict requirement.
