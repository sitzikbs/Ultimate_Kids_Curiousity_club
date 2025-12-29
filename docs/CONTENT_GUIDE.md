# Website Content Update Guide

Quick reference for updating website content without technical knowledge.

## Adding a New Episode

### Step 1: Prepare Episode Information

Collect the following information:
- Episode title
- Episode description (1-2 sentences)
- Duration (format: "M:SS")
- Duration in seconds
- Publish date (ISO format: "YYYY-MM-DDTHH:MM:SSZ")
- Audio file URL (hosted on CDN)
- Episode artwork URL
- Show notes (HTML and plain text)
- Tags (3-5 relevant tags)
- Key concepts covered

### Step 2: Update Episode JSON File

1. Navigate to `website/data/episodes/`
2. Open the appropriate show file:
   - `hannah_the_historian.json` for Hannah's show
   - `oliver_the_inventor.json` for Oliver's show
3. Add a new episode object to the `episodes` array:

```json
{
  "id": "ep_003",
  "title": "Your Episode Title",
  "description": "Brief description of what listeners will learn.",
  "duration": "9:30",
  "duration_seconds": 570,
  "publish_date": "2025-12-31T10:00:00Z",
  "audio_url": "https://cdn.kidscuriosityclub.com/hannah_the_historian/ep_003.mp3",
  "artwork_url": "../../assets/shows/hannah_the_historian/Hannah_the_historian.jpg",
  "show_notes_html": "<p>Detailed episode notes...</p><h3>Learning Objectives</h3><ul><li>Objective 1</li><li>Objective 2</li></ul>",
  "show_notes_text": "Plain text version of show notes for RSS feeds",
  "tags": ["History", "Ancient Rome", "Culture"],
  "concepts": ["Roman Empire", "gladiators", "Colosseum"],
  "file_size": 7500000,
  "explicit": false
}
```

### Step 3: Commit and Push

```bash
git add website/data/episodes/
git commit -m "Add episode: [Episode Title]"
git push origin main
```

The website will automatically update within a few minutes.

## Updating Show Information

To change show descriptions, tags, or images:

1. Edit `website/data/shows.json`
2. Update the relevant show object
3. Commit and push changes

## Adding a New Show

### Step 1: Create Show Data

1. Add show to `website/data/shows.json`:

```json
{
  "title": "New Show Name",
  "image": "assets/shows/new_show/artwork.jpg",
  "description": "Show description",
  "link": "shows/new-show.html",
  "tags": ["Tag1", "Tag2", "Tag3"]
}
```

### Step 2: Create Episode Data File

Create `website/data/episodes/new_show.json`:

```json
{
  "show_id": "new_show",
  "show_title": "New Show Name",
  "episodes": []
}
```

### Step 3: Create Show Page

Copy one of the existing show pages (`website/pages/shows/hannah-the-historian.html`) and:

1. Update the title and meta tags
2. Update the background image in the header
3. Update the show description
4. Update the `renderEpisodes()` call with the new show ID
5. Update Schema.org JSON-LD with show details

### Step 4: Add Show Artwork

Place show artwork in `website/assets/shows/new_show/`:
- Main artwork: `new_show.jpg` (at least 1400x1400px)
- Episode artwork (can use same as main)

## Updating Social Media Links

Edit `website/data/external_links.json`:

```json
{
  "social": {
    "instagram": "https://instagram.com/kidscuriosityclub",
    "facebook": "https://facebook.com/kidscuriosityclub",
    "twitter": "https://twitter.com/kidscuriosityclub"
  }
}
```

## Updating Podcast Platform Links

When podcast is live on platforms, update `website/data/external_links.json`:

```json
{
  "podcast": {
    "apple": "https://podcasts.apple.com/...",
    "spotify": "https://open.spotify.com/show/...",
    "amazon": "https://music.amazon.com/podcasts/...",
    "youtube": "https://youtube.com/@kidscuriosityclub",
    "rss": "https://kidscuriosityclub.com/feed.xml"
  }
}
```

## Content Guidelines

### Episode Titles
- Keep under 60 characters
- Make it engaging and descriptive
- Include the main topic or concept

### Episode Descriptions
- 1-2 sentences (150-200 characters)
- Highlight what kids will learn
- Use action words (discover, explore, learn, uncover)

### Show Notes
- Start with episode summary paragraph
- Include "Learning Objectives" section (3-5 bullet points)
- Include "Key Concepts" section
- Optional: "Try It Yourself!" activity
- Optional: "Fun Fact" callout

### Tags
- Use 3-5 tags per episode
- Choose from existing categories when possible
- Tags help with filtering and search
- Examples: History, STEM, Geography, Innovation, Culture

### Concepts
- List 3-5 key educational concepts
- Use simple, searchable terms
- These may be used for future features

## SEO Best Practices

### Page Titles
- Format: "[Show/Episode Name] - Kids Curiosity Club"
- Keep under 60 characters
- Include primary keyword

### Meta Descriptions
- 150-160 characters
- Include target keywords naturally
- End with call-to-action when appropriate

### Images
- Always include alt text
- Use descriptive filenames
- Optimize file sizes (keep under 200KB)
- Prefer JPG for photos, PNG for graphics

## Testing Changes Locally

Before pushing to production:

1. **Validate HTML**:
   ```bash
   python scripts/validate_html.py
   ```

2. **Test locally**:
   ```bash
   python -m http.server 8000 --directory website
   # Open http://localhost:8000 in browser
   ```

3. **Check episode loading**:
   - Navigate to show page
   - Verify episodes display correctly
   - Test play button
   - Verify show notes display

4. **Regenerate sitemap**:
   ```bash
   python scripts/generate_sitemap.py
   ```

## Common Issues

### Episode Not Showing
- Check JSON syntax (commas, quotes)
- Verify episode ID is unique
- Ensure publish_date is in the future or past
- Check audio_url is accessible

### Broken Images
- Verify image path is correct relative to website root
- Check image file exists
- Ensure image URL works in browser

### Sitemap Not Updated
- Run `python scripts/generate_sitemap.py`
- Commit and push sitemap.xml
- Wait for deployment to complete

## Need Help?

- Check existing episodes for examples
- Review [WP10a Documentation](../work_packages/WP10a_Website.md)
- Test changes locally before pushing
- Ask for help if JSON syntax is unclear

---

**Remember**: Always test locally before pushing to production!
