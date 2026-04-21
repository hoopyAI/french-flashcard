# French-Chinese Flashcard WeChat Mini Program

## Overview

A minimalist WeChat Mini Program for memorizing French textbook passages using flashcards. Each card displays one sentence pair (Chinese front / French back). Cards are organized by book and lesson.

## Tech Stack

- **Platform:** Native WeChat Mini Program (WXML + WXSS + JS)
- **Data:** Static JSON embedded in code
- **Storage:** `wx.setStorageSync` for learning progress

## Pages

### 1. Home — Book Catalog (`/pages/index/`)
- Grid/list of books, each showing title and icon (emoji)
- Tap a book → navigate to its lesson list

### 2. Lesson List (`/pages/lessons/`)
- List of lessons for the selected book
- Each lesson shows: lesson number, title, progress (e.g., "3/12 已掌握")
- Tap a lesson → navigate to card view

### 3. Card View (`/pages/cards/`)
- Full-screen flashcard, one sentence per card
- Default shows Chinese (front face)
- Tap card → 3D Y-axis flip animation (~0.4s) to French (back face)
- Tap again → flip back to Chinese
- Swipe left/right to switch cards (via `swiper` component)
- Switching cards auto-resets to front (Chinese) face
- Bottom buttons: 「✗ 未掌握」and「✓ 已掌握」— tapping advances to next card
- Top: progress indicator "3/12"
- Top toggle: 「全部 / 仅未掌握」filter (default: all)

## Data Structure

### Book/Lesson/Card Data (`data/books.js` — JS module export)

```json
{
  "books": [
    {
      "id": "book1",
      "title": "走遍法国 A1",
      "icon": "📘",
      "lessons": [
        {
          "id": "lesson1",
          "title": "第一课 你好",
          "cards": [
            {
              "id": "card1",
              "front": "你好，你叫什么名字？",
              "back": "Bonjour, comment tu t'appelles ?"
            }
          ]
        }
      ]
    }
  ]
}
```

### Progress Storage (wx.setStorageSync)

```json
{
  "book1-lesson1": {
    "mastered": ["card1", "card3"],
    "lastVisited": "card2"
  }
}
```

Key format: `{bookId}-{lessonId}`. Stores mastered card IDs and last visited card for resume.

## Visual Style — Excalidraw-inspired, Cool Blue

### Color Palette
- **Card front:** White background (`#fff`), dark text (`#1e1e1e`)
- **Card back:** Light blue-gray background (`#f0f4f8`), blue text (`#364fc7`)
- **Card border:** `2.5px solid #364fc7`, border-radius `16px`
- **Card shadow:** `4px 4px 0 rgba(54,79,199,0.2)` (offset shadow, hand-drawn feel)
- **Page background:** `#f8f9fc` (very light blue-gray)

### Typography
- Hand-drawn style font: system cursive fallback (`'Comic Sans MS', 'Segoe Print', cursive`)
- Card text: `20px`, centered, `line-height: 1.8`

### Design Principles
- Cards show ONLY the sentence — no labels, no decorations, no extra text
- Excalidraw-inspired: slightly rough borders, offset shadows, handwritten font
- Warm and soft overall feel despite cool blue palette
- Minimal UI chrome — content first

## Interaction Details

### Flip Animation
- CSS 3D transform on Y-axis
- Duration: ~0.4s ease-in-out
- Front and back faces use `backface-visibility: hidden`

### Card Navigation
- WeChat `swiper` component for left/right swipe
- On slide change: auto-reset card to front face (Chinese)
- Circular navigation disabled — stop at first/last card

### Mastery Tracking
- Two buttons below card: ✗ (not mastered) / ✓ (mastered)
- Tapping either button: save state to local storage, auto-advance to next card
- On last card: show a brief "完成！" toast, then navigate back to lesson list
- Progress persists across sessions via `wx.setStorageSync`

### Filter Mode
- Toggle at top of card page: "全部" / "仅未掌握"
- Default: show all cards
- When filtering, re-index the swiper to only show unmastered cards

## Project Structure

```
french-flashcard/
├── app.js
├── app.json
├── app.wxss                  # Global styles (Excalidraw theme)
├── data/
│   └── books.js              # All book/lesson/card data
├── utils/
│   └── storage.js            # Progress read/write helpers
└── pages/
    ├── index/                # Book catalog
    │   ├── index.wxml
    │   ├── index.wxss
    │   └── index.js
    ├── lessons/              # Lesson list
    │   ├── lessons.wxml
    │   ├── lessons.wxss
    │   └── lessons.js
    └── cards/                # Flashcard view
        ├── cards.wxml
        ├── cards.wxss
        └── cards.js
```

## Out of Scope

- Cloud data sync
- User accounts / login
- Spaced repetition algorithm
- Audio pronunciation
- Multi-platform (WeChat only)
