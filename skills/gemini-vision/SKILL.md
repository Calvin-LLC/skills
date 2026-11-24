---
name: gemini-vision
description: "Use when inspecting or reviewing UI screenshots, mockups, diagrams, or wireframes for layout, hierarchy, readability, or visual bugs. Not for pixel or color analysis of camera or capture images, nor for routine text edits."
license: MIT
---

# Visual inspection and review (`gemini-vision`)

Inspect rendered interfaces, mockups, and wireframes with a multimodal vision model. The skill is not tied to Gemini: `review.mjs` works with any vision model behind an OpenAI-compatible endpoint (OpenAI, Gemini, a gateway, a local model). Use when auditing visual hierarchy, confirming UI bug fixes, reading complex diagrams, or transcribing wireframes. For pixel or color analysis of camera or capture images, read the image directly or script it instead.

## Workflow

1. **Capture or locate image**:
   - Web application: capture a full-page or element screenshot with a headless-browser or screenshot tool.
   - Local mockup / wireframe / diagram: use the local file path.

2. **Inspect and label**:
   ```bash
   node <skill-dir>/review.mjs <image-path> --model <vision-model>
   ```

   To use a custom prompt or endpoint:
   ```bash
   node <skill-dir>/review.mjs <image-path> --prompt "Label all buttons, inputs, and form sections in this mockup" --base <openai-compatible-base-url> --model <vision-model>
   ```

   `review.mjs` needs Node 18 or newer. It reads settings from flags, then the environment, then `.env` in the working directory, then `.config/vision/env` under the home directory. It picks the endpoint and its key as a pair, so a key only goes to its own host. The first row that applies wins:

   | Configured | Requests go to |
   |---|---|
   | `--base` or `VISION_BASE_URL`, with `VISION_API_KEY` (a localhost endpoint needs no key) | that base URL |
   | `OPENAI_API_KEY` | `OPENAI_BASE_URL` if set, else `https://api.openai.com/v1` |
   | `GEMINI_API_KEY` | `https://generativelanguage.googleapis.com/v1beta/openai` |

   The model has no default, because model names go stale: pass `--model` or set `VISION_MODEL` to a vision-capable model on that endpoint. If no key or no model is configured, stop and ask the user. Do not invent review results. Set variables for one run like this:
   ```
   POSIX:                VISION_API_KEY=<key> VISION_BASE_URL=<base-url> VISION_MODEL=<model> node <skill-dir>/review.mjs <image-path>
   Windows (PowerShell): $env:VISION_API_KEY='<key>'; $env:VISION_BASE_URL='<base-url>'; $env:VISION_MODEL='<model>'; node <skill-dir>/review.mjs <image-path>
   ```

3. **Verify contrast deterministically**:
   Vision models approximate; never trust raw color numbers from a model. If the inspection flags potential contrast issues, test the hex pair directly:
   ```bash
   node <skill-dir>/wcag.mjs "#FOREGROUND" "#BACKGROUND"
   ```

4. **Iterate**:
   Make code changes, re-capture the screenshot, and run a second review to confirm resolution. Cap review cycles at two passes. If the second pass still fails, report what remains to the user.

## Diagram and wireframe transcription

When analyzing photographed whiteboard wireframes or rough sketches:
- Ask specifically for component bounds, text transcriptions, and visual hierarchy.
- Identify primary focal elements before inspecting secondary navigation.
- Flag any ambiguous gestures or handwritten text for human confirmation.
