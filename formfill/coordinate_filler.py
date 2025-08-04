#!/usr/bin/env python3
"""
Coordinate-based PDF form filler with real-time preview.

This module creates a visual overlay showing where text will be placed on a PDF,
then writes the text directly to the PDF at those coordinates.
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path
import fitz  # PyMuPDF

from anthropic import AsyncAnthropic
from anthropic.types.beta import BetaMessageParam

logger = logging.getLogger("coordinate_filler")


@dataclass
class TextPlacement:
    """Represents a text placement on the PDF."""
    field_name: str
    text: str
    x: int
    y: int
    width: int = 200
    height: int = 20
    font_size: int = 12
    confidence: float = 0.0


class CoordinateFiller:
    """Handles coordinate-based PDF form filling with real-time preview."""
    
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.placements: List[TextPlacement] = []
        self.current_image: Optional[Image.Image] = None
        self.pdf_path: Optional[str] = None
        
    async def analyze_form_fields(self, pdf_path: str, data: Dict[str, str]) -> List[TextPlacement]:
        """
        Analyze PDF form and determine optimal text placements.
        
        Args:
            pdf_path: Path to the PDF file
            data: Dictionary of field names to values
            
        Returns:
            List of TextPlacement objects
        """
        self.pdf_path = pdf_path
        
        # Convert PDF to image
        images = convert_from_path(pdf_path, dpi=150)
        if not images:
            raise ValueError("Could not convert PDF to images")
            
        self.current_image = images[0]  # For now, handle first page only
        
        # Prepare data string for Claude
        data_str = ", ".join([f"{k}: {v}" for k, v in data.items()])
        
        # Ask Claude to identify form fields and their coordinates
        messages = [
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text",
                        "text": f"""I need to fill out this PDF form with the following data: {data_str}

Please analyze this form image and identify where each piece of data should be placed. For each form field you can identify, please provide:

1. The field name/label you see
2. The approximate coordinates (x, y) where text should be placed
3. The estimated width and height of the field
4. Which piece of my data should go in that field

Please format your response as a JSON array like this:
[
  {{
    "field_name": "First Name",
    "suggested_data": "John",
    "x": 150,
    "y": 200,
    "width": 200,
    "height": 25,
    "confidence": 0.9
  }}
]

