# WP10: Website & Distribution

**Status**: ⏳ Not Started  
**Dependencies**: WP6 (Orchestrator - final MP3 generation)  
**Estimated Effort**: 3-4 days  
**Owner**: TBD  
**Subsystem:** Distribution (external-facing)

## 📋 Overview

Website & Distribution manages the public-facing marketing site and podcast distribution pipeline. The static website (already built, ported from old repo) serves show pages, episode listings, and subscription links. This WP focuses on **integrating episode publishing** from the content generation pipeline to podcast platforms and updating the website with new episodes.

**Key Deliverables**:
- Podcast hosting integration (Transistor.fm, Buzzsprout, or RSS.com)
- Automated episode metadata upload (title, description, show notes)
- RSS feed generation and management
- Website data updates (`shows.json`, episode listings)
- Analytics tracking (Google Analytics already integrated)
- Social media sharing automation (future)

**System Context**:
- **Subsystem:** Distribution (public-facing marketing + podcast hosting)
- **Depends on:** WP6 (Orchestrator produces final MP3s)
- **Used by:** End users (podcast listeners), podcast platforms
- **Parallel Development:** ⚠️ Can develop infrastructure in parallel, but integration requires WP6 complete

---

## 🎯 High-Level Tasks

### Task 10.1: Website Structure & Content Management
Organize episode data and integrate with existing static site.

**Subtasks**:
- [ ] 10.1.1: **Define Episode Metadata Schema**
  - Extend `shows.json` format to include episodes array
  - Schema: `{ id, title, description, duration, publish_date, audio_url, show_notes, tags }`
  - Store per-show episode manifests: `data/episodes/olivers_workshop.json`
  
- [ ] 10.1.2: **Create Episode Listing Pages**
  - Add dynamic episode list to each show page (`shows/hannah-the-historian.html`)
  - JavaScript to load episodes from `data/episodes/{show_id}.json`
  - Episode card template (title, date, duration, play button)
  - Filter by tags, sort by date
  
- [ ] 10.1.3: **Add Audio Player Integration**
  - Embed HTML5 audio player or third-party player (e.g., Plyr.io)
  - Play button on episode cards
  - "Play Latest Episode" on homepage
  - Progress tracking (localStorage)
  
- [ ] 10.1.4: **Generate Show Notes HTML**
  - Convert episode script metadata to show notes
  - Include: learning objectives, key concepts, activities mentioned
  - Link to educational resources if referenced
  - Format: HTML snippet for website + plain text for RSS

**Dependencies**: None (static website already exists)  
**Deliverables**: Updated website with episode listings and audio playback

---

### Task 10.2: Podcast Hosting Integration
Connect to podcast hosting platform for episode distribution.

**Subtasks**:
- [ ] 10.2.1: **Choose Podcast Host Provider**
  - Evaluate: Transistor.fm, Buzzsprout, RSS.com, Podbean
  - Criteria: API access, RSS generation, analytics, cost
  - Decision: Document in ADR 006
  
- [ ] 10.2.2: **Implement Upload Strategy**
  - **Option A**: Direct API upload to hosting platform
  - **Option B**: Upload to S3/R2, provide URL to hosting platform
  - **Recommendation**: Option B (more control, cheaper storage)
  
- [ ] 10.2.3: **Create Podcast Uploader Service**
  ```python
  class PodcastUploader:
      def upload_episode(
          self,
          show_id: str,
          episode: Episode,
          audio_file: Path,
          metadata: EpisodeMetadata
      ) -> str:
          """Upload episode and return public URL."""
  ```
  - Cloudflare R2 SDK integration (S3-compatible)
  - Episode metadata attachment (ID3 tags)
  - Thumbnail/artwork embedding
  
- [ ] 10.2.4: **Configure Hosting Platform**
  - Create shows on hosting platform (Oliver, Hannah)
  - Set show artwork, descriptions, categories
  - Configure RSS feed settings
  - Add podcast directories (Apple, Spotify, Google)

**Dependencies**: WP6 (produces final MP3s)  
**Deliverables**: Automated episode upload pipeline

---

### Task 10.3: RSS Feed Management
Generate and maintain RSS feeds for podcast directories.

