# WP10a: Website & SEO

**Parent WP**: WP10 (Website & Distribution)  
**Status**: ⏳ Not Started  
**Dependencies**: None (can start independently)  
**Estimated Effort**: 1.5-2 days  
**Owner**: TBD  
**Subsystem:** Distribution (public-facing website)

## 📋 Overview

WP10a focuses on the **static website** component of the distribution system. The website (already ported from old repo) serves as the primary marketing and discovery platform for the shows. This WP adds dynamic episode listings, audio playback, and SEO optimization to convert visitors into listeners.

**Key Deliverables**:
- Episode listing pages with audio player
- Episode metadata schema and JSON data files
- SEO optimization (Schema.org, social media tags, sitemap)
- Analytics verification and event tracking
- Website deployment and hosting configuration

**Scope Notes**:
- Static HTML/CSS/JS site (no backend server)
- Content loaded from JSON data files
- All hosting via CDN (Cloudflare Pages)
- No user authentication or database

---

## 🎯 Tasks

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

### Schema.org Example

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "PodcastSeries",
  "name": "Oliver the Inventor",
  "description": "Explore inventions and STEM concepts with Oliver!",
  "image": "https://kidscuriosityclub.com/assets/shows/oliver_the_inventor/artwork.jpg",
  "url": "https://kidscuriosityclub.com/shows/oliver-the-inventor",
  "author": {
    "@type": "Organization",
    "name": "Kids Curiosity Club"
  }
}
</script>
```

---

## 🧪 Testing Requirements

**Website Testing**:
- [ ] Test episode JSON generation
- [ ] Verify audio player functionality
- [ ] Test across browsers (Chrome, Safari, Firefox)
- [ ] Mobile responsiveness
- [ ] Test analytics event firing (play button clicks)
- [ ] Validate Schema.org markup with Google Rich Results Test
- [ ] Check Open Graph preview on Facebook/Twitter debuggers
- [ ] Test sitemap generation and validation

**Deliverables**: Full test coverage for website features

---

## 📦 Dependencies

### External Services Needed
1. **Cloudflare Pages** (website hosting) - Free tier sufficient
2. **Domain** (kidscuriosityclub.com) - $12/year
3. **Google Analytics** - Free (already set up)
4. **Google Search Console** - Free

### Internal Dependencies
- Episode audio files hosted by WP10b (for audio_url field)
- Episode metadata from WP6 (for show notes generation)

---

## 📊 Success Metrics

### MVP (Phase 1)
- [ ] Website live with episode listings
- [ ] Audio player working for at least 1 episode
- [ ] Google Analytics tracking plays
- [ ] Schema.org markup validated
- [ ] Sitemap generated and submitted

### Full Launch (Phase 2)
- [ ] 5+ episodes per show listed
- [ ] All social media tags working
- [ ] Website loads in <2 seconds (Lighthouse score >90)
- [ ] Mobile-responsive design verified on 3+ devices

---

## 🚀 Future Enhancements (Post-MVP)

### Enhanced Website Features
- [ ] User comments/ratings (with moderation)
- [ ] Episode search and filtering
- [ ] Show transcript pages (SEO benefit)
- [ ] Dark mode toggle
- [ ] Multi-language support (Spanish, French)

### Interactive Elements
- [ ] Quiz/activity pages tied to episodes
- [ ] Downloadable worksheets/coloring pages
- [ ] Virtual character meet-and-greet pages

### Performance
- [ ] Lazy-load episode images
- [ ] Pre-load audio for "Play Latest" button
- [ ] Service worker for offline episode list

---

## 📝 Notes

### Current Website Status (Ported from Old Repo)
- ✅ Static HTML/CSS/JS website
- ✅ Show pages for Hannah and Oliver
- ✅ Google Analytics integrated
- ✅ Responsive design
- ⏳ Episode listings (placeholder, needs integration)
- ⏳ Audio player (needs implementation)
- ⏳ Podcast platform links (needs real URLs after WP10b complete)

### Website TODO (from old README.md)
- [ ] Subscribe to mailing list functionality
- [ ] Play latest episode functionality
- [ ] Show banner images (currently uses preview images)
- [ ] Update external_links.json with real podcast URLs (from WP10b)
- [ ] Add more podcast directories to subscribe page (from WP10b)

---

## 🎯 Acceptance Criteria

WP10a is complete when:
1. ✅ Website is live at kidscuriosityclub.com with SSL
2. ✅ Episode listing pages display at least 1 test episode
3. ✅ Audio player plays episodes successfully
4. ✅ Google Analytics tracking episode plays
5. ✅ Schema.org markup validated with no errors
6. ✅ Open Graph tags render correctly on social media
7. ✅ Sitemap generated and submitted to Google Search Console
8. ✅ CI/CD pipeline deploys on push to main branch
9. ✅ Website passes Lighthouse audit (>90 score)

---

*This work package creates the public-facing website that converts curious visitors into engaged listeners.*
