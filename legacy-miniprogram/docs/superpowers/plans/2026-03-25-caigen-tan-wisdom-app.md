# Caigen Tan Wisdom App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PWA that matches Caigen Tan quotes to user moods via AI, with favorites and shareable image generation.

**Architecture:** Next.js App Router single-page app. One API route handles AI matching (GPT-4o-mini). Quote data lives in a static JSON file. Favorites use localStorage. Share images rendered client-side with html2canvas.

**Tech Stack:** Next.js 14+ (App Router), TypeScript, Tailwind CSS, GPT-4o-mini, html2canvas, Vercel

**Spec:** `docs/superpowers/specs/2026-03-25-caigen-tan-wisdom-app-design.md`

---

## File Structure

```
caigen-tan-app/
├── public/
│   ├── manifest.json              # PWA manifest
│   ├── sw.js                      # Service Worker
│   ├── icons/                     # PWA icons (192x192, 512x512)
│   └── fonts/                     # Self-hosted LXGW WenKai font files
├── src/
│   ├── app/
│   │   ├── layout.tsx             # Root layout: fonts, metadata, PWA meta tags
│   │   ├── page.tsx               # Main page: composes all sections
│   │   └── api/
│   │       └── match/
│   │           └── route.ts       # AI matching endpoint
│   ├── components/
│   │   ├── Header.tsx             # Brand area: product name + slogan
│   │   ├── MoodInput.tsx          # Input field + submit button
│   │   ├── QuoteCard.tsx          # Displays quote (original + interpretation + source)
│   │   ├── ActionButtons.tsx      # Save + Share buttons below the card
│   │   ├── Favorites.tsx          # Collapsible favorites list
│   │   ├── SharePreview.tsx       # Share image preview modal with template switcher
│   │   └── ShareTemplate.tsx      # The actual share image card (rendered to canvas)
│   ├── lib/
│   │   ├── quotes.ts              # Load and access quote data
│   │   ├── favorites.ts           # localStorage read/write helpers
│   │   └── share.ts               # html2canvas image generation logic
│   ├── data/
│   │   └── caigen-tan.json        # Full quote dataset (~360 entries)
│   └── types/
│       └── index.ts               # Shared TypeScript types (Quote, Favorite, etc.)
├── tailwind.config.ts
├── next.config.ts
├── tsconfig.json
├── package.json
└── .env.local                     # OPENAI_API_KEY
```

---

## Task 0: Content Preparation — Caigen Tan Dataset

**Files:**
- Create: `caigen-tan-app/src/data/caigen-tan.json`

This task runs in parallel with Tasks 1-2. The JSON file is needed starting from Task 3.

- [ ] **Step 1: Source the full text of Caigen Tan**

Search the web for a complete, structured version of 菜根谭 (前集 + 后集). Look for versions that already separate entries individually. Chinese wikisource or classical text databases are good sources.

- [ ] **Step 2: Structure into JSON**

Format each entry as:
```json
{
  "id": 1,
  "collection": "前集",
  "original": "栖守道德者，寂寞一时；依阿权势者，凄凉万古。达人观物外之物，思身后之身，宁受一时之寂寞，毋取万古之凄凉。",
  "interpretation": "",
  "source": "菜根谭·前集·第一则"
}
```

Leave `interpretation` empty for now.

- [ ] **Step 3: Batch-generate modern interpretations**

Use AI to generate a 白话释义 for each entry. Prompt:
```
你是一位中国古典文学专家。请为以下菜根谭原文写一段简洁的白话释义（2-3句话），语言要通俗易懂但不失文雅。
原文：{original}
```

Fill in the `interpretation` field for all entries.

- [ ] **Step 4: Validate the dataset**

Write a quick validation script to check:
- All entries have non-empty `id`, `collection`, `original`, `interpretation`, `source`
- No duplicate IDs
- `collection` is either "前集" or "后集"

