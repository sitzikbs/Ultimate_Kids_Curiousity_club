# Admin Dashboard

This directory contains **internal-only** administrative tools for managing show blueprints and configurations.

## ⚠️ Important

**These pages are NOT part of the public website.** They are administrative tools for internal use only and should be:
- Protected by authentication in production
- Not linked from the public website
- Only accessible to authorized staff

## Pages

### `/admin/index.html` - Show Management
Admin dashboard for viewing all shows and accessing the blueprint editor.

### `/admin/blueprint.html` - Blueprint Editor
Comprehensive editor for managing:
- Protagonist profiles
- World descriptions and locations
- Supporting characters
- Educational concepts timeline

## Access

In development: `http://localhost:8000/admin/`

In production: These pages should be protected by authentication middleware at the API level.

## Design Philosophy

- Clean, modern interface using Inter font
- Separate from public website branding
- Focus on functionality and usability
- Clear visual hierarchy for complex forms

## Technical Notes

- Uses Bootstrap 5 for layout and components
- Vanilla JavaScript (no framework dependencies)
- Integrates with WP9a API endpoints
- Self-contained styling (no dependency on public site CSS)
