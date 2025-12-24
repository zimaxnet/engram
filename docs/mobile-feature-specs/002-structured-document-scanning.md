# Mobile Feature Spec: Structured Document Scanning

## 1. Overview

This feature allows mobile users to scan physical documents via the camera for the purpose of efficient data ingestion. Unlike the "Visual Art" flow, this is a **utilitarian** flow focused on extracting structured information from text-heavy documents to populate the Knowledge Graph.

## 2. User Workflow

1. **Open Scanner**: User accesses the "Document Scanner" mode in the mobile app.
2. **Scan**: User positions camera over a document.
    - *UI Feature*: Edge detection guide overlays to assist regular cropping.
3. **Review**: User reviews the scan clarity and crops if necessary.
4. **Ingest**: User confirms upload.
5. **System Action**:
    - The document is processed by the "Structured" service.
    - Content is converted to structured JSON.
    - Data is ingested into the system's Memory (Zep).

## 3. Technical Implementation

### 3.1 Mobile Client

- **Scanner Interface**: Use platform-native document scanning APIs (e.g., VisionKit on iOS, ML Kit on Android) for:
  - Edge detection.
  - Perspective correction.
  - Auto-cropping.
- **Upload Endpoint**: `POST /api/v1/ingest/document` (Multipart/form-data).
- **Payload**:
  - `file`: The processed PDF or high-contrast image.
  - `session_id`: Current active session.

### 3.2 Backend Processing

1. **Storage**:
    - Save raw scan to Blob Storage.
2. **Structured Extraction**:
    - Send file to **Structured** (unstructured.io or internal equivalent service).
    - **Goal**: Extract hierarchy, tables, and key-value pairs into normalized JSON.
3. **Ingestion**:
    - Parse the returned JSON.
    - Chunk text based on document structure (headers, sections).
    - Embed chunks and upsert into **Zep Memory** and/or **Graph Database**.
4. **Metadata**:
    - Tag entry with `source_type: scanned_document`.

## 4. Requirements

- **Accuracy**: High-quality OCR and structure recognition.
- **Format**: Output must be machine-readable JSON, not just plain text blocks.
- **Searchability**: The ingested content must be immediately searchable by Agents (Elena/Marcus) within the session context.
