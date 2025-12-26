# Website Deployment Guide

This guide covers deploying the Kids Curiosity Club website to Cloudflare Pages.

## Prerequisites

1. **Cloudflare Account**: Sign up at [cloudflare.com](https://cloudflare.com) if you don't have one
2. **Domain**: Register `kidscuriosityclub.com` (or use a test domain)
3. **GitHub Access**: Admin access to this repository

## Setup Steps

### 1. Create Cloudflare Pages Project

1. Log into Cloudflare Dashboard
2. Go to **Pages** → **Create a project**
3. Connect to GitHub and select this repository
4. Configure build settings:
   - **Production branch**: `main`
   - **Build command**: Leave empty (static site)
   - **Build output directory**: `website`
5. Click **Save and Deploy**

### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

1. **CLOUDFLARE_API_TOKEN**
   - Go to Cloudflare Dashboard → My Profile → API Tokens
   - Create token with "Edit Cloudflare Pages" permissions
   - Copy the token to GitHub secrets

2. **CLOUDFLARE_ACCOUNT_ID**
   - Go to Cloudflare Pages → Your project → Settings
   - Copy the Account ID
   - Add to GitHub secrets

### 3. Configure Domain (Optional)

If you own `kidscuriosityclub.com`:

1. In Cloudflare Pages project, go to **Custom domains**
2. Click **Set up a custom domain**
3. Enter `kidscuriosityclub.com`
4. Follow DNS configuration instructions
5. Set up `www` redirect:
   - Add `www.kidscuriosityclub.com` as custom domain
   - Enable automatic redirect

### 4. Enable SSL/TLS

1. Go to **SSL/TLS** in Cloudflare Dashboard
2. Set encryption mode to **Full** or **Full (strict)**
3. Enable **Always Use HTTPS**
4. Enable **HTTP Strict Transport Security (HSTS)**

### 5. Configure Cache Rules (Optional)

The `_headers` file in the website directory already configures caching. To customize:

1. Go to **Rules** → **Page Rules** in Cloudflare
2. Add rules for specific paths if needed

## Deployment Process

### Automatic Deployment

Every push to `main` branch with changes to `website/**` triggers automatic deployment via GitHub Actions.

The workflow:
1. Checks out code
2. Generates fresh sitemap.xml
3. Deploys to Cloudflare Pages
4. Posts comment on PRs (if applicable)

### Manual Deployment

To deploy manually:

```bash
# Generate sitemap
python scripts/generate_sitemap.py

# Trigger workflow via GitHub Actions
# Go to Actions → Deploy Website → Run workflow
```

### Local Testing

To test the website locally:

```bash
# Install a simple HTTP server
python -m http.server 8000 --directory website

# Or use Node.js
npx http-server website -p 8000

# Open browser to http://localhost:8000
```

## Post-Deployment Tasks

### 1. Submit Sitemap to Google Search Console

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add property for `kidscuriosityclub.com`
3. Verify domain ownership
4. Submit sitemap: `https://kidscuriosityclub.com/sitemap.xml`

### 2. Test Social Media Sharing

Test Open Graph tags:
- **Facebook**: [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
- **Twitter**: [Twitter Card Validator](https://cards-dev.twitter.com/validator)
- **LinkedIn**: [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/)

### 3. Validate Schema.org Markup

Use [Google Rich Results Test](https://search.google.com/test/rich-results) to validate JSON-LD markup.

### 4. Run Lighthouse Audit

1. Open website in Chrome
2. Open DevTools (F12)
3. Go to **Lighthouse** tab
4. Run audit for:
   - Performance
   - Accessibility
   - Best Practices
   - SEO

Target scores: >90 for all categories

## Monitoring

### Cloudflare Analytics

- View real-time and historical traffic
- Track page views, unique visitors
- Monitor performance metrics
- All available in Cloudflare Pages dashboard

### Google Analytics

Already integrated via `bundle.min.js`:
- Track ID: `G-6Y7PCZS0FZ`
- Events tracked:
  - Page views
  - Episode plays
  - Episode completions

## Updating Content

### Adding New Episodes

1. Edit episode JSON files in `website/data/episodes/`
2. Add new episode object to `episodes` array
3. Commit and push to `main` branch
4. Sitemap auto-regenerates on deployment

Example:

```json
{
  "id": "ep_003",
  "title": "New Episode Title",
  "description": "Episode description...",
  "duration": "9:30",
  "duration_seconds": 570,
  "publish_date": "2025-12-31T10:00:00Z",
  "audio_url": "https://cdn.kidscuriosityclub.com/show_id/ep_003.mp3",
  "artwork_url": "../../assets/shows/show_id/artwork.jpg",
  "show_notes_html": "<p>Episode notes...</p>",
  "show_notes_text": "Episode notes...",
  "tags": ["Tag1", "Tag2"],
  "concepts": ["concept1", "concept2"],
  "file_size": 7500000,
  "explicit": false
}
```

### Regenerating Sitemap

Sitemap regenerates automatically on deployment. To regenerate manually:

```bash
python scripts/generate_sitemap.py
```

## Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs
2. Verify Cloudflare API token is valid
3. Ensure Account ID is correct
4. Check for syntax errors in HTML/CSS/JS

### Pages Not Loading

1. Check browser console for errors
2. Verify file paths are correct
3. Check network tab for failed requests
4. Clear browser cache

### Sitemap Not Updating

1. Run `python scripts/generate_sitemap.py` locally
2. Commit and push changes
3. Verify workflow runs successfully
4. Check sitemap.xml on live site

### Analytics Not Tracking

1. Verify Google Analytics ID in `bundle.min.js`
2. Check browser console for gtag errors
3. Disable ad blockers for testing
4. Wait 24-48 hours for data to appear

## Security

### Headers Configuration

The `_headers` file configures:
- **Cache-Control**: Optimized caching for different asset types
- **X-Frame-Options**: Prevents clickjacking
- **X-Content-Type-Options**: Prevents MIME sniffing
- **Referrer-Policy**: Protects user privacy
- **Permissions-Policy**: Restricts browser features

### SSL/TLS

- All traffic encrypted with TLS 1.3
- Automatic certificate renewal
- HSTS enabled (after initial testing)

## Performance Optimization

Current optimizations:
- ✅ CDN-hosted assets (Bootstrap, fonts)
- ✅ Minified JavaScript
- ✅ Optimized images
- ✅ Cache headers configured
- ✅ No render-blocking resources

Future improvements:
- [ ] Lazy-load episode images
- [ ] Pre-connect to audio CDN
- [ ] Service worker for offline support
- [ ] WebP image format

## Support

For issues or questions:
- Check [Cloudflare Pages docs](https://developers.cloudflare.com/pages/)
- Review GitHub Actions workflow logs
- Open an issue in this repository

---

**Last Updated**: 2025-12-26  
**Deployment Status**: ✅ Ready for production
