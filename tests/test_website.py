"""Tests for website structure and sitemap generation."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest


class TestWebsiteStructure:
    """Test website file structure and content."""

    @pytest.fixture
    def website_dir(self) -> Path:
        """Get website directory path."""
        return Path(__file__).parent.parent / "website"

    def test_website_directory_exists(self, website_dir: Path) -> None:
        """Test that website directory exists."""
        assert website_dir.exists()
        assert website_dir.is_dir()

    def test_required_files_exist(self, website_dir: Path) -> None:
        """Test that all required website files exist."""
        required_files = [
            "index.html",
            "sitemap.xml",
            "robots.txt",
            "_headers",
            "data/shows.json",
            "data/external_links.json",
            "data/episodes/hannah_the_historian.json",
            "data/episodes/oliver_the_inventor.json",
            "pages/shows/hannah-the-historian.html",
            "pages/shows/oliver-the-inventor.html",
        ]

        for file_path in required_files:
            full_path = website_dir / file_path
            assert full_path.exists(), f"Required file missing: {file_path}"

    def test_shows_json_structure(self, website_dir: Path) -> None:
        """Test that shows.json has valid structure."""
        shows_file = website_dir / "data" / "shows.json"
        with shows_file.open() as f:
            shows = json.load(f)

        assert isinstance(shows, list)
        assert len(shows) > 0

        for show in shows:
            assert "title" in show
            assert "description" in show
            assert "link" in show
            assert "image" in show
            assert "tags" in show

    def test_episode_json_structure(self, website_dir: Path) -> None:
        """Test that episode JSON files have valid structure."""
        episodes_dir = website_dir / "data" / "episodes"
        episode_files = list(episodes_dir.glob("*.json"))

        assert len(episode_files) > 0, "No episode JSON files found"

        for episode_file in episode_files:
            with episode_file.open() as f:
                data = json.load(f)

            assert "show_id" in data
            assert "show_title" in data
            assert "episodes" in data
            assert isinstance(data["episodes"], list)

            for episode in data["episodes"]:
                required_fields = [
                    "id",
                    "title",
                    "description",
                    "duration",
                    "duration_seconds",
                    "publish_date",
                    "audio_url",
                    "artwork_url",
                    "show_notes_html",
                    "show_notes_text",
                    "tags",
                    "concepts",
                ]
                for field in required_fields:
                    assert (
                        field in episode
                    ), f"Missing field {field} in episode {episode.get('id', 'unknown')}"


class TestSitemap:
    """Test sitemap.xml generation and validity."""

    @pytest.fixture
    def sitemap_path(self) -> Path:
        """Get sitemap path."""
        return Path(__file__).parent.parent / "website" / "sitemap.xml"

    def test_sitemap_exists(self, sitemap_path: Path) -> None:
        """Test that sitemap.xml exists."""
        assert sitemap_path.exists()

    def test_sitemap_valid_xml(self, sitemap_path: Path) -> None:
        """Test that sitemap is valid XML."""
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        assert root.tag.endswith("urlset")

    def test_sitemap_has_urls(self, sitemap_path: Path) -> None:
        """Test that sitemap contains URLs."""
        tree = ET.parse(sitemap_path)
        root = tree.getroot()

        # Extract namespace
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        urls = root.findall("sm:url", ns)
        assert len(urls) > 0, "Sitemap has no URLs"

        # Check that homepage is included
        homepage_found = False
        for url in urls:
            loc = url.find("sm:loc", ns)
            if loc is not None and loc.text == "https://kidscuriosityclub.com":
                homepage_found = True
                break

        assert homepage_found, "Homepage not found in sitemap"

    def test_sitemap_url_structure(self, sitemap_path: Path) -> None:
        """Test that each URL has required elements."""
        tree = ET.parse(sitemap_path)
        root = tree.getroot()

        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = root.findall("sm:url", ns)

        for url in urls:
            # Each URL should have loc, lastmod, priority, changefreq
            loc = url.find("sm:loc", ns)
            lastmod = url.find("sm:lastmod", ns)
            priority = url.find("sm:priority", ns)
            changefreq = url.find("sm:changefreq", ns)

            assert loc is not None and loc.text, "URL missing loc"
            assert lastmod is not None and lastmod.text, "URL missing lastmod"
            assert priority is not None and priority.text, "URL missing priority"
            assert changefreq is not None and changefreq.text, "URL missing changefreq"

            # Validate priority is between 0.0 and 1.0
            priority_val = float(priority.text)
            assert 0.0 <= priority_val <= 1.0, f"Invalid priority: {priority_val}"


class TestSEO:
    """Test SEO elements in HTML pages."""

    @pytest.fixture
    def website_dir(self) -> Path:
        """Get website directory path."""
        return Path(__file__).parent.parent / "website"

    def test_homepage_has_meta_tags(self, website_dir: Path) -> None:
        """Test that homepage has required meta tags."""
        index_file = website_dir / "index.html"
        content = index_file.read_text()

        # Check for basic meta tags
        assert "<title>" in content
        assert 'name="description"' in content

        # Check for Open Graph tags
        assert 'property="og:title"' in content
        assert 'property="og:description"' in content
        assert 'property="og:image"' in content

        # Check for Twitter Card tags
        assert 'property="twitter:card"' in content
        assert 'property="twitter:title"' in content

        # Check for Schema.org JSON-LD
        assert 'type="application/ld+json"' in content
        assert "@context" in content
        assert "@type" in content

    def test_show_pages_have_meta_tags(self, website_dir: Path) -> None:
        """Test that show pages have required meta tags."""
        show_pages = [
            "pages/shows/hannah-the-historian.html",
            "pages/shows/oliver-the-inventor.html",
        ]

        for page_path in show_pages:
            page_file = website_dir / page_path
            content = page_file.read_text()

            # Check for basic meta tags
            assert "<title>" in content
            assert 'name="description"' in content

            # Check for Open Graph tags
            assert 'property="og:title"' in content
            assert 'property="og:description"' in content
            assert 'property="og:image"' in content

            # Check for Twitter Card tags
            assert 'property="twitter:card"' in content

            # Check for Schema.org PodcastSeries
            assert 'type="application/ld+json"' in content
            assert "PodcastSeries" in content

    def test_robots_txt_exists(self, website_dir: Path) -> None:
        """Test that robots.txt exists and has sitemap reference."""
        robots_file = website_dir / "robots.txt"
        assert robots_file.exists()

        content = robots_file.read_text()
        assert "User-agent:" in content
        assert "Sitemap:" in content
        assert "sitemap.xml" in content
