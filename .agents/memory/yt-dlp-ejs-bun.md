---
name: yt-dlp EJS Bun fix
description: How to make yt-dlp solve YouTube JS challenges (signature + n-challenge) in Replit without Node 22.
---

# yt-dlp YouTube JS Challenge Solving on Replit

## The rule
yt-dlp ≥2025 requires BOTH: (1) `yt-dlp-ejs` Python package AND (2) a supported JS runtime to decrypt YouTube URLs.

**Why:** YouTube enforces SABR streaming + obfuscated JS signatures. yt-dlp's EJS system solves these, but needs a runtime to run the solver scripts.

**How to apply:**
1. `pip install yt-dlp-ejs` (adds to pyproject.toml dependencies)
2. Install `bun` as system dep via installSystemDependencies(['bun'])
3. In yt-dlp Python API options: `'js_runtimes': {'bun': {}}` (must be dict, not list)
4. Use `player_client: ['tv']` — works with cookies + EJS; android/ios skip cookies entirely
5. Node.js v20 is **unsupported** (yt-dlp needs ≥22); bun ≥1.2.11 works fine
6. Bun shows a "deprecated" warning but still functions correctly

## Cookie file
- `attached_assets/cookies_1781947987715.txt` — real .youtube.com cookies from user's browser
- In code: read from `YOUTUBE_COOKIES` env secret or `YOUTUBE_COOKIES_FILE` path
