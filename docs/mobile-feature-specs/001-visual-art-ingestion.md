# Mobile Feature Spec: Visual Art Ingestion

## 1. Overview

This feature enables mobile users to use their device camera to capture visual art (e.g., welded metal art, landscapes, physical objects). This visual input serves as a creative prompt to:

1. Inspire a Story.
2. Drive the generation of a complementary visual by Sage Meridian.

This is a **creative** ingestion flow, distinct from document scanning.

## 2. User Workflow

1. **Open Camera**: User accesses the "Visual Capture" mode in the mobile app.
2. **Capture**: User takes a photo of an artistic subject (e.g., a welded metal sculpture).
3. **Ingest**: The app uploads the image to the Engram system.
4. **System Action**:
    * The image is analyzed.
    * A story is generated based on the visual input.
    * **Sage Meridian** generates a new, related visual response.
    * Both the original image, the story, and Sage's response are saved to the current Session.

## 3. Technical Implementation

### 3.1 Mobile Client

- **Camera Interface**: Standard system camera integration.
* **Upload Endpoint**: `POST /api/v1/ingest/visual` (Multipart/form-data).
* **Payload**:
  * `image`: The captured image file.
  * `context`: (Optional) User's voice note or text caption.
  * `session_id`: Current active session.

### 3.2 Backend Processing

1. **Storage**:
    * Save original image to Blob Storage (e.g., `uploads/{session_id}/{timestamp}_original.jpg`).
2. **Visual Analysis**:
    * Use a Vision-Language Model (VLM) (e.g., Gemini Vision) to describe the image in rich detail.
3. **Story Generation**:
    * Feed the image description into the Story Engine.
    * Generate a short narrative or reflection.
4. **Sage Meridian Integration**:
    * Pass the image description and story context to Sage Meridian.
    * Sage prompts the image generator (Nano Banana Pro) to create a *complementary* visual (a "visual reply").
5. **Persistence**:
    * Save Original Image URL, Image Description, Generated Story, and Sage's Image URL to the **Memory System** (Zep) associated with the `session_id`.

## 4. Requirements

- **Performance**: Fast upload and asynchronous processing (user shouldn't wait for generation to finish to continue).
* **Quality**: High-resolution image capture.
* **Feedback**: Push notification or UI update when Sage's response is ready.
