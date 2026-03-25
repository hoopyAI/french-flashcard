# Caigen Tan Wisdom App — Design Spec

## Overview

A PWA that matches Caigen Tan (菜根谭) quotes to users' moods using AI semantic matching. Users describe how they feel, and the app returns the most fitting quote with a modern Chinese interpretation. Quotes can be saved and exported as beautifully designed shareable images.

**Goals**: Technical practice project that showcases the creator's taste through content curation and design quality.

**Non-goals**: User growth, monetization, social features, multi-book support (for now).

## Core User Flow

1. User opens the app → sees a random Caigen Tan quote as the default state
2. User types their mood in the input field (e.g., "今天加班到很晚，很疲惫")
3. User taps submit → brief transition animation → matched quote appears
4. Quote card displays: original text (文言文) + modern interpretation (白话释义) + source (出处)
5. User can: **save** the quote to favorites / **generate a share image**

## Page Structure

### Top — Brand Area
- Product name + short slogan (small text)
- Minimal, no navigation bar needed

### Middle — Core Interaction Area
- **Input field**: placeholder text like "说说你现在的心情…"
- **Submit button**
- **Quote card**: displays matched result (original text + interpretation + source)
- Two action buttons below the card: Save to favorites / Generate share image

### Bottom — Favorites Area
- Collapsible section, hidden by default
- Each saved quote can be: viewed, deleted, or exported as a share image

### Interaction Details
- Fade-in transition animation when a new quote appears
- Share image generation shows a preview before saving
- Page loads with a random quote — always something to see without any input

## Share Image Design

The share image is the primary vehicle for showcasing taste. Design quality here is critical.

### Specs
- **Aspect ratio**: 3:4 (works well for WeChat Moments, Xiaohongshu)
- **3 templates for MVP**, user swipes to choose:
  - Ink wash / calligraphy: xuan paper texture, generous whitespace, vertical text layout
  - Modern minimal: solid/gradient background, horizontal layout, sans-serif + Chinese contrast
  - Neo-Chinese: geometric mountains/cloud motifs as subtle accents
- **Typography**: original text in calligraphy/Song-style font, interpretation in modern font — visual contrast creates hierarchy
- **Layout**: carefully tuned letter-spacing, line-height, and whitespace ratios — not just centered text
- **Watermark**: small, refined product logo — present but not distracting

### Content on the Image
- Original quote (文言文)
- Modern interpretation (白话释义)
- Source (菜根谭·前集/后集·第X则)
- Product watermark

## Technical Architecture

```
Vercel
├── Next.js (TypeScript + Tailwind CSS)
│   ├── Single page app (/)
│   └── API Route (/api/match)
│       └── Calls AI API (GPT-4o-mini or Claude Haiku)
├── PWA config
│   ├── manifest.json
│   └── Service Worker (offline caching)
└── Static assets
    ├── caigen-tan.json (full text, ~360 entries)
    └── Fonts (Noto Serif SC / LXGW WenKai)
```

### Data Layer
- **Quote data**: JSON file bundled with the app. Each entry contains:
  ```json
  {
    "id": 1,
    "collection": "前集",
    "original": "栖守道德者，寂寞一时；依阿权势者，凄凉万古。...",
    "interpretation": "坚守道德的人，可能一时寂寞；...",
    "source": "菜根谭·前集·第一则"
  }
  ```
- **Favorites**: localStorage (no login required)
- **Share image generation**: html2canvas (pure frontend, no server needed)

### AI Matching Logic (API Route)
- Send full Caigen Tan text (~360 entries, ~25K tokens) as context
- Prompt structure: "User's current mood is {input}. From the following Caigen Tan quotes, select the most fitting one. Return the id, original text, interpretation, and source."
- Model: GPT-4o-mini as default (cheapest option, sufficient for selection tasks; can swap to Claude Haiku if needed)
- Estimated cost: ~$0.004 per call (GPT-4o-mini), affordable for personal project scale

### PWA Configuration
- `manifest.json`: app name, icons, theme color, display mode (standalone)
- Service Worker: cache static assets and fonts for offline access
- Supports "Add to Home Screen" on mobile browsers

### Font Strategy
- Primary (quotes): Noto Serif SC or LXGW WenKai — elegant, readable Chinese serif
- Secondary (interpretation/UI): system font stack or a clean sans-serif
- Loaded via Google Fonts with `font-display: swap`

## Tech Stack Summary

| Layer | Choice | Reason |
|-------|--------|--------|
| Framework | Next.js 14+ (App Router) | SSR + API Routes in one project |
| Language | TypeScript | Type safety, signals technical competence |
| Styling | Tailwind CSS | Utility-first, works well with UI UX Pro Max skill |
| AI API | GPT-4o-mini (default) | Lowest cost, sufficient for quote matching |
| Image Gen | html2canvas | Client-side, no server dependency |
| Storage | localStorage | No auth needed, simple |
| Hosting | Vercel | Zero-config Next.js deployment, free tier |
| PWA | next-pwa or manual config | Offline support, installable |

## Content Structure

**Source**: Caigen Tan (菜根谭) by Hong Yingming (洪应明), Ming Dynasty

**Scope**: Full text, approximately 360 entries across two collections (前集 + 后集)

**Per-entry data**:
- `id`: sequential number
- `collection`: 前集 or 后集
- `original`: original classical Chinese text
- `interpretation`: modern Chinese interpretation
- `source`: formatted citation

**Content preparation** (prerequisite, can run in parallel with development):
1. Use AI to batch-generate modern interpretations for all ~360 entries
2. Manual review for quality and tone consistency
3. Output: final `caigen-tan.json` ready for the app

## Scope Boundaries

**In scope (MVP)**:
- Single page with mood input and quote matching
- AI-powered semantic matching via API
- Share image generation with multiple templates (3:4 ratio)
- Favorites (localStorage)
- PWA support (installable, offline-capable)
- Responsive design (mobile-first)

**Out of scope (future iterations)**:
- User accounts / login
- Multiple books (Dao De Jing, Xiao Chuang You Ji, etc.)
- Mood tags / preset labels
- Daily push notifications
- Emotion calendar / history tracking
- Embedding-based pre-filtering optimization
