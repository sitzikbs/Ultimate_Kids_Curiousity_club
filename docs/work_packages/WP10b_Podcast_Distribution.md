# WP10b: Podcast Distribution & Hosting

**Parent WP**: WP10 (Website & Distribution)  
**Status**: ⏳ Not Started  
**Dependencies**: WP6 (Orchestrator - final MP3 generation), WP7 (CLI)  
**Estimated Effort**: 2-2.5 days  
**Owner**: TBD  
**Subsystem:** Distribution (podcast hosting & platforms)

## 📋 Overview

WP10b handles the **podcast distribution pipeline** - uploading episodes to hosting platforms, generating RSS feeds, submitting to podcast directories, and orchestrating the full publication workflow. This is the technical backend that delivers audio content to podcast apps worldwide.

**Key Deliverables**:
- Podcast hosting integration (Transistor.fm, Buzzsprout, or RSS.com)
- Automated episode metadata upload (title, description, show notes)
- RSS feed generation and management (RSS 2.0 + iTunes tags)
- Publication orchestrator for multi-platform coordination
- Podcast directory submissions (Apple, Spotify, Google)
- CI/CD pipeline for automated publishing
- Comprehensive testing suite for distribution pipeline

**Scope Notes**:
- Backend services only (no frontend UI except CLI)
- Cloudflare R2 for audio file storage (S3-compatible)
- RSS feed hosted alongside website (CDN-cached)
- Publication state tracking in episode metadata

---

## 🎯 Tasks

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

### Task 10.8: Testing & Validation
Comprehensive testing for podcast distribution pipeline.

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
  
- [ ] 10.8.3: **Integration Tests**
  - Test full publish workflow end-to-end
  - Verify RSS feed updates after publish
  - Test CDN cache invalidation
  - Verify episode state transitions
  
- [ ] 10.8.4: **End-to-End Publication Test**
  - Publish test episode to staging environment
  - Verify RSS feed updates
  - Test playback in podcast apps (Apple, Spotify, Overcast)
  - Validate analytics tracking

**Deliverables**: Full test coverage for distribution pipeline

---

## 🔧 Technical Implementation

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

Transitions:
- publish_episode() → READY_TO_PUBLISH → PUBLISHING
- upload_complete() → PUBLISHING → PUBLISHED
- update_rss() → PUBLISHED → LIVE
- unpublish_episode() → LIVE → PUBLISHED (removed from RSS)
- rollback() → Any state → READY_TO_PUBLISH
```

### Cloudflare R2 Integration

```python
import boto3

class R2Storage:
    def __init__(self, account_id: str, access_key: str, secret_key: str):
        self.s3 = boto3.client(
            's3',
            endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    
    def upload_episode(
        self, 
        bucket: str, 
        episode_id: str, 
        audio_file: Path
    ) -> str:
        """Upload episode and return public URL."""
        key = f"episodes/{episode_id}.mp3"
        self.s3.upload_file(
            str(audio_file),
            bucket,
            key,
            ExtraArgs={'ContentType': 'audio/mpeg'}
        )
        return f"https://cdn.kidscuriosityclub.com/{key}"
```

---

## 📦 Dependencies

### External Services Needed
1. **Cloudflare R2** (audio storage) - $0.015/GB/month
2. **Podcast Host** (Transistor.fm, Buzzsprout) - $19-49/month
3. **Apple Podcasts Connect** - Free (requires Apple ID)
4. **Spotify for Podcasters** - Free
5. **Google Podcasts Manager** - Free

### Internal Dependencies
- WP6: Orchestrator must produce final MP3s with metadata
- WP7: CLI for manual publication commands
- WP1: Episode models extended with publication fields
- WP10a: Website provides RSS feed hosting location

### Python Packages
```toml
# pyproject.toml additions
[project.dependencies]
boto3 = "^1.34.0"  # S3/R2 SDK
feedgen = "^1.0.0"  # RSS feed generation
mutagen = "^1.47.0"  # ID3 tag manipulation
```

---

## 📊 Success Metrics

### MVP (Phase 1)
- [ ] 1 episode successfully uploaded to R2
- [ ] RSS feed generated and validated
- [ ] Episode playable in at least 1 podcast app (Apple or Spotify)
- [ ] CLI publish command works end-to-end
- [ ] Publication state tracked correctly

### Full Launch (Phase 2)
- [ ] Shows live on Apple, Spotify, Google Podcasts
- [ ] 5+ episodes published per show
- [ ] RSS feeds validated with no errors
- [ ] Automated CI/CD publishing (future)
- [ ] Zero failed uploads (99.9% success rate)

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

### Dynamic Publishing
- [ ] Schedule episodes for future publish dates
- [ ] Batch publish multiple episodes
- [ ] Preview mode (unlisted RSS feed for testing)

---

## 📝 Notes

### Podcast Host Selection Criteria

| Provider | API | Analytics | Cost | Notes |
|----------|-----|-----------|------|-------|
| Transistor.fm | ✅ Full API | ✅ Excellent | $19/mo (10k downloads) | Best for automation |
| Buzzsprout | ⚠️ Limited | ✅ Good | $12/mo (3 hours) | User-friendly UI |
| RSS.com | ✅ Full API | ✅ Good | $0-20/mo | Free tier available |
| Podbean | ❌ No API | ⚠️ Basic | $9/mo | Manual upload only |

**Recommendation**: Transistor.fm for API-first approach, or RSS.com for cost-conscious start.

### RSS Feed Best Practices
- Keep episode descriptions under 4000 characters
- Use high-quality artwork (3000x3000 px minimum)
- Include explicit content tags (always set to `false` for kids)
- Test feed in multiple podcast apps before submission
- Update feed within 15 minutes of new episode publish

---

## 🎯 Acceptance Criteria

WP10b is complete when:
1. ✅ Episode upload pipeline working (R2 or hosting platform)
2. ✅ RSS feed generator producing valid RSS 2.0 + iTunes XML
3. ✅ At least 1 episode published and playable in podcast app
4. ✅ CLI command `publish episode` works end-to-end
5. ✅ RSS feed submitted to Apple Podcasts (in review or approved)
6. ✅ RSS feed submitted to Spotify for Podcasters
7. ✅ Google Podcasts auto-discovery working
8. ✅ Publication state tracking persisted correctly
9. ✅ Rollback/unpublish functionality tested
10. ✅ All tests passing (RSS validation, upload, integration)

---

*This work package delivers the technical infrastructure that puts episodes into the ears of curious kids worldwide.*