**Subtasks**:
- [ ] 10.3.1: **RSS Feed Generator**
  ```python
  class RSSFeedGenerator:
      def generate_feed(self, show_id: str) -> str:
          """Generate RSS 2.0 + iTunes podcast XML."""
  ```
  - Podcast RSS 2.0 spec compliance
  - iTunes tags (`<itunes:*>`)
  - Spotify tags if needed
  - Episode enclosures with file size and duration
  
- [ ] 10.3.2: **Feed Hosting**
  - Host RSS at `https://kidscuriosityclub.com/feeds/{show_id}.xml`
  - Cloudflare CDN for caching
  - Support `<podcast:*>` namespace (Podcasting 2.0)
  
- [ ] 10.3.3: **Feed Validation**
  - Validate against RSS 2.0 schema
  - Check with Cast Feed Validator
  - Test in Apple Podcasts Preview
  
- [ ] 10.3.4: **Feed Updates**
  - Trigger on new episode publish
  - Update episode count, latest episode date
  - Maintain episode history (keep all published episodes)

**Dependencies**: Task 10.2 (upload pipeline)  
**Deliverables**: Valid RSS feeds for podcast directories

---

### Task 10.4: Publication Workflow
Coordinate episode publishing across all platforms.

**Subtasks**:
- [ ] 10.4.1: **Publication Orchestrator**
  ```python
  class PublicationOrchestrator:
      async def publish_episode(self, episode_id: str):
          """Full publication workflow."""
          # 1. Upload audio to R2/S3
          # 2. Update hosting platform
          # 3. Regenerate RSS feed
          # 4. Update website JSON
          # 5. Clear CDN cache
          # 6. Send notifications (future)
  ```
  
- [ ] 10.4.2: **Episode State Tracking**
  - Add `PUBLISHED` state to Episode model
  - Track publication date, platform URLs
  - Store in `episode_001_state.json`
  
- [ ] 10.4.3: **Rollback Support**
  - Unpublish episode (remove from RSS)
  - Mark as unlisted (keep URL but hide)
  - Re-publish with corrections
  
- [ ] 10.4.4: **Publication CLI Commands**
  ```bash
  # Publish episode to all platforms
  python -m src.cli publish episode ep_001 --show olivers_workshop
  
  # Unpublish episode
  python -m src.cli unpublish episode ep_001
  
  # Update episode metadata only (no re-upload)
  python -m src.cli update-metadata ep_001 --title "New Title"
  ```

**Dependencies**: WP6 (orchestrator), WP7 (CLI)  
**Deliverables**: End-to-end publication workflow

---

### Task 10.5: Analytics & SEO
Track website traffic and optimize discoverability.

**Subtasks**:
- [ ] 10.5.1: **Verify Google Analytics**
  - Already integrated in `js/bundle.min.js`
  - Test event tracking (play button clicks)
  - Set up goals (episode plays, subscriptions)
  
- [ ] 10.5.2: **Schema.org Markup**
  - Add PodcastSeries JSON-LD to show pages
  - Add PodcastEpisode JSON-LD to episode pages
  - Validate with Google Rich Results Test
  
- [ ] 10.5.3: **Social Media Meta Tags**
  - Open Graph tags for Facebook sharing
  - Twitter Card tags
  - Episode-specific images for sharing
  
- [ ] 10.5.4: **Sitemap Generation**
  - Generate `sitemap.xml` with all show/episode pages
  - Submit to Google Search Console
  - Update on each new episode

**Dependencies**: Task 10.1 (episode pages)  
**Deliverables**: Optimized SEO and analytics tracking

---

### Task 10.6: Podcast Directory Submission
Submit shows to major podcast platforms.

**Subtasks**:
- [ ] 10.6.1: **Apple Podcasts**
  - Submit RSS feed via Podcasts Connect
  - Verify artwork requirements (3000x3000 px)
  - Set show categories and language
  - Request review for Kids & Family category
  
- [ ] 10.6.2: **Spotify for Podcasters**
  - Submit RSS feed via Spotify dashboard
  - Claim show ownership
  - Set show metadata and categories
  
- [ ] 10.6.3: **Google Podcasts**
  - RSS feed auto-discovery via sitemap
  - Verify in Google Podcasts Manager
  - Add podcast:locked tag to prevent hijacking
  
