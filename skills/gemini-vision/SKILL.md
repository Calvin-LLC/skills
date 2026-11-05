---
name: gemini-vision
description: >
  Thorough visual inspection and review of UI screenshots, mockups, diagrams, and wireframes.
  Labels UI components, verifies layout hierarchy and alignment, audits readability, and
  diagnoses visual bugs with deterministic contrast checks.
license: MIT
---

# Visual inspection and review (`gemini-vision`)

Inspect rendered interfaces, mockups, and wireframes with a multimodal vision model. Use when auditing visual hierarchy, confirming UI bug fixes, reading complex diagrams, or transcribing wireframes.

## Workflow

1. **Capture or locate image**:
   - Web application: capture a full-page or element screenshot using headless browser automation (`browser-use`, `playwright`, or native agent screenshot tool).
   - Local mockup / wireframe / diagram: use the local file path.

2. **Inspect and label**:
   ```bash
   node <skill-dir>/review.mjs <image-path>
   ```

   To use a custom prompt, model, or OpenAI-compatible endpoint:
   ```bash
   node <skill-dir>/review.mjs <image-path> --prompt "Label all buttons, inputs, and form sections in this mockup" --model "gemini-2.5-flash"
   ```

3. **Verify contrast deterministically**:
   Vision models approximate; never trust raw color numbers from a model. If the inspection flags potential contrast issues, test the hex pair directly:
   ```bash
   node <skill-dir>/wcag.mjs "#FOREGROUND" "#BACKGROUND"
   ```

4. **Iterate**:
   Make code changes, re-capture the screenshot, and run a second review to confirm resolution. Cap review cycles at two passes.

## Diagram and wireframe transcription

When analyzing photographed whiteboard wireframes or rough sketches:
- Ask specifically for component bounds, text transcriptions, and visual hierarchy.
- Identify primary focal elements before inspecting secondary navigation.
- Flag any ambiguous gestures or handwritten text for human confirmation.
