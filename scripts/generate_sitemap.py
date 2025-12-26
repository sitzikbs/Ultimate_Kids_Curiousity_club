#!/usr/bin/env python3
"""Generate sitemap.xml for the Kids Curiosity Club website."""

import json
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET


def generate_sitemap(base_url: str = "https://kidscuriosityclub.com") -> str:
    """
    Generate sitemap.xml content for the website.

    Args:
        base_url: Base URL of the website

    Returns:
        XML content as string
    """
    # Create root element
    urlset = ET.Element(
        "urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    )

    # Static pages with priorities
    static_pages = [
        ("", "1.0", "daily"),  # Homepage
        ("pages/about.html", "0.8", "monthly"),
        ("pages/shows.html", "0.9", "weekly"),
        ("pages/subscribe.html", "0.8", "monthly"),
        ("pages/contact.html", "0.7", "monthly"),
        ("pages/privacy.html", "0.5", "yearly"),
    ]

    current_date = datetime.now().strftime("%Y-%m-%d")

    for page, priority, changefreq in static_pages:
        url_elem = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url_elem, "loc")
        loc.text = f"{base_url}/{page}" if page else base_url
        lastmod = ET.SubElement(url_elem, "lastmod")
        lastmod.text = current_date
        priority_elem = ET.SubElement(url_elem, "priority")
        priority_elem.text = priority
        changefreq_elem = ET.SubElement(url_elem, "changefreq")
        changefreq_elem.text = changefreq

    # Load shows data
    website_dir = Path(__file__).parent.parent / "website"
    shows_file = website_dir / "data" / "shows.json"

    if shows_file.exists():
        with shows_file.open() as f:
            shows = json.load(f)

        # Add show pages
        for show in shows:
            url_elem = ET.SubElement(urlset, "url")
            loc = ET.SubElement(url_elem, "loc")
            loc.text = f"{base_url}/pages/{show['link']}"
            lastmod = ET.SubElement(url_elem, "lastmod")
            lastmod.text = current_date
            priority_elem = ET.SubElement(url_elem, "priority")
            priority_elem.text = "0.9"
            changefreq_elem = ET.SubElement(url_elem, "changefreq")
            changefreq_elem.text = "weekly"

    # Load episode data and add episode pages
    episodes_dir = website_dir / "data" / "episodes"
    if episodes_dir.exists():
        for episode_file in episodes_dir.glob("*.json"):
            with episode_file.open() as f:
                episode_data = json.load(f)

            for episode in episode_data.get("episodes", []):
                # Convert publish date to sitemap format
                try:
                    pub_date = datetime.fromisoformat(
                        episode["publish_date"].replace("Z", "+00:00")
                    )
                    lastmod_date = pub_date.strftime("%Y-%m-%d")
                except Exception:
                    lastmod_date = current_date

                url_elem = ET.SubElement(urlset, "url")
                loc = ET.SubElement(url_elem, "loc")
                # Note: Individual episode pages would need to be created
                # For now, link to show page with hash
                show_id = episode_data["show_id"]
                show_page = show_id.replace("_", "-")
                loc.text = f"{base_url}/pages/shows/{show_page}.html#{episode['id']}"
                lastmod = ET.SubElement(url_elem, "lastmod")
                lastmod.text = lastmod_date
                priority_elem = ET.SubElement(url_elem, "priority")
                priority_elem.text = "0.7"
                changefreq_elem = ET.SubElement(url_elem, "changefreq")
                changefreq_elem.text = "monthly"

    # Generate XML string with declaration
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")

    # Convert to string
    xml_str = ET.tostring(urlset, encoding="unicode", method="xml")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'


def main() -> None:
    """Generate and save sitemap.xml."""
    website_dir = Path(__file__).parent.parent / "website"
    sitemap_path = website_dir / "sitemap.xml"

    sitemap_content = generate_sitemap()

    with sitemap_path.open("w", encoding="utf-8") as f:
        f.write(sitemap_content)

    print(f"✅ Sitemap generated successfully at {sitemap_path}")
    print(f"   Total URLs: {sitemap_content.count('<url>')}")


if __name__ == "__main__":
    main()