- [ ] 10.6.4: **Additional Directories**
  - Amazon Music/Audible
  - Podcast Addict
  - Overcast
  - Pocket Casts
  - Update `external_links.json` with all directory URLs

**Dependencies**: Task 10.3 (RSS feeds), at least 1 published episode  
**Deliverables**: Shows live on all major podcast platforms

---

### Task 10.7: Website Deployment & Hosting
Configure hosting and deployment pipeline for static site.

**Subtasks**:
- [ ] 10.7.1: **Choose Hosting Provider**
  - **Recommendation**: Cloudflare Pages (free, fast CDN, easy GitHub integration)
  - **Alternatives**: Netlify, Vercel, GitHub Pages
  - Decision: Document in ADR 007
  
- [ ] 10.7.2: **Domain Configuration**
  - Point `kidscuriosityclub.com` to hosting provider
  - Configure SSL certificate (automatic with Cloudflare)
  - Set up `www` redirect
  
- [ ] 10.7.3: **CI/CD Pipeline**
  ```yaml
  # .github/workflows/deploy-website.yml
  name: Deploy Website
  on:
    push:
      branches: [main]
      paths: ['website/**']
  jobs:
    deploy:
      runs-on: ubuntu-latest
      steps:
        - name: Deploy to Cloudflare Pages
          uses: cloudflare/pages-action@v1
  ```
  
- [ ] 10.7.4: **Cache Configuration**
  - Set cache headers for static assets (CSS/JS/images: 1 year)
  - Short cache for episode JSON (5 minutes)
  - RSS feed: no cache (always fresh)

**Dependencies**: None (can set up early)  
**Deliverables**: Live website with automated deployments

---

## 🔧 Technical Implementation

### Episode Metadata Structure

**Website Format** (`website/data/episodes/olivers_workshop.json`):
```json
{
  "show_id": "olivers_workshop",
  "show_title": "Oliver the Inventor",
  "episodes": [
    {
      "id": "ep_001",
      "title": "The Lever Adventure",
      "description": "Oliver discovers how levers work by building a see-saw!",
      "duration": "8:32",
      "duration_seconds": 512,
      "publish_date": "2025-12-24T10:00:00Z",
      "audio_url": "https://cdn.kidscuriosityclub.com/olivers_workshop/ep_001.mp3",
      "artwork_url": "https://cdn.kidscuriosityclub.com/olivers_workshop/ep_001_artwork.jpg",
      "show_notes_html": "<p>In this episode...</p>",
      "show_notes_text": "In this episode...",
      "tags": ["Physics", "Simple Machines", "STEM"],
      "concepts": ["levers", "fulcrum", "mechanical advantage"],
      "file_size": 8388608,
      "explicit": false
    }
  ]
}
```

### RSS Feed Structure

**Podcast RSS 2.0 + iTunes**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:podcast="https://podcastindex.org/namespace/1.0">
  <channel>
    <title>Oliver the Inventor</title>
    <link>https://kidscuriosityclub.com/shows/oliver-the-inventor</link>
    <description>Explore inventions and STEM concepts with Oliver!</description>
    <language>en-us</language>
    <itunes:author>Kids Curiosity Club</itunes:author>
    <itunes:category text="Kids &amp; Family">
      <itunes:category text="Education for Kids"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="https://cdn.kidscuriosityclub.com/olivers_workshop/show_artwork.jpg"/>
    
    <item>
      <title>The Lever Adventure</title>
      <description>Oliver discovers how levers work!</description>
      <enclosure url="https://cdn.kidscuriosityclub.com/olivers_workshop/ep_001.mp3"
                 length="8388608" type="audio/mpeg"/>
      <guid isPermaLink="false">ep_001</guid>
      <pubDate>Tue, 24 Dec 2025 10:00:00 GMT</pubDate>
      <itunes:duration>512</itunes:duration>
      <itunes:episode>1</itunes:episode>
      <itunes:episodeType>full</itunes:episodeType>
    </item>
  </channel>
</rss>
```

### Publication State Machine

```
Episode States:
COMPLETE (WP6) → READY_TO_PUBLISH → PUBLISHING → PUBLISHED → LIVE

