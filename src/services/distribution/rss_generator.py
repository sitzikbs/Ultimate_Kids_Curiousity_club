"""RSS 2.0 + iTunes podcast feed generator."""

import logging
from datetime import datetime

from feedgen.feed import FeedGenerator

logger = logging.getLogger(__name__)


class PodcastFeedGenerator:
    """Generate podcast RSS feeds compliant with RSS 2.0 + iTunes."""

    def __init__(
        self,
        site_url: str = "https://kidscuriosityclub.com",
        cdn_url: str = "https://cdn.kidscuriosityclub.com",
    ) -> None:
        """Initialize feed generator.

        Args:
            site_url: Base URL for the podcast website.
            cdn_url: Base URL for CDN-served assets.
        """
        self.site_url = site_url.rstrip("/")
        self.cdn_url = cdn_url.rstrip("/")

    def generate_feed(
        self,
        show_id: str,
        show_title: str,
        show_description: str,
        author: str,
        artwork_url: str,
        episodes: list[dict],
        language: str = "en-us",
    ) -> str:
        """Generate RSS 2.0 + iTunes podcast feed XML.

        Args:
            show_id: Unique show identifier.
            show_title: Display title for the show.
            show_description: Show description.
            author: Show author/creator name.
            artwork_url: URL to show artwork (3000x3000 recommended).
            episodes: List of episode dicts with keys: id, title,
                description, audio_url, file_size_bytes,
                duration_seconds, publish_date, episode_number.
            language: RSS language code.

        Returns:
            RSS XML string.
        """
        fg = FeedGenerator()
        fg.load_extension("podcast")

        # Channel metadata
        fg.title(show_title)
        fg.link(href=f"{self.site_url}/shows/{show_id}", rel="alternate")
        fg.description(show_description)
        fg.language(language)
        fg.generator("Kids Curiosity Club Podcast Generator")
        fg.copyright(f"© {datetime.now().year} Kids Curiosity Club")

        # iTunes metadata
        fg.podcast.itunes_author(author)
        fg.podcast.itunes_category("Kids & Family", "Education for Kids")
        fg.podcast.itunes_explicit("no")
        fg.podcast.itunes_image(artwork_url)
        fg.podcast.itunes_owner(name=author, email="hello@kidscuriosityclub.com")
        fg.podcast.itunes_type("episodic")

        # Add episodes sorted oldest-first so feedgen outputs newest-first
        sorted_episodes = sorted(
            episodes,
            key=lambda e: e.get("publish_date", ""),
            reverse=False,
        )

        for ep in sorted_episodes:
            fe = fg.add_entry()
            fe.id(ep["id"])
            fe.title(ep["title"])
            fe.description(ep.get("description", ""))
            fe.published(ep.get("publish_date"))

            # Audio enclosure
            fe.enclosure(
                url=ep["audio_url"],
                length=str(ep.get("file_size_bytes", 0)),
                type="audio/mpeg",
            )

            # iTunes episode metadata
            fe.podcast.itunes_duration(int(ep.get("duration_seconds", 0)))
            fe.podcast.itunes_episode(ep.get("episode_number", 1))
            fe.podcast.itunes_episode_type("full")
            fe.podcast.itunes_explicit("no")

        return fg.rss_str(pretty=True).decode("utf-8")

    def validate_feed(self, feed_xml: str) -> dict:
        """Basic validation of RSS feed structure.

        Args:
            feed_xml: RSS XML string to validate.

        Returns:
            Dict with 'valid' bool and 'errors' list.
        """
        import xml.etree.ElementTree as ET

        errors: list[str] = []

        # Validate well-formed XML
        try:
            root = ET.fromstring(feed_xml)
        except ET.ParseError as e:
            return {"valid": False, "errors": [f"Malformed XML: {e}"]}

        if root.tag != "rss":
            errors.append(f"Root element is <{root.tag}>, expected <rss>")

        channel = root.find("channel")
        if channel is None:
            errors.append("Missing <channel> element")
        else:
            if channel.find("title") is None:
                errors.append("Missing <title> element")

        # Check for iTunes namespace
        if "xmlns:itunes" not in feed_xml:
            errors.append("Missing iTunes namespace declaration")

        # Check episodes have enclosures
        items = root.findall(".//item")
        for i, item in enumerate(items):
            if item.find("enclosure") is None:
                title = item.findtext("title", f"item {i + 1}")
                errors.append(f"Episode '{title}' missing <enclosure>")

        return {"valid": len(errors) == 0, "errors": errors}
