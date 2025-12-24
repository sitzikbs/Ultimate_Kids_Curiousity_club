# WP5: Image Service

**Status**: ⏳ Not Started  
**Dependencies**: WP1 (Foundation)  
**Estimated Effort**: 1-2 days  
**Owner**: TBD  
**Subsystem:** Audio Production (visual assets)

## 📋 Overview

Image Service handles **Show Blueprint images** (protagonist, world scenes, supporting characters) and episode artwork. For MVP, focuses on loading and managing existing images from Show Blueprint. Includes optional integration with image generation APIs (Flux, DALL-E) for future enhancement. Images used for Show Blueprint visualization in web dashboard, podcast album art, and potential YouTube thumbnails.

**Key Deliverables**:
- Image loading and validation from Show Blueprint paths
- Optional image generation via Flux/DALL-E/Mock
- Image resizing and format conversion
- Album art embedding support
- Character/world reference image management

**System Context**:
- **Subsystem:** Audio Production (visual assets)
- **Depends on:** WP1 (Foundation - Show Blueprint models with image_path)
- **Used by:** WP6 (Orchestrator), WP9 (Dashboard for image display)
- **Parallel Development:** ✅ Can develop in parallel with WP2, WP3, WP4 after WP1 complete

## 🎯 High-Level Tasks

### Task 5.1: Image Loading & Validation
Core image handling functionality.

**Subtasks**:
- [ ] 5.1.1: Create `ImageManager` class
- [ ] 5.1.2: Implement `load_image(path: Path) -> Image` using Pillow
- [ ] 5.1.3: Validate image format (PNG, JPG, WEBP)
- [ ] 5.1.4: Validate image dimensions (minimum 1400x1400 for podcast art)
- [ ] 5.1.5: Implement image resizing to standard sizes (1400x1400, 3000x3000)
- [ ] 5.1.6: Convert images to required formats (PNG for album art)

**Expected Outputs**:
- `src/services/image/manager.py`
- Image validation utilities

### Task 5.2: Provider Abstraction (Optional)
Prepare for future image generation capabilities.

**Subtasks**:
- [ ] 5.2.1: Create `BaseImageProvider` abstract base class
- [ ] 5.2.2: Implement `FluxProvider` (stub for future)
- [ ] 5.2.3: Implement `DALLEProvider` (stub for future)
- [ ] 5.2.4: Implement `MockImageProvider` (return placeholder images)
- [ ] 5.2.5: Create `ImageProviderFactory`

**Expected Outputs**:
- `src/services/image/base.py`
- `src/services/image/providers/` directory
- `src/services/image/factory.py`

### Task 5.3: Character Reference Images
Manage character artwork.

**Subtasks**:
- [ ] 5.3.1: Create character image templates (Oliver, Hannah)
- [ ] 5.3.2: Validate character images in character JSON loader
- [ ] 5.3.3: Generate placeholder images for characters without artwork
- [ ] 5.3.4: Support multiple image variants (profile, full-body, expressions)

**Expected Outputs**:
- `data/characters/images/oliver.png`
- `data/characters/images/hannah.png`
- Placeholder generation logic

### Task 5.4: Episode Artwork
Generate or load episode-specific artwork.

**Subtasks**:
- [ ] 5.4.1: Implement default podcast logo as fallback
- [ ] 5.4.2: Support custom episode artwork (user-provided)
- [ ] 5.4.3: Generate composite images (character + text overlay for topic)
- [ ] 5.4.4: Optimize images for podcast standards (1400x1400, <512KB)

**Expected Outputs**:
- `src/services/image/episode_artwork.py`
- Default podcast logo in `data/images/logo.png`

### Task 5.5: Image Composition (Optional)
Combine multiple images for episode thumbnails.

**Subtasks**:
- [ ] 5.5.1: Implement character layering (Oliver + Hannah side-by-side)
- [ ] 5.5.2: Add text overlays (episode title, topic)
- [ ] 5.5.3: Apply background templates
- [ ] 5.5.4: Export as PNG with transparency support