States:
- READY_TO_PUBLISH: MP3 generated, metadata ready
- PUBLISHING: Upload in progress
- PUBLISHED: On hosting platform, not in RSS yet
- LIVE: In RSS feed, available to listeners
```

---

## 🧪 Testing Requirements

### Task 10.8: Testing & Validation

**Subtasks**:
- [ ] 10.8.1: **RSS Feed Validation Tests**
  - Unit tests for RSS generator
  - Validate against RSS 2.0 schema
  - Check iTunes podcast requirements
  - Test with Cast Feed Validator
  
- [ ] 10.8.2: **Upload Pipeline Tests**
  - Mock Cloudflare R2 uploads
  - Test metadata attachment
  - Verify file permissions and URLs
  - Test rollback scenarios
  
- [ ] 10.8.3: **Website Integration Tests**
  - Test episode JSON generation
  - Verify audio player functionality
  - Test across browsers (Chrome, Safari, Firefox)
  - Mobile responsiveness
  
- [ ] 10.8.4: **End-to-End Publication Test**
  - Publish test episode to staging environment
  - Verify RSS feed updates
  - Test playback in podcast apps
  - Validate analytics tracking

**Deliverables**: Full test coverage for distribution pipeline

---

## 📦 Dependencies

### External Services Needed
1. **Cloudflare R2** (audio storage) - $0.015/GB/month
2. **Podcast Host** (Transistor.fm, Buzzsprout) - $19-49/month
3. **Domain** (kidscuriosityclub.com) - $12/year
4. **Cloudflare Pages** (website hosting) - Free tier sufficient

### Internal Dependencies
- WP6: Orchestrator must produce final MP3s with metadata
- WP7: CLI for manual publication commands
- WP1: Episode models extended with publication fields

---

## 📊 Success Metrics

### MVP (Phase 1)
- [ ] Website live with episode listings
- [ ] 1 episode published to podcast host
- [ ] RSS feed validated and submitted to Apple Podcasts
- [ ] Audio playback working on website

### Full Launch (Phase 2)
- [ ] Shows live on Apple, Spotify, Google Podcasts
- [ ] Automated publication from CLI
- [ ] Analytics tracking episode plays
- [ ] 5+ episodes published per show

---

## 🚀 Future Enhancements (Post-MVP)

### Social Media Automation
- [ ] Auto-post to Twitter/X when episode published
- [ ] Generate audiogram videos for Instagram/TikTok
- [ ] Facebook page integration

### Advanced Analytics
- [ ] Podcast download statistics from hosting platform
- [ ] Geographic listener distribution
- [ ] Episode completion rates
- [ ] A/B testing episode titles/descriptions

### Newsletter Integration
- [ ] Email list collection on website
- [ ] Auto-send episode notifications
- [ ] Weekly digest of new episodes

### Dynamic Website
- [ ] Connect website to WP9 Dashboard API
- [ ] Real-time episode status updates
- [ ] User comments/ratings (future, with moderation)

---

## 📝 Notes

### Current Website Status (Ported from Old Repo)
- ✅ Static HTML/CSS/JS website
- ✅ Show pages for Hannah and Oliver
- ✅ Google Analytics integrated
- ✅ Responsive design
- ⏳ Episode listings (placeholder, needs integration)
- ⏳ Audio player (needs implementation)
- ⏳ Podcast platform links (needs real URLs after submission)

### Website TODO (from old README.md)
- [ ] Subscribe to mailing list functionality
- [ ] Play latest episode functionality
- [ ] Show banner images (currently uses preview images)
- [ ] Update external_links.json with real podcast URLs
- [ ] Add more podcast directories to subscribe page

---

## 🎯 Acceptance Criteria

WP10 is complete when:
1. ✅ Website is live at kidscuriosityclub.com
2. ✅ At least 1 episode published to podcast hosting
3. ✅ RSS feed validated and submitted to Apple Podcasts
4. ✅ Audio playback working on website
5. ✅ CLI command `publish episode` works end-to-end
6. ✅ Analytics tracking episode plays
7. ✅ All major podcast directories submitted (Apple, Spotify, Google)
8. ✅ Publication workflow documented in user guide

---

*This work package handles the "last mile" of episode distribution - getting finished episodes in front of listeners on their preferred platforms.*
