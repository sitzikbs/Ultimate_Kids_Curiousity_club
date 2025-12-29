# Kids Curiosity Club - Website

This directory contains all the files for the Kids Curiosity Club public-facing website.

## 🎉 New Features (WP10a)

### ✅ Dynamic Episode Listings
- Episodes load from JSON data files
- Interactive play buttons with HTML5 audio
- Show notes with expandable content
- Progress tracking via localStorage
- Google Analytics event tracking

### ✅ SEO Optimization
- Schema.org JSON-LD markup (PodcastSeries, Organization)
- Open Graph tags for social media sharing
- Twitter Card tags
- Optimized meta descriptions and titles
- Sitemap.xml with all pages and episodes
- Robots.txt for search engines

### ✅ Deployment Ready
- CI/CD pipeline with GitHub Actions
- Cloudflare Pages configuration
- Cache headers for optimal performance
- Security headers configured
- Automatic sitemap generation

## 📁 Directory Structure

```
website/
├── index.html              # Homepage with "Play Latest Episode"
├── sitemap.xml            # Auto-generated sitemap
├── robots.txt             # Search engine directives
├── _headers               # Cache and security headers
├── assets/                # Images, logos, icons
├── css/
│   └── style.css         # Main stylesheet (with episode card styles)
├── js/
│   └── bundle.min.js     # All JavaScript (includes episode player)
├── data/
│   ├── shows.json        # Show metadata
│   ├── external_links.json  # Social media and podcast links
│   └── episodes/
│       ├── hannah_the_historian.json  # Hannah's episodes
│       └── oliver_the_inventor.json   # Oliver's episodes
└── pages/
    ├── about.html
    ├── shows.html
    ├── subscribe.html
    ├── contact.html
    ├── privacy.html
    └── shows/
        ├── hannah-the-historian.html  # Dynamic episode listing
        └── oliver-the-inventor.html   # Dynamic episode listing
```

## 🚀 Quick Start

### Local Development

```bash
# Serve website locally
python -m http.server 8000 --directory website

# Open browser to http://localhost:8000
```

### Adding New Episodes

1. Edit the appropriate file in `website/data/episodes/`
2. Add new episode object to the `episodes` array
3. See [Content Guide](../docs/CONTENT_GUIDE.md) for details

### Regenerating Sitemap

```bash
python scripts/generate_sitemap.py
```

## 🧪 Testing

### Run Website Tests

```bash
# Test website structure, episodes, SEO
uv run pytest tests/test_website.py -v

# Validate HTML files
python scripts/validate_html.py
```

### Manual Testing Checklist

- [ ] Homepage loads and displays shows
- [ ] "Play Latest Episode" button works
- [ ] Show pages display episodes dynamically
- [ ] Play buttons trigger audio playback
- [ ] Show notes toggle correctly
- [ ] Progress bars appear for in-progress episodes
- [ ] All images load correctly
- [ ] Links work on all pages
- [ ] Mobile responsive (test on phone)

## 📚 Documentation

- [Deployment Guide](../docs/DEPLOYMENT.md) - Full deployment instructions
- [Content Guide](../docs/CONTENT_GUIDE.md) - How to update content
- [ADR 007](../docs/decisions/007-hosting-provider.md) - Hosting decision
- [WP10a](../docs/work_packages/WP10a_Website.md) - Full work package

## ✅ Completed Features

- ✅ Static HTML/CSS/JS website
- ✅ Show pages for Hannah and Oliver
- ✅ Google Analytics integrated
- ✅ Responsive design
- ✅ Dynamic episode listings
- ✅ HTML5 audio player with progress tracking
- ✅ Schema.org markup for SEO
- ✅ Open Graph and Twitter Card tags
- ✅ Sitemap generation
- ✅ CI/CD deployment pipeline
- ✅ Cache and security headers

## 🔜 Remaining Tasks

### High Priority
- [ ] **Subscribe to mailing list** - Add email subscription functionality
- [ ] **Update podcast platform links** - Once podcast is live on platforms
- [ ] **Add more podcast directories** - Expand beyond Apple/Spotify
- [ ] **Test live deployment** - Deploy to Cloudflare Pages
- [ ] **Submit sitemap to Google Search Console**

### Future Enhancements
- [ ] Show banner images (currently uses preview images)
- [ ] Social media links (once profiles are created)
- [ ] Episode search and filtering
- [ ] Dark mode toggle
- [ ] Multi-language support
- [ ] Episode transcripts
- [ ] User comments/ratings

## 🔧 Technologies Used

- **HTML5** - Semantic markup
- **CSS3** - Custom styles with CSS variables
- **JavaScript (ES6+)** - Vanilla JS, no frameworks
- **Bootstrap 5.3** - UI components and responsive grid
- **Google Fonts** - Nunito (headings) and Lato (body)
- **Google Analytics** - Usage tracking
- **Schema.org** - Structured data for SEO

## 📊 Performance

Target metrics (Lighthouse):
- Performance: >90
- Accessibility: >90
- Best Practices: >90
- SEO: >90

Optimizations:
- CDN-hosted dependencies
- Minified JavaScript
- Cache headers configured
- No render-blocking resources
- Optimized images

## 🔒 Security

- SSL/TLS encryption (via Cloudflare)
- Security headers configured
- No exposed API keys
- CORS properly configured
- XSS protection enabled

---

**Last Updated**: 2025-12-26  
**Status**: ✅ Ready for production deployment