**Expected Outputs**:
- `src/services/image/compositor.py`
- Image composition utilities

### Task 5.6: Integration Testing
Validate image handling pipeline.

**Subtasks**:
- [ ] 5.6.1: Test image loading for all supported formats
- [ ] 5.6.2: Test image resizing maintains aspect ratio
- [ ] 5.6.3: Test album art embedding in MP3 files
- [ ] 5.6.4: Test placeholder generation for missing images

**Expected Outputs**:
- Integration test suite in `tests/test_image_integration.py`

## 🔧 Technical Specifications

### ImageManager Implementation
```python
from PIL import Image
from pathlib import Path

class ImageManager:
    PODCAST_ART_SIZE = (1400, 1400)
    YOUTUBE_THUMBNAIL_SIZE = (1280, 720)
    MAX_FILE_SIZE_KB = 512
    
    def load_image(self, path: Path) -> Image.Image:
        """Load and validate image file."""
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        
        img = Image.open(path)
        
        # Validate format
        if img.format not in ["PNG", "JPEG", "WEBP"]:
            raise ValueError(f"Unsupported format: {img.format}")
        
        return img
    
    def resize_for_podcast(self, image: Image.Image) -> Image.Image:
        """Resize image to podcast album art standard."""
        return image.resize(self.PODCAST_ART_SIZE, Image.Resampling.LANCZOS)
    
    def resize_for_youtube(self, image: Image.Image) -> Image.Image:
        """Resize image to YouTube thumbnail standard."""
        return image.resize(self.YOUTUBE_THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
    
    def save_optimized(self, image: Image.Image, output_path: Path) -> None:
        """Save image optimized for size."""
        # Save as PNG with optimization
        image.save(output_path, format="PNG", optimize=True)
        
        # Check file size
        size_kb = output_path.stat().st_size / 1024
        if size_kb > self.MAX_FILE_SIZE_KB:
            # Reduce quality if too large
            image.save(output_path, format="JPEG", quality=85, optimize=True)
```

### BaseImageProvider Interface (Future)
```python
from abc import ABC, abstractmethod

class BaseImageProvider(ABC):
    """Abstract base class for image generation providers."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: str | None = None
    ) -> Image.Image:
        """
        Generate image from text prompt.
        
        Args:
            prompt: Text description of desired image
            width: Image width in pixels
            height: Image height in pixels
            style: Optional style modifier (e.g., "cartoon", "realistic")
            
        Returns:
            Generated PIL Image
        """
        pass
    
    @abstractmethod
    def get_cost(self, width: int, height: int) -> float:
        """Calculate cost for image generation."""
        pass
```

### Mock Image Provider
```python
from PIL import Image, ImageDraw, ImageFont

class MockImageProvider(BaseImageProvider):
    """Mock provider that generates placeholder images."""
    
    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: str | None = None
    ) -> Image.Image:
        """Generate simple placeholder image."""
        # Create solid color background
        img = Image.new("RGB", (width, height), color=(100, 150, 200))
        
        # Add text
        draw = ImageDraw.Draw(img)
        text = f"MOCK\n{prompt[:50]}"
        
        # Use default font
        font = ImageFont.load_default()
        
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((width - text_width) // 2, (height - text_height) // 2)
        
        draw.text(position, text, fill=(255, 255, 255), font=font)
        
        return img
    
    def get_cost(self, width: int, height: int) -> float:
        return 0.0  # Mock is free
```

