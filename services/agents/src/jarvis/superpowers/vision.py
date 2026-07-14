"""
JARVIS Vision Engine - Document & Image Analysis
Handles OCR, image analysis, document parsing, and visual intelligence.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger("jarvis.vision")


class VisionEngine:
    """JARVIS vision superpower - see and understand the world."""

    def __init__(self, config):
        self.config = config
        self._ocr_model = None
        self._vision_model = None

    async def initialize(self) -> None:
        """Initialize vision models."""
        try:
            # Try to load PaddleOCR for document analysis
            from paddleocr import PaddleOCR
            self._ocr_model = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            logger.info("[VisionEngine] PaddleOCR loaded.")
        except ImportError:
            logger.warning("[VisionEngine] PaddleOCR not available.")
        
        logger.info("[VisionEngine] Initialized.")

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Process vision-related queries."""
        lower_query = query.lower()
        
        # OCR extraction
        if "ocr" in lower_query or "extract text" in lower_query or "read document" in lower_query:
            image_path = context.get("image_path") if context else None
            if image_path:
                text = await self.extract_text(image_path)
                return f"Extracted Text:\n```\n{text}\n```"
            return "No image/document provided for OCR."
        
        # Image analysis
        if "analyze image" in lower_query or "look at" in lower_query:
            image_path = context.get("image_path") if context else None
            if image_path:
                analysis = await self.analyze_image(image_path, query)
                return analysis
            return "No image provided for analysis."
        
        # Screenshot analysis
        if "screenshot" in lower_query:
            return await self.capture_screenshot()
        
        return "Vision engine ready. Provide an image or document to analyze."

    async def extract_text(self, file_path: str) -> str:
        """Extract text from image/document using OCR."""
        if self._ocr_model:
            result = self._ocr_model.ocr(file_path, cls=True)
            texts = []
            for line in result[0]:
                if line:
                    texts.append(line[1][0])
            return "\n".join(texts)
        return "OCR model not available."

    async def analyze_image(self, image_path: str, query: str) -> str:
        """Analyze image content using vision model."""
        # Use OpenAI vision API if available
        if self.config.api_key:
            try:
                import base64
                with open(image_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode()
                
                from openai import OpenAI
                client = OpenAI(api_key=self.config.api_key)
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": query},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                                }
                            ]
                        }
                    ],
                    max_tokens=1000,
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"Vision analysis error: {e}"
        
        return "Vision API not configured."

    async def capture_screenshot(self) -> str:
        """Capture and analyze screen."""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save("/tmp/jarvis_screenshot.png")
            return await self.analyze_image("/tmp/jarvis_screenshot.png", "Describe what's on this screen.")
        except Exception as e:
            return f"Screenshot capture failed: {e}"

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream vision analysis."""
        result = await self.process(query, session_id, context)
        yield result

    async def shutdown(self) -> None:
        """Cleanup vision resources."""
        self._ocr_model = None
        self._vision_model = None
