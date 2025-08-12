"""
Image optimization utilities for email delivery.

This module provides image processing capabilities to optimize 
generated images for email attachments while maintaining quality.
"""

from __future__ import annotations

import os
import io
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class OptimizationResult:
    """Result of image optimization operation."""
    
    optimized_bytes: bytes
    original_size: int
    optimized_size: int
    original_dimensions: Tuple[int, int]
    optimized_dimensions: Tuple[int, int]
    compression_ratio: float


class EmailImageOptimizer:
    """Optimizes images for email delivery."""
    
    def __init__(self, 
                 target_width: int = 600,
                 max_file_size_kb: int = 500,
                 jpeg_quality: int = 85):
        """
        Initialize the image optimizer.
        
        Args:
            target_width: Target width for email images (default 600px)
            max_file_size_kb: Maximum file size in KB (default 500KB)
            jpeg_quality: JPEG compression quality 1-100 (default 85)
        """
        self.target_width = target_width
        self.max_file_size_kb = max_file_size_kb
        self.jpeg_quality = jpeg_quality
    
    def optimize_for_email(self, image_path: str) -> Optional[OptimizationResult]:
        """
        Optimize an image for email delivery.
        
        Args:
            image_path: Path to the image file to optimize
            
        Returns:
            OptimizationResult with optimized image data, or None if error
        """
        try:
            # Try to import PIL, fallback gracefully if not available
            try:
                from PIL import Image
            except ImportError:
                print("⚠️ PIL not available for image optimization. Using original image.")
                return self._fallback_to_original(image_path)
            
            # Correct the path if it has leading slash
            corrected_path = image_path.lstrip("/")
            
            if not os.path.exists(corrected_path):
                print(f"❌ Image file not found: {corrected_path}")
                return None
            
            # Load the image
            with Image.open(corrected_path) as img:
                original_size = os.path.getsize(corrected_path)
                original_dimensions = img.size
                
                # Calculate optimal dimensions
                optimized_dimensions = self._calculate_email_dimensions(img.size)
                
                # Resize if needed
                if optimized_dimensions != img.size:
                    img = img.resize(optimized_dimensions, Image.Resampling.LANCZOS)
                
                # Convert to RGB if needed (for JPEG)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save to bytes with JPEG compression
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG', quality=self.jpeg_quality, optimize=True)
                optimized_bytes = img_bytes.getvalue()
                
                # Calculate compression ratio
                optimized_size = len(optimized_bytes)
                compression_ratio = (original_size - optimized_size) / original_size
                
                return OptimizationResult(
                    optimized_bytes=optimized_bytes,
                    original_size=original_size,
                    optimized_size=optimized_size,
                    original_dimensions=original_dimensions,
                    optimized_dimensions=optimized_dimensions,
                    compression_ratio=compression_ratio
                )
                
        except Exception as e:
            print(f"❌ Image optimization failed: {e}")
            return self._fallback_to_original(image_path)
    
    def _calculate_email_dimensions(self, original_size: Tuple[int, int]) -> Tuple[int, int]:
        """
        Calculate optimal dimensions for email display.
        
        Args:
            original_size: (width, height) of original image
            
        Returns:
            (width, height) optimized for email
        """
        original_width, original_height = original_size
        
        # If already smaller than target, keep original
        if original_width <= self.target_width:
            return original_size
        
        # Calculate proportional height
        scale_factor = self.target_width / original_width
        new_height = int(original_height * scale_factor)
        
        return (self.target_width, new_height)
    
    def _fallback_to_original(self, image_path: str) -> Optional[OptimizationResult]:
        """
        Fallback to using original image if optimization fails.
        
        Args:
            image_path: Path to original image
            
        Returns:
            OptimizationResult with original image data
        """
        try:
            corrected_path = image_path.lstrip("/")
            
            if not os.path.exists(corrected_path):
                return None
            
            with open(corrected_path, 'rb') as f:
                original_bytes = f.read()
            
            # Get basic file info without PIL
            original_size = len(original_bytes)
            
            return OptimizationResult(
                optimized_bytes=original_bytes,
                original_size=original_size,
                optimized_size=original_size,
                original_dimensions=(0, 0),  # Unknown without PIL
                optimized_dimensions=(0, 0),
                compression_ratio=0.0
            )
            
        except Exception as e:
            print(f"❌ Fallback image loading failed: {e}")
            return None


def optimize_image_for_email(image_path: str, 
                           target_width: int = 600,
                           jpeg_quality: int = 85) -> Optional[OptimizationResult]:
    """
    Convenience function to optimize an image for email.
    
    Args:
        image_path: Path to image file
        target_width: Target width in pixels (default 600)
        jpeg_quality: JPEG quality 1-100 (default 85)
        
    Returns:
        OptimizationResult or None if failed
    """
    optimizer = EmailImageOptimizer(
        target_width=target_width,
        jpeg_quality=jpeg_quality
    )
    return optimizer.optimize_for_email(image_path)