Focus on identifying clear, fillable form fields. Be precise with coordinates."""
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": self._image_to_base64(self.current_image)
                        }
                    }
                ]
            }
        ]
        
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=messages
        )
        
        # Parse Claude's response
        response_text = response.content[0].text
        logger.info(f"Claude's field analysis: {response_text}")
        
        # Extract JSON from response
        try:
            # Find JSON array in response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON array found in response")
                
            json_str = response_text[start_idx:end_idx]
            field_data = json.loads(json_str)
            
            # Convert to TextPlacement objects
            placements = []
            for field in field_data:
                # Find matching data
                suggested_data = field.get('suggested_data', '')
                actual_data = self._match_data_to_field(field['field_name'], data, suggested_data)
                
                placement = TextPlacement(
                    field_name=field['field_name'],
                    text=actual_data,
                    x=field['x'],
                    y=field['y'],
                    width=field.get('width', 200),
                    height=field.get('height', 25),
                    confidence=field.get('confidence', 0.5)
                )
                placements.append(placement)
                
            self.placements = placements
            return placements
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse Claude's response: {e}")
            logger.error(f"Response was: {response_text}")
            return []
    
    def _match_data_to_field(self, field_name: str, data: Dict[str, str], suggested: str) -> str:
        """Match form field to appropriate data."""
        field_lower = field_name.lower()
        
        # Try exact match first
        for key, value in data.items():
            if key.lower() in field_lower or field_lower in key.lower():
                return value
                
        # Try semantic matching
        name_fields = ['name', 'first', 'last', 'full']
        email_fields = ['email', 'mail']
        phone_fields = ['phone', 'tel', 'number']
        address_fields = ['address', 'street', 'addr']
        date_fields = ['date', 'birth', 'dob']
        
        for pattern in name_fields:
            if pattern in field_lower:
                for key, value in data.items():
                    if 'name' in key.lower():
                        return value
                        
        for pattern in email_fields:
            if pattern in field_lower:
                for key, value in data.items():
                    if 'email' in key.lower():
                        return value
                        
        for pattern in phone_fields:
            if pattern in field_lower:
                for key, value in data.items():
                    if 'phone' in key.lower():
                        return value
                        
        for pattern in address_fields:
            if pattern in field_lower:
                for key, value in data.items():
                    if 'address' in key.lower():
                        return value
                        
        for pattern in date_fields:
            if pattern in field_lower:
                for key, value in data.items():
                    if 'birth' in key.lower() or 'date' in key.lower():
                        return value
        
        # Return suggested data if no match found
        return suggested
    
    def create_preview_image(self, show_labels: bool = True) -> Image.Image:
        """
        Create a preview image showing where text will be placed.
        
        Args:
            show_labels: Whether to show field labels
            
        Returns:
            PIL Image with text placement overlay
        """
        if not self.current_image or not self.placements:
            return self.current_image or Image.new('RGB', (800, 600), 'white')
            
        # Create a copy of the original image
        preview = self.current_image.copy()
        draw = ImageDraw.Draw(preview)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
            label_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 10)
        except:
            font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        
        # Draw placements
        for i, placement in enumerate(self.placements):
            # Draw bounding box
            bbox = [
                placement.x, placement.y,
                placement.x + placement.width, placement.y + placement.height
            ]
            
            # Color based on confidence
            if placement.confidence > 0.8:
                color = (0, 255, 0, 128)  # Green for high confidence
            elif placement.confidence > 0.5:
                color = (255, 255, 0, 128)  # Yellow for medium confidence
            else:
                color = (255, 0, 0, 128)  # Red for low confidence
            
            # Draw semi-transparent rectangle
            overlay = Image.new('RGBA', preview.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(bbox, fill=color, outline=color[:3], width=2)
            preview = Image.alpha_composite(preview.convert('RGBA'), overlay).convert('RGB')
            
            # Draw text that will be placed
            draw = ImageDraw.Draw(preview)
            text_x = placement.x + 2
            text_y = placement.y + 2
            draw.text((text_x, text_y), placement.text, fill=(0, 0, 0), font=font)
            
            # Draw field label if requested
            if show_labels:
                label_text = f"{i+1}. {placement.field_name}"
                label_y = placement.y - 15 if placement.y > 15 else placement.y + placement.height + 2
                draw.text((placement.x, label_y), label_text, fill=(0, 0, 255), font=label_font)
        
        return preview
    
    def save_preview(self, output_path: str, show_labels: bool = True):
        """Save preview image to file."""
        preview = self.create_preview_image(show_labels)
        preview.save(output_path)
        logger.info(f"Preview saved to {output_path}")
    
    def write_to_pdf(self, output_path: str) -> str:
        """
        Write text directly to PDF at specified coordinates.
        
        Args:
            output_path: Path for output PDF
            
        Returns:
            Path to the created PDF
        """
        if not self.pdf_path or not self.placements:
            raise ValueError("No PDF or placements available")
            
        # Open PDF with PyMuPDF
        doc = fitz.open(self.pdf_path)
        page = doc[0]  # First page only for now
        
        for placement in self.placements:
            # Convert coordinates (PIL uses different coordinate system)
            point = fitz.Point(placement.x, placement.y + placement.font_size)
            
            # Insert text
            page.insert_text(
                point,
                placement.text,
                fontsize=placement.font_size,
                color=(0, 0, 0)  # Black text
            )
        
        # Save the modified PDF
        doc.save(output_path)
        doc.close()
        
        logger.info(f"Filled PDF saved to {output_path}")
        return output_path
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        import base64
        import io
        
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')
    
    def adjust_placement(self, index: int, x: int = None, y: int = None, 
                        width: int = None, height: int = None):
        """Manually adjust a text placement."""
        if 0 <= index < len(self.placements):
            placement = self.placements[index]
            if x is not None:
                placement.x = x
            if y is not None:
                placement.y = y
            if width is not None:
                placement.width = width
            if height is not None:
                placement.height = height
            logger.info(f"Adjusted placement {index}: {placement.field_name}")
    
    def remove_placement(self, index: int):
        """Remove a text placement."""
        if 0 <= index < len(self.placements):
            removed = self.placements.pop(index)
            logger.info(f"Removed placement: {removed.field_name}")
    
    def add_placement(self, field_name: str, text: str, x: int, y: int, 
                     width: int = 200, height: int = 25):
        """Manually add a text placement."""
        placement = TextPlacement(
            field_name=field_name,
            text=text,
            x=x,
            y=y,
            width=width,
            height=height,
            confidence=1.0  # Manual placements have full confidence
        )
        self.placements.append(placement)
        logger.info(f"Added placement: {field_name} at ({x}, {y})")


async def main():
    """Example usage of the CoordinateFiller."""
    import os
    
    # Example data
    sample_data = {
        "First Name": "Jane",
        "Last Name": "Doe", 
        "Email": "jane.doe@email.com",
        "Phone": "(555) 987-6543",
        "Address": "123 Main St, Apt 4B"
    }
    
    # Initialize filler
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return
        
    filler = CoordinateFiller(api_key)
    
    # Analyze form
    pdf_path = "examples/sample_form.pdf"
    if not Path(pdf_path).exists():
        print(f"Error: {pdf_path} not found")
        return
        
    print("🔍 Analyzing form fields...")
    placements = await filler.analyze_form_fields(pdf_path, sample_data)
    
    print(f"📍 Found {len(placements)} field placements:")
    for i, p in enumerate(placements):
        print(f"  {i+1}. {p.field_name}: '{p.text}' at ({p.x}, {p.y}) [confidence: {p.confidence:.2f}]")
    
    # Create preview
    print("🖼️  Creating preview...")
    filler.save_preview("form_preview.png")
    print("   Preview saved as 'form_preview.png'")
    
    # Write to PDF
    print("📄 Writing to PDF...")
    output_pdf = filler.write_to_pdf("sample_form_filled.pdf")
    print(f"   Filled PDF saved as '{output_pdf}'")


if __name__ == "__main__":
    asyncio.run(main())