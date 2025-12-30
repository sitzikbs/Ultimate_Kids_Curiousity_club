"""MP3 export with ID3 tags for podcast distribution."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, COMM, ID3
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class MP3Exporter:
    """Export audio as MP3 with podcast metadata."""

    def __init__(
        self,
        bitrate: str = "192k",
        quality: str = "0",  # VBR quality (0=best, 9=worst)
    ):
        """Initialize MP3 exporter.

        Args:
            bitrate: Target bitrate (default "192k")
            quality: VBR quality setting (default "0" = best)
        """
        self.bitrate = bitrate
        self.quality = quality

    def export(
        self,
        audio: AudioSegment,
        output_path: Path | str,
        metadata: dict[str, Any] | None = None,
        album_art_path: Path | str | None = None,
    ) -> None:
        """Export audio as MP3 with ID3 tags.

        Args:
            audio: Audio segment to export
            output_path: Path for output MP3 file
            metadata: Dictionary with ID3 tag data (title, artist, album, etc.)
            album_art_path: Optional path to album art image file

        Raises:
            ValueError: If output directory doesn't exist
        """
        output_path = Path(output_path)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export audio
        logger.info(f"Exporting MP3 to {output_path} at {self.bitrate} bitrate")
        audio.export(
            str(output_path),
            format="mp3",
            bitrate=self.bitrate,
            parameters=["-q:a", self.quality],  # VBR quality
        )

        # Add ID3 tags if metadata provided
        if metadata:
            self._add_id3_tags(output_path, metadata)

        # Add album art if provided
        if album_art_path:
            self._add_album_art(output_path, album_art_path)

        logger.info(f"Successfully exported MP3: {output_path}")

    def _add_id3_tags(self, audio_path: Path, metadata: dict[str, Any]) -> None:
        """Add ID3 tags to MP3 file.

        Args:
            audio_path: Path to MP3 file
            metadata: Dictionary with tag data
        """
        try:
            audio_file = EasyID3(str(audio_path))
        except Exception:
            # Create new ID3 tag if none exists
            audio_file = EasyID3()

        # Set standard tags
        if "title" in metadata:
            audio_file["title"] = metadata["title"]
        if "artist" in metadata:
            audio_file["artist"] = metadata["artist"]
        if "album" in metadata:
            audio_file["album"] = metadata["album"]
        if "genre" in metadata:
            audio_file["genre"] = metadata["genre"]
        else:
            audio_file["genre"] = "Educational"

        # Set date/year
        if "date" in metadata:
            audio_file["date"] = metadata["date"]
        elif "year" in metadata:
            audio_file["date"] = str(metadata["year"])
        else:
            audio_file["date"] = str(datetime.now().year)

        # Add comment with generation metadata
        comment_text = None
        if "comment" in metadata:
            comment_text = metadata["comment"]
        elif "generation_metadata" in metadata:
            # Format generation metadata as comment
            gen_meta = metadata["generation_metadata"]
            comment_parts = []
            if "date" in gen_meta:
                comment_parts.append(f"Generated: {gen_meta['date']}")
            if "cost" in gen_meta:
                comment_parts.append(f"Cost: ${gen_meta['cost']:.2f}")
            if "models" in gen_meta:
                comment_parts.append(f"Models: {', '.join(gen_meta['models'])}")
            if comment_parts:
                comment_text = " | ".join(comment_parts)

        audio_file.save(str(audio_path))

        # Add comment using standard ID3 interface (not EasyID3)
        if comment_text:
            try:
                id3_file = ID3(str(audio_path))
                id3_file["COMM"] = COMM(
                    encoding=3,  # UTF-8
                    lang="eng",
                    desc="",
                    text=comment_text,
                )
                id3_file.save(str(audio_path))
            except Exception as e:
                logger.warning(f"Failed to add comment: {e}")

        logger.info(f"Added ID3 tags to {audio_path}")

    def _add_album_art(self, audio_path: Path, album_art_path: Path | str) -> None:
        """Add album art to MP3 file.

        Args:
            audio_path: Path to MP3 file
            album_art_path: Path to image file

        Raises:
            ValueError: If album art file doesn't exist
        """
        album_art_path = Path(album_art_path)
        if not album_art_path.exists():
            raise ValueError(f"Album art file not found: {album_art_path}")

        # Determine MIME type
        mime_type = self._get_mime_type(album_art_path)

        # Add album art
        try:
            audio_file = ID3(str(audio_path))
        except Exception:
            audio_file = ID3()

        with open(album_art_path, "rb") as img:
            audio_file["APIC"] = APIC(
                encoding=3,  # UTF-8
                mime=mime_type,
                type=3,  # Cover (front)
                desc="Cover",
                data=img.read(),
            )

        audio_file.save(str(audio_path))
        logger.info(f"Added album art from {album_art_path}")

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type from file extension.

        Args:
            file_path: Path to image file

        Returns:
            MIME type string
        """
        extension = file_path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
        }
        return mime_types.get(extension, "image/jpeg")