```bash
node -e "
const data = require('./src/data/caigen-tan.json');
const ids = data.map(d => d.id);
console.log('Total entries:', data.length);
console.log('Duplicates:', ids.length - new Set(ids).size);
data.forEach(d => {
  if (!d.original || !d.interpretation || !d.source) {
    console.log('Incomplete entry:', d.id);
  }
});
console.log('Validation complete');
"
```

- [ ] **Step 5: Commit**

```bash
git add src/data/caigen-tan.json
git commit -m "data: add caigen tan full dataset with interpretations"
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `caigen-tan-app/package.json`
- Create: `caigen-tan-app/tsconfig.json`
- Create: `caigen-tan-app/tailwind.config.ts`
- Create: `caigen-tan-app/next.config.ts`
- Create: `caigen-tan-app/src/app/layout.tsx`
- Create: `caigen-tan-app/src/app/page.tsx`
- Create: `caigen-tan-app/src/types/index.ts`
- Create: `caigen-tan-app/.env.local`

- [ ] **Step 1: Create Next.js project**

```bash
cd /c/Users/racwang/hoopy
npx create-next-app@latest caigen-tan-app --typescript --tailwind --app --src-dir --no-eslint --import-alias "@/*"
```

When prompted, accept defaults. This scaffolds the project with TypeScript, Tailwind, and App Router.

- [ ] **Step 2: Define shared types**

Create `src/types/index.ts`:
```typescript
export interface Quote {
  id: number;
  collection: "前集" | "后集";
  original: string;
  interpretation: string;
  source: string;
}

export interface Favorite {
  quote: Quote;
  savedAt: string; // ISO date string
}
```

- [ ] **Step 3: Set up environment variables**

Create `.env.local`:
```
OPENAI_API_KEY=your-key-here
```

Add `.env.local` to `.gitignore` (should already be there from create-next-app).

- [ ] **Step 4: Install additional dependencies**

```bash
cd caigen-tan-app
npm install html2canvas openai
```

- [ ] **Step 5: Verify the dev server starts**

```bash
npm run dev
```

Expected: Server starts on http://localhost:3000, default Next.js page loads.

- [ ] **Step 6: Commit**

```bash
git init
git add -A
git commit -m "feat: scaffold next.js project with typescript and tailwind"
```

---

## Task 2: Font Setup and Root Layout

**Files:**
- Create: `caigen-tan-app/public/fonts/` (font files)
- Modify: `caigen-tan-app/src/app/layout.tsx`
- Modify: `caigen-tan-app/tailwind.config.ts`

- [ ] **Step 1: Download LXGW WenKai font**

Download LXGW WenKai (霞鹜文楷) woff2 files for self-hosting. This is the primary font for quote display — elegant Chinese serif with good web performance.

```bash
mkdir -p public/fonts
curl -L -o public/fonts/LXGWWenKai-Regular.woff2 "https://cdn.jsdelivr.net/npm/lxgw-wenkai-webfont@1.7.0/fonts/LXGWWenKai-Regular.woff2"
curl -L -o public/fonts/LXGWWenKai-Bold.woff2 "https://cdn.jsdelivr.net/npm/lxgw-wenkai-webfont@1.7.0/fonts/LXGWWenKai-Bold.woff2"
```

- [ ] **Step 2: Configure fonts in layout.tsx**

Update `src/app/layout.tsx` to load LXGW WenKai via `@font-face` and set up the root layout with proper metadata:

```typescript
import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "菜根谭 — 说说你的心情",
  description: "输入你的心情，从菜根谭里找到一句说给你听的话",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#1a1a1a",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-stone-50 text-stone-900 antialiased">
        {children}
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Add font-face declarations to globals.css**

Add to `src/app/globals.css` (after the Tailwind directives):

```css
@font-face {
  font-family: "LXGW WenKai";
  src: url("/fonts/LXGWWenKai-Regular.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "LXGW WenKai";
  src: url("/fonts/LXGWWenKai-Bold.woff2") format("woff2");
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
```

- [ ] **Step 4: Extend Tailwind config with custom font family**