### Episode Artwork Generation
```python
class EpisodeArtworkGenerator:
    def __init__(self, image_manager: ImageManager):
        self.manager = image_manager
    
    def generate_artwork(
        self,
        episode_title: str,
        characters: list[Character],
        custom_image: Path | None = None
    ) -> Image.Image:
        """Generate episode artwork."""
        if custom_image:
            # Use custom image
            img = self.manager.load_image(custom_image)
        else:
            # Use default podcast logo
            logo_path = Path("data/images/logo.png")
            img = self.manager.load_image(logo_path)
        
        # Resize for podcast
        img = self.manager.resize_for_podcast(img)
        
        # Optional: Add text overlay
        img = self._add_text_overlay(img, episode_title)
        
        return img
    
    def _add_text_overlay(self, image: Image.Image, text: str) -> Image.Image:
        """Add text overlay to image."""
        draw = ImageDraw.Draw(image)
        
        # Load font (use default if custom not available)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()
        
        # Add semi-transparent background for text
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 128))
        image = Image.alpha_composite(image.convert("RGBA"), overlay)
        
        # Draw text at bottom
        draw = ImageDraw.Draw(image)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        position = ((image.width - text_width) // 2, image.height - 100)
        
        draw.text(position, text, fill=(255, 255, 255), font=font)
        
        return image.convert("RGB")
```

## 🧪 Testing Requirements

### Unit Tests
- **ImageManager Tests**:
  - Load PNG, JPEG, WEBP images
  - Validate minimum dimensions
  - Resize to podcast art size (1400x1400)
  - Resize to YouTube thumbnail size (1280x720)
  - Optimize file size (<512KB)
  
- **Mock Provider Tests**:
  - Generate placeholder with prompt text
  - Return correct dimensions
  - Cost is $0

### Integration Tests
- **Artwork Generation**:
  - Generate episode artwork with default logo
  - Generate artwork with custom image
  - Add text overlay to artwork
  - Embed artwork in MP3 file

### Fixtures
```python
@pytest.fixture
def sample_image(tmp_path):
    img = Image.new("RGB", (1600, 1600), color=(255, 0, 0))
    img_path = tmp_path / "test_image.png"
    img.save(img_path)
    return img_path

@pytest.fixture
def podcast_logo():
    return Path("data/images/logo.png")
```

## 📝 Implementation Notes

### Dependencies
```toml
[project]
dependencies = [
    "Pillow>=10.0.0"
]

[project.optional-dependencies]
future = [
    "replicate>=0.15.0",  # For Flux
    "openai>=1.12.0"      # For DALL-E (already in WP2)
]
```

### Key Design Decisions
1. **Pillow for Image Processing**: Lightweight, well-supported library
2. **Optional Generation**: Image generation is NOT required for MVP (use defaults)
3. **Reference Images**: Characters have fixed reference images, not generated
4. **Podcast Standards**: Follow Apple Podcasts guidelines (1400x1400 minimum, <512KB)
5. **Placeholder Support**: System works without any images (generates placeholders)

### Image Standards
- **Album Art**: 1400x1400 to 3000x3000 pixels, PNG or JPEG, <512KB
- **YouTube Thumbnail**: 1280x720 pixels, PNG or JPEG
- **Character Images**: 512x512 to 1024x1024, PNG with transparency

### Future Enhancements (Post-MVP)
- Dynamic episode artwork generation based on topic
- Character expression variants (happy, surprised, thoughtful)
- Automated thumbnail generation with character compositing
- Integration with Flux for custom artwork

## 📂 File Structure
```
src/services/image/
├── __init__.py
├── manager.py
├── base.py                # BaseImageProvider
├── episode_artwork.py
├── compositor.py          # (Optional)
├── factory.py
└── providers/
    ├── __init__.py
    ├── mock_provider.py
    ├── flux_provider.py   # (Future)
    └── dalle_provider.py  # (Future)

data/images/
├── logo.png               # Default podcast logo
└── placeholders/
    └── character_default.png

data/characters/images/
├── oliver.png
└── hannah.png

tests/services/image/
├── test_manager.py
├── test_episode_artwork.py
└── test_image_integration.py
```

## ✅ Definition of Done
- [ ] ImageManager loads and validates images (PNG, JPEG, WEBP)
- [ ] Image resizing to podcast (1400x1400) and YouTube (1280x720) standards
- [ ] Episode artwork generation with default logo
- [ ] Character reference images created (Oliver, Hannah)
- [ ] Mock image provider generates placeholders
- [ ] Integration with audio exporter for album art embedding
- [ ] Test coverage ≥ 70% (lower threshold since mostly optional features)
- [ ] Documentation includes image standards and format guidelines
