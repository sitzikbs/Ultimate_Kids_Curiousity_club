# ADR 007: Website Hosting Provider Selection

**Status**: Accepted  
**Date**: 2025-12-26  
**Deciders**: Development Team  
**Context**: WP10a - Website & Distribution

## Context

The Kids Curiosity Club website is a static HTML/CSS/JavaScript site that needs reliable, fast, and cost-effective hosting. The site serves as the primary marketing and discovery platform for our podcast shows, requiring:

- Fast global content delivery (CDN)
- SSL/TLS certificate management
- Easy deployment from GitHub
- Custom domain support
- Zero or low cost for initial launch
- Minimal configuration and maintenance

## Decision

We will use **Cloudflare Pages** as our primary hosting provider for the Kids Curiosity Club website.

## Rationale

### Cloudflare Pages Advantages

1. **Free Tier**: Unlimited bandwidth and requests on free tier, perfect for our needs
2. **Global CDN**: Built-in content delivery network with 200+ edge locations worldwide
3. **Automatic SSL**: Free SSL certificates with automatic renewal
4. **GitHub Integration**: Direct deployment from GitHub repository
5. **Zero Configuration**: No server setup or maintenance required
6. **Fast Performance**: Edge caching provides sub-100ms response times globally
7. **Developer Experience**: Simple CI/CD with GitHub Actions integration
8. **Analytics**: Built-in Web Analytics (privacy-friendly, no cookie banner needed)
9. **Cache Control**: Fine-grained cache header control for different asset types

### Alternatives Considered

#### GitHub Pages
- **Pros**: Native GitHub integration, free, simple
- **Cons**: Limited CDN performance, no custom cache headers, slower build times
- **Verdict**: Good but not as performant as Cloudflare

#### Netlify
- **Pros**: Excellent developer experience, form handling, serverless functions
- **Cons**: More complex than needed, bandwidth limits on free tier
- **Verdict**: Over-featured for our static site needs

#### Vercel
- **Pros**: Great performance, excellent Next.js support
- **Cons**: Optimized for frameworks (we're pure HTML), bandwidth limits
- **Verdict**: Not ideal for vanilla static sites

## Implementation

### Deployment Configuration

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
      - uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: kids-curiosity-club
          directory: website
```

### Cache Strategy

- **HTML files**: Short cache (5 minutes) - allows quick content updates
- **CSS/JS/Images**: Long cache (1 year) - static assets with versioning
- **Episode JSON**: Medium cache (5 minutes) - dynamic episode data
- **Sitemap/Robots**: Short cache (1 hour) - SEO files

Implemented via `_headers` file in website root:

```
/assets/*
  Cache-Control: public, max-age=31536000, immutable

/*.html
  Cache-Control: public, max-age=300, must-revalidate

/data/episodes/*.json
  Cache-Control: public, max-age=300, must-revalidate

/sitemap.xml
  Cache-Control: public, max-age=3600, must-revalidate
```

### Domain Configuration

1. Point `kidscuriosityclub.com` to Cloudflare Pages via CNAME
2. Enable "Always Use HTTPS" in Cloudflare dashboard
3. Set up `www` to non-www redirect
4. Enable HSTS (HTTP Strict Transport Security)

## Consequences

### Positive

- Zero hosting costs for foreseeable future
- Excellent global performance (< 2s page load times)
- Automatic deployments on every push to main
- Free SSL with automatic renewal
- Built-in DDoS protection from Cloudflare
- No server maintenance burden

### Negative

- Vendor lock-in to Cloudflare ecosystem
- Limited to static content (no server-side processing)
- Requires Cloudflare account and API token management
- Migration would require redeployment to new platform

### Neutral

- GitHub Actions required for deployment automation
- Need to manage Cloudflare secrets in GitHub repository settings
- Sitemap must be regenerated on each deployment

## Compliance & Monitoring

- Monitor deployment success via GitHub Actions logs
- Track website performance with Cloudflare Analytics
- Set up Google Search Console for SEO monitoring
- Review hosting costs monthly (should remain $0)

## Future Considerations

If we need server-side features in the future (user accounts, comments, forms), we can:
1. Add Cloudflare Workers for serverless functions
2. Keep static hosting on Pages, add API via separate service
3. Migrate to Netlify/Vercel for more built-in features

For now, pure static hosting is optimal for our content delivery needs.

---

**Related Documents**:
- [WP10a: Website & SEO](../work_packages/WP10a_Website.md)
- [Website README](../../website/README.md)
- [Deployment Workflow](../../.github/workflows/deploy-website.yml)