Update `tailwind.config.ts`:
```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        wenkai: ['"LXGW WenKai"', "serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 5: Verify fonts load correctly**

Update `src/app/page.tsx` temporarily to test:
```typescript
export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <p className="font-wenkai text-2xl">栖守道德者，寂寞一时</p>
    </main>
  );
}
```

Run `npm run dev`, verify the text renders in LXGW WenKai font.

- [ ] **Step 6: Commit**

```bash
git add public/fonts src/app/layout.tsx src/app/globals.css src/app/page.tsx tailwind.config.ts
git commit -m "feat: set up LXGW WenKai font and root layout"
```

---

## Task 3: Quote Data Layer

**Files:**
- Create: `caigen-tan-app/src/lib/quotes.ts`

**Depends on:** Task 0 (caigen-tan.json must exist)

- [ ] **Step 1: Create the quote data access module**

Create `src/lib/quotes.ts`:
```typescript
import quotesData from "@/data/caigen-tan.json";
import type { Quote } from "@/types";

const quotes: Quote[] = quotesData as Quote[];

export function getAllQuotes(): Quote[] {
  return quotes;
}

export function getRandomQuote(): Quote {
  const index = Math.floor(Math.random() * quotes.length);
  return quotes[index];
}

export function getQuoteById(id: number): Quote | undefined {
  return quotes.find((q) => q.id === id);
}

export function getQuotesFormatted(): string {
  return quotes
    .map((q) => `[ID:${q.id}] ${q.original}`)
    .join("\n");
}
```

- [ ] **Step 2: Verify the module loads data correctly**

```bash
npx tsx -e "
import { getAllQuotes, getRandomQuote } from './src/lib/quotes';
console.log('Total quotes:', getAllQuotes().length);
console.log('Random quote:', getRandomQuote().original.slice(0, 30) + '...');
"
```

Expected: prints total count and a random quote excerpt.

- [ ] **Step 3: Commit**

```bash
git add src/lib/quotes.ts
git commit -m "feat: add quote data access layer"
```

---

## Task 4: AI Matching API Route

**Files:**
- Create: `caigen-tan-app/src/app/api/match/route.ts`

- [ ] **Step 1: Create the API route**

Create `src/app/api/match/route.ts`:
```typescript
import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";
import { getQuotesFormatted, getQuoteById } from "@/lib/quotes";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function POST(request: NextRequest) {
  try {
    const { mood } = await request.json();

    if (!mood || typeof mood !== "string" || mood.trim().length === 0) {
      return NextResponse.json(
        { error: "请输入你的心情" },
        { status: 400 }
      );
    }

    // Limit input length to prevent excessive API costs
    if (mood.length > 500) {
      return NextResponse.json(
        { error: "输入内容过长" },
        { status: 400 }
      );
    }

    const quotesContext = getQuotesFormatted();

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      temperature: 0.7,
      messages: [
        {
          role: "system",
          content: `你是一位深谙菜根谭智慧的哲人。用户会描述自己当前的心情或处境，你需要从以下菜根谭语录中选出最契合的一句。

要求：
1. 理解用户情绪的深层含义，不要只做表面关键词匹配
2. 选择最能给用户启发或慰藉的语录
3. 只返回一个 JSON 对象，格式为 {"id": <数字>}
4. 不要返回任何其他内容

语录列表：
${quotesContext}`,
        },
        {
          role: "user",
          content: mood,
        },
      ],
    });

    const rawContent = completion.choices[0]?.message?.content?.trim();
    if (!rawContent) {
      return NextResponse.json(
        { error: "AI 未返回结果" },
        { status: 500 }
      );
    }

    // Strip markdown code fences if present
    const content = rawContent.replace(/^```(?:json)?\s*|\s*```$/g, "");
    const parsed = JSON.parse(content);
    const quote = getQuoteById(parsed.id);

    if (!quote) {
      return NextResponse.json(
        { error: "未找到匹配的语录" },
        { status: 500 }
      );
    }

    return NextResponse.json({ quote });
  } catch (error) {
    console.error("Match API error:", error);
    return NextResponse.json(
      { error: "匹配失败，请稍后再试" },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 2: Test the API route with curl**

Start the dev server, then test:
```bash
curl -X POST http://localhost:3000/api/match \
  -H "Content-Type: application/json" \
  -d '{"mood": "今天工作压力很大，很疲惫"}'
```

Expected: JSON response with a matched quote object.

- [ ] **Step 3: Test error handling**

```bash
# Empty mood
curl -X POST http://localhost:3000/api/match \
  -H "Content-Type: application/json" \
  -d '{"mood": ""}'
```

Expected: 400 response with error message.

- [ ] **Step 4: Commit**

```bash
git add src/app/api/match/route.ts
git commit -m "feat: add AI mood matching API route"
```

---

## Task 5: Core UI Components — Header and MoodInput

**Files:**
- Create: `caigen-tan-app/src/components/Header.tsx`
- Create: `caigen-tan-app/src/components/MoodInput.tsx`

**Note:** Use @ui-ux-pro-max skill when building these components. It will auto-generate a design system based on the product type.

- [ ] **Step 1: Create Header component**

Create `src/components/Header.tsx`:
```typescript
"use client";

export default function Header() {
  return (
    <header className="pt-12 pb-6 text-center">
      <h1 className="font-wenkai text-3xl font-bold tracking-wide text-stone-800">
        菜根谭
      </h1>
      <p className="mt-2 text-sm text-stone-400">
        说说你的心情，听一句古人的话
      </p>
    </header>
  );
}
```

- [ ] **Step 2: Create MoodInput component**

Create `src/components/MoodInput.tsx`:
```typescript
"use client";

import { useState } from "react";

interface MoodInputProps {
  onSubmit: (mood: string) => void;
  isLoading: boolean;
}

export default function MoodInput({ onSubmit, isLoading }: MoodInputProps) {
  const [mood, setMood] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mood.trim() && !isLoading) {
      onSubmit(mood.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-md px-6">
      <textarea
        value={mood}
        onChange={(e) => setMood(e.target.value)}
        placeholder="说说你现在的心情…"
        rows={3}
        className="w-full resize-none rounded-xl border border-stone-200 bg-white px-4 py-3 font-wenkai text-base text-stone-700 placeholder-stone-300 shadow-sm transition focus:border-stone-400 focus:outline-none focus:ring-1 focus:ring-stone-300"
      />
      <button
        type="submit"
        disabled={!mood.trim() || isLoading}
        className="mt-3 w-full rounded-xl bg-stone-800 py-3 text-sm font-medium text-white transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {isLoading ? "正在寻找…" : "寻一句话"}
      </button>
    </form>
  );
}
```

- [ ] **Step 3: Verify components render**

Update `src/app/page.tsx`:
```typescript
import Header from "@/components/Header";

export default function Home() {
  return (
    <main className="min-h-screen">
      <Header />
      <p className="text-center text-stone-400 text-sm">Components working</p>
    </main>
  );
}
```

Run `npm run dev`, check that the header renders correctly.

- [ ] **Step 4: Commit**

```bash
git add src/components/Header.tsx src/components/MoodInput.tsx src/app/page.tsx
git commit -m "feat: add Header and MoodInput components"
```

---

## Task 6: QuoteCard and ActionButtons Components

**Files:**
- Create: `caigen-tan-app/src/components/QuoteCard.tsx`
- Create: `caigen-tan-app/src/components/ActionButtons.tsx`

- [ ] **Step 1: Create QuoteCard component**

Create `src/components/QuoteCard.tsx`:
```typescript
"use client";

import type { Quote } from "@/types";

interface QuoteCardProps {
  quote: Quote;
  isVisible: boolean;
}

export default function QuoteCard({ quote, isVisible }: QuoteCardProps) {
  return (
    <div
      className={`mx-auto max-w-md px-6 transition-opacity duration-500 ${
        isVisible ? "opacity-100" : "opacity-0"
      }`}
    >
      <div className="rounded-2xl bg-white p-8 shadow-sm">
        <blockquote className="font-wenkai text-lg leading-relaxed text-stone-800 tracking-wide">
          {quote.original}
        </blockquote>
        <p className="mt-4 text-sm leading-relaxed text-stone-500">
          {quote.interpretation}
        </p>
        <p className="mt-4 text-xs text-stone-300">
          —— {quote.source}
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create ActionButtons component**

Create `src/components/ActionButtons.tsx`:
```typescript
"use client";

interface ActionButtonsProps {
  onSave: () => void;
  onShare: () => void;
  isSaved: boolean;
}

export default function ActionButtons({
  onSave,
  onShare,
  isSaved,
}: ActionButtonsProps) {
  return (
    <div className="mx-auto mt-4 flex max-w-md justify-center gap-4 px-6">
      <button
        onClick={onSave}
        className={`rounded-lg px-5 py-2 text-sm transition ${
          isSaved
            ? "bg-stone-100 text-stone-400 cursor-default"
            : "bg-stone-100 text-stone-600 hover:bg-stone-200"
        }`}
        disabled={isSaved}
      >
        {isSaved ? "已收藏" : "收藏"}
      </button>
      <button
        onClick={onShare}
        className="rounded-lg bg-stone-100 px-5 py-2 text-sm text-stone-600 transition hover:bg-stone-200"
      >
        生成分享图
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/QuoteCard.tsx src/components/ActionButtons.tsx
git commit -m "feat: add QuoteCard and ActionButtons components"
```

---

## Task 7: Favorites Module and Component

**Files:**
- Create: `caigen-tan-app/src/lib/favorites.ts`
- Create: `caigen-tan-app/src/components/Favorites.tsx`

- [ ] **Step 1: Create favorites localStorage helpers**

Create `src/lib/favorites.ts`:
```typescript
import type { Quote, Favorite } from "@/types";

const STORAGE_KEY = "caigen-tan-favorites";

export function getFavorites(): Favorite[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : [];
}

export function addFavorite(quote: Quote): Favorite[] {
  const favorites = getFavorites();
  if (favorites.some((f) => f.quote.id === quote.id)) return favorites;
  const updated = [
    { quote, savedAt: new Date().toISOString() },
    ...favorites,
  ];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}

export function removeFavorite(quoteId: number): Favorite[] {
  const favorites = getFavorites().filter((f) => f.quote.id !== quoteId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites));
  return favorites;
}

export function isFavorited(quoteId: number): boolean {
  return getFavorites().some((f) => f.quote.id === quoteId);
}
```

- [ ] **Step 2: Create Favorites component**

Create `src/components/Favorites.tsx`:
```typescript
"use client";

import { useState } from "react";
import type { Favorite } from "@/types";

interface FavoritesProps {
  favorites: Favorite[];
  onRemove: (quoteId: number) => void;
  onShare: (favorite: Favorite) => void;
}

export default function Favorites({
  favorites,
  onRemove,
  onShare,
}: FavoritesProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (favorites.length === 0) return null;

  return (
    <section className="mx-auto mt-12 max-w-md px-6 pb-12">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between text-sm text-stone-400 transition hover:text-stone-600"
      >
        <span>收藏 ({favorites.length})</span>
        <span className={`transition-transform ${isOpen ? "rotate-180" : ""}`}>
          ▾
        </span>
      </button>

      {isOpen && (
        <div className="mt-4 space-y-3">
          {favorites.map((fav) => (
            <div
              key={fav.quote.id}
              className="rounded-xl bg-white p-4 shadow-sm"
            >
              <p className="font-wenkai text-sm leading-relaxed text-stone-700">
                {fav.quote.original}
              </p>
              <div className="mt-2 flex justify-end gap-2">
                <button
                  onClick={() => onShare(fav)}
                  className="text-xs text-stone-400 hover:text-stone-600"
                >
                  分享
                </button>
                <button
                  onClick={() => onRemove(fav.quote.id)}
                  className="text-xs text-stone-400 hover:text-red-400"
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add src/lib/favorites.ts src/components/Favorites.tsx
git commit -m "feat: add favorites storage and component"
```

---

## Task 8: Share Image Generation

**Files:**
- Create: `caigen-tan-app/src/lib/share.ts`
- Create: `caigen-tan-app/src/components/ShareTemplate.tsx`
- Create: `caigen-tan-app/src/components/SharePreview.tsx`

- [ ] **Step 1: Create ShareTemplate component**

This is the card that gets rendered to an image. 3:4 aspect ratio. Three template styles.

Create `src/components/ShareTemplate.tsx`:
```typescript
"use client";

import { forwardRef } from "react";
import type { Quote } from "@/types";

interface ShareTemplateProps {
  quote: Quote;
  template: "ink" | "minimal" | "neo";
}

const templateStyles = {
  ink: {
    bg: "bg-amber-50",
    text: "text-stone-800",
    sub: "text-stone-500",
    source: "text-stone-400",
    accent: "border-l-2 border-stone-300 pl-4",
  },
  minimal: {
    bg: "bg-stone-900",
    text: "text-stone-100",
    sub: "text-stone-400",
    source: "text-stone-500",
    accent: "",
  },
  neo: {
    bg: "bg-gradient-to-br from-emerald-50 to-amber-50",
    text: "text-stone-800",
    sub: "text-stone-500",
    source: "text-stone-400",
    accent: "",
  },
};

const ShareTemplate = forwardRef<HTMLDivElement, ShareTemplateProps>(
  ({ quote, template }, ref) => {
    const styles = templateStyles[template];

    return (
      <div
        ref={ref}
        className={`flex flex-col justify-between ${styles.bg} p-10`}
        style={{ width: 600, height: 800 }}
      >
        <div className="flex-1 flex flex-col justify-center">
          <div className={styles.accent}>
            <p
              className={`font-wenkai text-2xl leading-loose tracking-widest ${styles.text}`}
            >
              {quote.original}
            </p>
          </div>
          <p className={`mt-6 text-sm leading-relaxed ${styles.sub}`}>
            {quote.interpretation}
          </p>
        </div>

        <div className="flex items-end justify-between">
          <p className={`text-xs ${styles.source}`}>—— {quote.source}</p>
          <p className={`text-xs ${styles.source}`}>菜根谭</p>
        </div>
      </div>
    );
  }
);

ShareTemplate.displayName = "ShareTemplate";

export default ShareTemplate;
```

- [ ] **Step 2: Create share image generation utility**

Create `src/lib/share.ts`:
```typescript
import html2canvas from "html2canvas";

export async function generateShareImage(
  element: HTMLElement
): Promise<string> {
  // Wait for custom fonts to load before capturing
  await document.fonts.ready;
  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    backgroundColor: null,
  });
  return canvas.toDataURL("image/png");
}

export function downloadImage(dataUrl: string, filename: string) {
  const link = document.createElement("a");
  link.href = dataUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
```

- [ ] **Step 3: Create SharePreview modal**

Create `src/components/SharePreview.tsx`:
```typescript
"use client";

import { useRef, useState } from "react";
import type { Quote } from "@/types";
import ShareTemplate from "./ShareTemplate";
import { generateShareImage, downloadImage } from "@/lib/share";

interface SharePreviewProps {
  quote: Quote;
  onClose: () => void;
}

const templates = ["ink", "minimal", "neo"] as const;
const templateNames = { ink: "水墨", minimal: "极简", neo: "新中式" };

export default function SharePreview({ quote, onClose }: SharePreviewProps) {
  const [activeTemplate, setActiveTemplate] =
    useState<(typeof templates)[number]>("ink");
  const [isGenerating, setIsGenerating] = useState(false);
  const templateRef = useRef<HTMLDivElement>(null);

  const handleSave = async () => {
    if (!templateRef.current) return;
    setIsGenerating(true);
    try {
      const dataUrl = await generateShareImage(templateRef.current);
      downloadImage(dataUrl, `caigen-tan-${quote.id}.png`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6">
        {/* Template switcher */}
        <div className="mb-4 flex justify-center gap-2">
          {templates.map((t) => (
            <button
              key={t}
              onClick={() => setActiveTemplate(t)}
              className={`rounded-lg px-3 py-1.5 text-xs transition ${
                activeTemplate === t
                  ? "bg-stone-800 text-white"
                  : "bg-stone-100 text-stone-500 hover:bg-stone-200"
              }`}
            >
              {templateNames[t]}
            </button>
          ))}
        </div>

        {/* Preview */}
        <div className="flex justify-center overflow-hidden rounded-xl">
          <div style={{ transform: "scale(0.5)", transformOrigin: "top center" }}>
            <ShareTemplate
              ref={templateRef}
              quote={quote}
              template={activeTemplate}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="mt-4 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-xl bg-stone-100 py-2.5 text-sm text-stone-500 transition hover:bg-stone-200"
          >
            关闭
          </button>
          <button
            onClick={handleSave}
            disabled={isGenerating}
            className="flex-1 rounded-xl bg-stone-800 py-2.5 text-sm text-white transition hover:bg-stone-700 disabled:opacity-40"
          >
            {isGenerating ? "生成中…" : "保存图片"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add src/components/ShareTemplate.tsx src/components/SharePreview.tsx src/lib/share.ts
git commit -m "feat: add share image templates and generation"
```

---

## Task 9: Main Page Assembly

**Files:**
- Modify: `caigen-tan-app/src/app/page.tsx`

This task wires everything together into the final page.

- [ ] **Step 1: Build the main page**

Replace `src/app/page.tsx` with the full page that composes all components:

```typescript
"use client";

import { useState, useEffect } from "react";
import type { Quote, Favorite } from "@/types";
import Header from "@/components/Header";
import MoodInput from "@/components/MoodInput";
import QuoteCard from "@/components/QuoteCard";
import ActionButtons from "@/components/ActionButtons";
import Favorites from "@/components/Favorites";
import SharePreview from "@/components/SharePreview";
import { getRandomQuote } from "@/lib/quotes";
import {
  getFavorites,
  addFavorite,
  removeFavorite,
  isFavorited,
} from "@/lib/favorites";

export default function Home() {
  const [quote, setQuote] = useState<Quote | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [saved, setSaved] = useState(false);
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [shareQuote, setShareQuote] = useState<Quote | null>(null);

  // Load initial random quote and favorites
  useEffect(() => {
    const initial = getRandomQuote();
    setQuote(initial);
    setSaved(isFavorited(initial.id));
    setIsVisible(true);
    setFavorites(getFavorites());
  }, []);

  const handleMoodSubmit = async (mood: string) => {
    setIsLoading(true);
    setIsVisible(false);

    try {
      const res = await fetch("/api/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mood }),
      });

      const data = await res.json();

      if (data.quote) {
        // Small delay for fade-out to complete
        setTimeout(() => {
          setQuote(data.quote);
          setSaved(isFavorited(data.quote.id));
          setIsVisible(true);
        }, 300);
      }
    } catch (error) {
      console.error("Failed to match:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = () => {
    if (quote) {
      const updated = addFavorite(quote);
      setFavorites(updated);
      setSaved(true);
    }
  };

  const handleRemoveFavorite = (quoteId: number) => {
    const updated = removeFavorite(quoteId);
    setFavorites(updated);
    if (quote?.id === quoteId) setSaved(false);
  };

  return (
    <main className="min-h-screen">
      <Header />
      <MoodInput onSubmit={handleMoodSubmit} isLoading={isLoading} />

      {quote && (
        <>
          <div className="mt-8">
            <QuoteCard quote={quote} isVisible={isVisible} />
          </div>
          {isVisible && (
            <ActionButtons
              onSave={handleSave}
              onShare={() => setShareQuote(quote)}
              isSaved={saved}
            />
          )}
        </>
      )}

      <Favorites
        favorites={favorites}
        onRemove={handleRemoveFavorite}
        onShare={(fav) => setShareQuote(fav.quote)}
      />

      {shareQuote && (
        <SharePreview
          quote={shareQuote}
          onClose={() => setShareQuote(null)}
        />
      )}
    </main>
  );
}
```

- [ ] **Step 2: Verify the full flow**

Run `npm run dev` and test:
1. Page loads with a random quote ✓
2. Type a mood and submit → new quote appears with fade animation ✓
3. Click "收藏" → button changes to "已收藏" ✓
4. Click "生成分享图" → modal opens with template switcher ✓
5. Switch templates and save image ✓
6. Favorites section shows saved quotes ✓

- [ ] **Step 3: Commit**

```bash
git add src/app/page.tsx
git commit -m "feat: assemble main page with all components"
```

---

## Task 10: PWA Configuration

**Files:**
- Create: `caigen-tan-app/public/manifest.json`
- Create: `caigen-tan-app/public/sw.js`
- Modify: `caigen-tan-app/src/app/layout.tsx`

- [ ] **Step 1: Create PWA manifest**

Create `public/manifest.json`:
```json
{
  "name": "菜根谭",
  "short_name": "菜根谭",
  "description": "输入你的心情，从菜根谭里找到一句说给你听的话",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#fafaf9",
  "theme_color": "#1a1a1a",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

- [ ] **Step 2: Create Service Worker**

Create `public/sw.js`:
```javascript
const CACHE_NAME = "caigen-tan-v1";
const STATIC_ASSETS = ["/", "/fonts/LXGWWenKai-Regular.woff2", "/fonts/LXGWWenKai-Bold.woff2"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener("fetch", (event) => {
  // Only cache GET requests for static assets
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request);
    })
  );
});
```

- [ ] **Step 3: Create placeholder PWA icons**

```bash
mkdir -p public/icons
```

Generate simple placeholder icons (replace with designed icons later):
```bash
npx @aspect-build/rules_js//js/private:gen-pwa-icons || echo "Create 192x192 and 512x512 PNG icons manually in public/icons/"
```

For now, create simple colored square PNGs at `public/icons/icon-192.png` and `public/icons/icon-512.png`. These will be replaced with properly designed icons.

- [ ] **Step 4: Register Service Worker in layout**

Add to `src/app/layout.tsx`, inside the `<head>` area (via metadata):

Update the metadata export:
```typescript
export const metadata: Metadata = {
  title: "菜根谭 — 说说你的心情",
  description: "输入你的心情，从菜根谭里找到一句说给你听的话",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "菜根谭",
  },
};
```

Add a client component or script to register the service worker. Add to the bottom of `layout.tsx` body:
```typescript
<script
  dangerouslySetInnerHTML={{
    __html: `
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js');
      }
    `,
  }}
/>
```

- [ ] **Step 5: Verify PWA**

Run `npm run build && npm run start`, open in Chrome:
1. Open DevTools → Application → Manifest → verify manifest loads
2. Application → Service Workers → verify SW is registered
3. Lighthouse → check PWA score

- [ ] **Step 6: Commit**

```bash
git add public/manifest.json public/sw.js public/icons src/app/layout.tsx
git commit -m "feat: add PWA manifest, service worker, and icons"
```

---

## Task 11: Polish and Deploy

**Files:**
- Modify: various files for final polish

- [ ] **Step 1: Add loading state and error handling to the page**

In `page.tsx`, add user-visible error handling:
- If the API call fails, show a toast or message like "匹配失败，请稍后再试"
- Add a subtle loading animation/skeleton while waiting for AI response

- [ ] **Step 2: Mobile responsiveness check**

Open dev tools, test at these viewports:
- iPhone SE (375px)
- iPhone 14 (390px)
- iPad (768px)
- Desktop (1440px)

Adjust spacing/sizing as needed. The design should feel best on mobile (primary use case).

- [ ] **Step 3: Run production build**

```bash
npm run build
```

Fix any TypeScript errors or build warnings.

- [ ] **Step 4: Deploy to Vercel**

```bash
npx vercel --prod
```

Or connect the GitHub repo to Vercel for auto-deploy. Set the `OPENAI_API_KEY` environment variable in Vercel dashboard.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: polish UI and prepare for production"
```
