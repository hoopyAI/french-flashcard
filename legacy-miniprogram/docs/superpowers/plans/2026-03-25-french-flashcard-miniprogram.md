# French-Chinese Flashcard Mini Program Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimalist WeChat Mini Program for memorizing French textbook passages with flip cards, organized by book and lesson.

**Architecture:** Three-page native mini program (catalog → lessons → cards). Static data in JS module, progress in wx local storage. Excalidraw-inspired blue visual theme.

**Tech Stack:** Native WeChat Mini Program (WXML + WXSS + JS), no external dependencies.

**Spec:** `docs/superpowers/specs/2026-03-25-french-flashcard-miniprogram-design.md`

**Note on testing:** WeChat Mini Programs lack a standard unit test framework. Each task includes manual verification steps to run in WeChat DevTools simulator. Open the project in DevTools after each task to verify.

---

## File Structure

```
french-flashcard/
├── app.js                    # App lifecycle (empty for now)
├── app.json                  # App config: pages, window, navigation bar
├── app.wxss                  # Global Excalidraw theme styles
├── project.config.json       # DevTools project config
├── data/
│   └── books.js              # All book/lesson/card data (module.exports)
├── utils/
│   └── storage.js            # Progress read/write/toggle helpers
└── pages/
    ├── index/                # Book catalog
    │   ├── index.wxml
    │   ├── index.wxss
    │   └── index.js
    ├── lessons/              # Lesson list for a book
    │   ├── lessons.wxml
    │   ├── lessons.wxss
    │   └── lessons.js
    └── cards/                # Flashcard view
        ├── cards.wxml
        ├── cards.wxss
        └── cards.js
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `french-flashcard/app.js`
- Create: `french-flashcard/app.json`
- Create: `french-flashcard/app.wxss`
- Create: `french-flashcard/project.config.json`

- [ ] **Step 1: Create project directory**

```bash
mkdir -p french-flashcard/pages/index french-flashcard/pages/lessons french-flashcard/pages/cards french-flashcard/data french-flashcard/utils
```

- [ ] **Step 2: Create `app.json`**

```json
{
  "pages": [
    "pages/index/index",
    "pages/lessons/lessons",
    "pages/cards/cards"
  ],
  "window": {
    "backgroundTextStyle": "light",
    "navigationBarBackgroundColor": "#f8f9fc",
    "navigationBarTitleText": "课文背诵",
    "navigationBarTextStyle": "black",
    "backgroundColor": "#f8f9fc"
  }
}
```

- [ ] **Step 3: Create `app.js`**

```js
App({})
```

- [ ] **Step 4: Create `app.wxss` — Global Excalidraw theme**

Global styles: page background, hand-drawn font stack, common card styling, button styles. All pages inherit these.

```css
page {
  background-color: #f8f9fc;
  font-family: 'Comic Sans MS', 'Segoe Print', 'Ma Shan Zheng', cursive;
  color: #1e1e1e;
  box-sizing: border-box;
}

/* Excalidraw card base */
.card {
  background: #fff;
  border: 2.5px solid #364fc7;
  border-radius: 16px;
  box-shadow: 4px 4px 0 rgba(54, 79, 199, 0.2);
}

/* Primary action button */
.btn-primary {
  background: #364fc7;
  color: #fff;
  border: 2.5px solid #364fc7;
  border-radius: 12px;
  box-shadow: 3px 3px 0 rgba(54, 79, 199, 0.2);
  padding: 12rpx 32rpx;
  font-family: inherit;
  font-size: 28rpx;
}

/* Secondary / outline button */
.btn-outline {
  background: #fff;
  color: #364fc7;
  border: 2.5px solid #364fc7;
  border-radius: 12px;
  box-shadow: 3px 3px 0 rgba(54, 79, 199, 0.2);
  padding: 12rpx 32rpx;
  font-family: inherit;
  font-size: 28rpx;
}
```

- [ ] **Step 5: Create `project.config.json`**

```json
{
  "description": "French-Chinese Flashcard App",
  "packOptions": {
    "ignore": []
  },
  "setting": {
    "urlCheck": false,
    "es6": true,
    "enhance": true,
    "postcss": true,
    "minified": true
  },
  "compileType": "miniprogram",
  "appid": "touristappid",
  "projectname": "french-flashcard",
  "condition": {}
}
```

- [ ] **Step 6: Create placeholder pages**

Create minimal placeholder files so the app compiles:

`pages/index/index.wxml`:
```html
<view class="container">
  <text>书目录</text>
</view>
```

`pages/index/index.wxss`:
```css
.container { padding: 40rpx; }
```

`pages/index/index.js`:
```js
Page({})
```

Repeat the same pattern for `pages/lessons/` and `pages/cards/` (with text "课文列表" and "卡片" respectively).

- [ ] **Step 7: Verify in DevTools**

Open `french-flashcard/` in WeChat DevTools. Expected: app loads, shows "书目录" text on light blue-gray background with hand-drawn font.

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "feat: scaffold mini program project with Excalidraw theme"
```

---

### Task 2: Data Layer

**Files:**
- Create: `french-flashcard/data/books.js`
- Create: `french-flashcard/utils/storage.js`

- [ ] **Step 1: Create `data/books.js` with sample data**

Include at least 2 books, each with 2+ lessons, each lesson with 3-5 cards. Use real French-Chinese sentence pairs.

```js
module.exports = {
  books: [
    {
      id: 'reflets1',
      title: '走遍法国 1',
      icon: '📘',
      lessons: [
        {
          id: 'l1',
          title: '第1课 你好',
          cards: [
            { id: 'c1', front: '你好！', back: 'Bonjour !' },
            { id: 'c2', front: '你好，你叫什么名字？', back: 'Bonjour, comment tu t\'appelles ?' },
            { id: 'c3', front: '我叫皮埃尔。', back: 'Je m\'appelle Pierre.' },
            { id: 'c4', front: '你好吗？', back: 'Comment vas-tu ?' },
            { id: 'c5', front: '我很好，谢谢。', back: 'Je vais bien, merci.' }
          ]
        },
        {
          id: 'l2',
          title: '第2课 在咖啡馆',
          cards: [
            { id: 'c1', front: '请给我一杯咖啡。', back: 'Un café, s\'il vous plaît.' },
            { id: 'c2', front: '多少钱？', back: 'C\'est combien ?' },
            { id: 'c3', front: '谢谢您。', back: 'Merci beaucoup.' },
            { id: 'c4', front: '不客气。', back: 'De rien.' }
          ]
        }
      ]
    },
    {
      id: 'reflets2',
      title: '走遍法国 2',
      icon: '📗',
      lessons: [
        {
          id: 'l1',
          title: '第1课 重逢',
          cards: [
            { id: 'c1', front: '好久不见！', back: 'Ça fait longtemps !' },
            { id: 'c2', front: '你最近怎么样？', back: 'Comment vas-tu ces derniers temps ?' },
            { id: 'c3', front: '一切都好。', back: 'Tout va bien.' }
          ]
        }
      ]
    }
  ]
}
```

- [ ] **Step 2: Create `utils/storage.js`**

Four helper functions: `getProgress`, `saveProgress`, `toggleMastered`, `isMastered`.

```js
const STORAGE_KEY_PREFIX = 'progress_'

function _getKey(bookId, lessonId) {
  return STORAGE_KEY_PREFIX + bookId + '-' + lessonId
}

/** Get progress for a lesson. Returns { mastered: [], lastVisited: '' } */
function getProgress(bookId, lessonId) {
  var key = _getKey(bookId, lessonId)
  var data = wx.getStorageSync(key)
  if (!data) {
    return { mastered: [], lastVisited: '' }
  }
  return data
}

/** Save full progress object for a lesson */
function saveProgress(bookId, lessonId, progress) {
  var key = _getKey(bookId, lessonId)
  wx.setStorageSync(key, progress)
}

/** Set mastered status for a card. `mastered` = desired state (true=mastered). */
function setMastered(bookId, lessonId, cardId, mastered) {
  var progress = getProgress(bookId, lessonId)
  if (mastered) {
    // Add to mastered
    if (progress.mastered.indexOf(cardId) === -1) {
      progress.mastered.push(cardId)
    }
  } else {
    // Remove from mastered
    progress.mastered = progress.mastered.filter(function(id) { return id !== cardId })
  }
  saveProgress(bookId, lessonId, progress)
  return mastered
}

/** Check if a specific card is mastered */
function isMastered(bookId, lessonId, cardId) {
  var progress = getProgress(bookId, lessonId)
  return progress.mastered.indexOf(cardId) !== -1
}

/** Get mastered count for a lesson */
function getMasteredCount(bookId, lessonId) {
  var progress = getProgress(bookId, lessonId)
  return progress.mastered.length
}

module.exports = {
  getProgress: getProgress,
  saveProgress: saveProgress,
  setMastered: setMastered,
  isMastered: isMastered,
  getMasteredCount: getMasteredCount
}
```

- [ ] **Step 3: Verify data imports**

In `pages/index/index.js`, temporarily add:
```js
var booksData = require('../../data/books')
console.log('Books loaded:', booksData.books.length)
```
Open DevTools console. Expected: "Books loaded: 2".

- [ ] **Step 4: Commit**

```bash
git add data/books.js utils/storage.js pages/index/index.js
git commit -m "feat: add book data and storage utility helpers"
```

---

### Task 3: Home Page — Book Catalog

**Files:**
- Modify: `french-flashcard/pages/index/index.js`
- Modify: `french-flashcard/pages/index/index.wxml`
- Modify: `french-flashcard/pages/index/index.wxss`

- [ ] **Step 1: Implement `index.js`**

Load books data, navigate to lessons page on tap.

```js
var booksData = require('../../data/books')

Page({
  data: {
    books: []
  },

  onLoad: function () {
    this.setData({ books: booksData.books })
  },

  onTapBook: function (e) {
    var bookId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: '/pages/lessons/lessons?bookId=' + bookId
    })
  }
})
```

- [ ] **Step 2: Implement `index.wxml`**

```html
<view class="page">
  <view class="title">我的课本</view>
  <view class="book-list">
    <view
      class="card book-item"
      wx:for="{{books}}"
      wx:key="id"
      data-id="{{item.id}}"
      bindtap="onTapBook"
    >
      <text class="book-icon">{{item.icon}}</text>
      <text class="book-title">{{item.title}}</text>
      <text class="book-count">{{item.lessons.length}} 课</text>
    </view>
  </view>
</view>
```

- [ ] **Step 3: Implement `index.wxss`**

```css
.page {
  padding: 40rpx;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  margin-bottom: 40rpx;
  color: #1e1e1e;
}

.book-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.book-item {
  display: flex;
  align-items: center;
  padding: 32rpx;
  gap: 24rpx;
}

.book-icon {
  font-size: 56rpx;
}

.book-title {
  font-size: 34rpx;
  flex: 1;
  color: #1e1e1e;
}

.book-count {
  font-size: 26rpx;
  color: #999;
}
```

- [ ] **Step 4: Verify in DevTools**

Expected: page shows "我的课本" title, two book cards with emoji, title, and lesson count. Tapping a book navigates (to blank lessons page for now).

- [ ] **Step 5: Commit**

```bash
git add pages/index/
git commit -m "feat: implement book catalog home page"
```

---

### Task 4: Lesson List Page

**Files:**
- Modify: `french-flashcard/pages/lessons/lessons.js`
- Modify: `french-flashcard/pages/lessons/lessons.wxml`
- Modify: `french-flashcard/pages/lessons/lessons.wxss`

- [ ] **Step 1: Implement `lessons.js`**

Receive bookId param, find the book, compute mastered counts, navigate to cards.

```js
var booksData = require('../../data/books')
var storage = require('../../utils/storage')

Page({
  data: {
    book: null,
    lessons: []
  },

  onLoad: function (options) {
    this.bookId = options.bookId
    var book = booksData.books.find(function(b) { return b.id === options.bookId })
    this.setData({ book: book })
    this._refreshProgress()
  },

  onShow: function () {
    // Refresh progress when returning from cards page
    this._refreshProgress()
  },

  _refreshProgress: function () {
    var bookId = this.bookId
    var book = this.data.book
    if (!book) return

    var lessons = book.lessons.map(function (lesson) {
      var masteredCount = storage.getMasteredCount(bookId, lesson.id)
      return {
        id: lesson.id,
        title: lesson.title,
        totalCards: lesson.cards.length,
        masteredCount: masteredCount
      }
    })
    this.setData({ lessons: lessons })
  },

  onTapLesson: function (e) {
    var lessonId = e.currentTarget.dataset.id
    wx.navigateTo({
      url: '/pages/cards/cards?bookId=' + this.bookId + '&lessonId=' + lessonId
    })
  }
})
```

- [ ] **Step 2: Implement `lessons.wxml`**

```html
<view class="page">
  <view class="title">{{book.title}}</view>
  <view class="lesson-list">
    <view
      class="card lesson-item"
      wx:for="{{lessons}}"
      wx:key="id"
      data-id="{{item.id}}"
      bindtap="onTapLesson"
    >
      <view class="lesson-info">
        <text class="lesson-title">{{item.title}}</text>
        <text class="lesson-progress">{{item.masteredCount}}/{{item.totalCards}} 已掌握</text>
      </view>
      <view class="progress-bar">
        <view class="progress-fill" style="width: {{item.totalCards > 0 ? (item.masteredCount / item.totalCards * 100) : 0}}%"></view>
      </view>
    </view>
  </view>
</view>
```

- [ ] **Step 3: Implement `lessons.wxss`**

```css
.page {
  padding: 40rpx;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  margin-bottom: 40rpx;
  color: #1e1e1e;
}

.lesson-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.lesson-item {
  padding: 32rpx;
}

.lesson-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.lesson-title {
  font-size: 32rpx;
  color: #1e1e1e;
}

.lesson-progress {
  font-size: 24rpx;
  color: #364fc7;
}

.progress-bar {
  height: 8rpx;
  background: #e8ecf4;
  border-radius: 4rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #364fc7;
  border-radius: 4rpx;
  transition: width 0.3s;
}
```

- [ ] **Step 4: Verify in DevTools**

Navigate from home → book. Expected: book title at top, lesson cards with title, "0/5 已掌握" progress text, and empty progress bar. Tapping a lesson navigates to cards page.

- [ ] **Step 5: Commit**

```bash
git add pages/lessons/
git commit -m "feat: implement lesson list page with progress display"
```

---

### Task 5: Card View — Layout and Swiper

**Files:**
- Modify: `french-flashcard/pages/cards/cards.js`
- Modify: `french-flashcard/pages/cards/cards.wxml`
- Modify: `french-flashcard/pages/cards/cards.wxss`

This task builds the card page structure, swiper navigation, and flip animation. Mastery buttons come in Task 6.

- [ ] **Step 1: Implement `cards.js` — data loading and flip logic**

```js
var booksData = require('../../data/books')
var storage = require('../../utils/storage')

Page({
  data: {
    cards: [],           // current visible card list
    allCards: [],        // all cards in lesson
    currentIndex: 0,
    flipped: false,
    filterMode: 'all',   // 'all' or 'unmastered'
    totalCount: 0,
    progressText: '',
    lessonTitle: ''
  },

  onLoad: function (options) {
    this.bookId = options.bookId
    this.lessonId = options.lessonId

    var book = booksData.books.find(function(b) { return b.id === options.bookId })
    var lesson = book.lessons.find(function(l) { return l.id === options.lessonId })

    // Annotate cards with mastered status
    var self = this
    var cards = lesson.cards.map(function(card) {
      return {
        id: card.id,
        front: card.front,
        back: card.back,
        mastered: storage.isMastered(self.bookId, self.lessonId, card.id)
      }
    })

    this.allCards = cards
    this.setData({
      allCards: cards,
      cards: cards,
      lessonTitle: lesson.title,
      totalCount: cards.length
    })
    this._updateProgress()

    // Resume from last visited
    var progress = storage.getProgress(this.bookId, this.lessonId)
    if (progress.lastVisited) {
      var idx = cards.findIndex(function(c) { return c.id === progress.lastVisited })
      if (idx > 0) {
        this.setData({ currentIndex: idx })
      }
    }
  },

  /** Tap card to flip */
  onTapCard: function () {
    this.setData({ flipped: !this.data.flipped })
  },

  /** Swiper slide change */
  onSwiperChange: function (e) {
    var index = e.detail.current
    this.setData({
      currentIndex: index,
      flipped: false   // auto-reset to front face
    })

    // Save last visited
    var card = this.data.cards[index]
    if (card) {
      var progress = storage.getProgress(this.bookId, this.lessonId)
      progress.lastVisited = card.id
      storage.saveProgress(this.bookId, this.lessonId, progress)
    }
    this._updateProgress()
  },

  _updateProgress: function () {
    var current = this.data.currentIndex + 1
    var total = this.data.cards.length
    this.setData({ progressText: current + '/' + total })
  }
})
```

- [ ] **Step 2: Implement `cards.wxml`**

```html
<view class="page">
  <!-- Top bar: progress + filter -->
  <view class="top-bar">
    <text class="progress-text">{{progressText}}</text>
    <text class="lesson-title-small">{{lessonTitle}}</text>
  </view>

  <!-- Card swiper -->
  <swiper
    class="card-swiper"
    current="{{currentIndex}}"
    bindchange="onSwiperChange"
    duration="300"
    easing-function="easeInOutCubic"
  >
    <swiper-item wx:for="{{cards}}" wx:key="id">
      <view class="card-wrapper" bindtap="onTapCard">
        <view class="flip-container {{flipped && currentIndex === index ? 'flipped' : ''}}">
          <!-- Front: Chinese -->
          <view class="flip-face flip-front card">
            <text class="card-text">{{item.front}}</text>
          </view>
          <!-- Back: French -->
          <view class="flip-face flip-back card">
            <text class="card-text card-text-back">{{item.back}}</text>
          </view>
        </view>
      </view>
    </swiper-item>
  </swiper>
</view>
```

- [ ] **Step 3: Implement `cards.wxss` — flip animation and layout**

```css
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 24rpx;
  box-sizing: border-box;
}

/* Top bar */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12rpx 8rpx;
  margin-bottom: 16rpx;
}

.progress-text {
  font-size: 30rpx;
  color: #364fc7;
  font-weight: bold;
}

.lesson-title-small {
  font-size: 26rpx;
  color: #999;
}

/* Swiper */
.card-swiper {
  flex: 1;
  width: 100%;
}

/* Card wrapper inside swiper-item */
.card-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 24rpx;
  box-sizing: border-box;
}

/* 3D Flip */
.flip-container {
  width: 100%;
  height: 70%;
  position: relative;
  perspective: 1000px;
  transform-style: preserve-3d;
  transition: transform 0.4s ease-in-out;
}

.flip-container.flipped {
  transform: rotateY(180deg);
}

.flip-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
  box-sizing: border-box;
}

.flip-front {
  background: #fff;
}

.flip-back {
  background: #f0f4f8;
  transform: rotateY(180deg);
}

/* Card text */
.card-text {
  font-size: 40rpx;
  text-align: center;
  line-height: 1.8;
  color: #1e1e1e;
}

.card-text-back {
  color: #364fc7;
}
```

- [ ] **Step 4: Verify in DevTools**

Navigate home → book → lesson. Expected:
- Progress "1/5" at top left, lesson title at top right
- Card centered on screen with sentence in Chinese
- Tap card → 3D flip to French (blue text, light blue bg)
- Tap again → flips back
- Swipe left/right → next/prev card, auto-resets to front

- [ ] **Step 5: Commit**

```bash
git add pages/cards/
git commit -m "feat: implement card view with flip animation and swiper"
```

---

### Task 6: Card View — Mastery Buttons and Auto-Advance

**Files:**
- Modify: `french-flashcard/pages/cards/cards.js`
- Modify: `french-flashcard/pages/cards/cards.wxml`
- Modify: `french-flashcard/pages/cards/cards.wxss`

- [ ] **Step 1: Add mastery button handlers to `cards.js`**

Add these methods to the Page object:

```js
  /** Mark as not mastered, advance to next */
  onMarkNotMastered: function () {
    this._setMastered(false)
  },

  /** Mark as mastered, advance to next */
  onMarkMastered: function () {
    this._setMastered(true)
  },

  _setMastered: function (mastered) {
    var index = this.data.currentIndex
    var card = this.data.cards[index]
    if (!card) return

    // Update storage
    storage.setMastered(this.bookId, this.lessonId, card.id, mastered)

    // Update local state
    var cards = this.data.cards
    cards[index].mastered = mastered
    var allCards = this.allCards
    var allIdx = allCards.findIndex(function(c) { return c.id === card.id })
    if (allIdx !== -1) allCards[allIdx].mastered = mastered

    this.setData({ cards: cards, allCards: allCards })

    // If in unmastered filter mode and card was mastered, remove it from view
    if (this.data.filterMode === 'unmastered' && mastered) {
      var filtered = this.data.cards.filter(function(c) { return c.id !== card.id })
      if (filtered.length === 0) {
        wx.showToast({ title: '全部已掌握！', icon: 'success', duration: 1500 })
        setTimeout(function() { wx.navigateBack() }, 1500)
        return
      }
      var newIndex = Math.min(index, filtered.length - 1)
      this.setData({ cards: filtered, currentIndex: newIndex, flipped: false })
      this._updateProgress()
      return
    }

    // Advance or finish
    if (index >= this.data.cards.length - 1) {
      // Last card — show toast and go back
      wx.showToast({ title: '完成！', icon: 'success', duration: 1500 })
      setTimeout(function() {
        wx.navigateBack()
      }, 1500)
    } else {
      this.setData({
        currentIndex: index + 1,
        flipped: false
      })
      this._updateProgress()
    }
  },
```

- [ ] **Step 2: Add mastery buttons to `cards.wxml`**

Insert after the `</swiper>` closing tag, before `</view>`:

```html
  <!-- Bottom buttons -->
  <view class="bottom-bar">
    <view class="btn-outline mastery-btn" bindtap="onMarkNotMastered">
      <text>✗ 未掌握</text>
    </view>
    <view class="mastery-indicator {{cards[currentIndex].mastered ? 'mastered' : ''}}">
      <text>{{cards[currentIndex].mastered ? '已掌握' : '未掌握'}}</text>
    </view>
    <view class="btn-primary mastery-btn" bindtap="onMarkMastered">
      <text>✓ 已掌握</text>
    </view>
  </view>
```

- [ ] **Step 3: Add bottom bar styles to `cards.wxss`**

```css
/* Bottom bar */
.bottom-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 8rpx;
  gap: 16rpx;
}

.mastery-btn {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  font-size: 30rpx;
}

.mastery-indicator {
  font-size: 24rpx;
  color: #999;
}

.mastery-indicator.mastered {
  color: #364fc7;
}
```

- [ ] **Step 4: Verify in DevTools**

Expected:
- Two buttons at bottom: "✗ 未掌握" (outline) and "✓ 已掌握" (filled)
- Current mastery status shown between buttons
- Tap "✓ 已掌握" → card advances to next, status saved
- On last card, tap either button → "完成！" toast, then auto-navigates back to lesson list
- Return to lesson list → progress shows updated count (e.g., "2/5 已掌握")

- [ ] **Step 5: Commit**

```bash
git add pages/cards/
git commit -m "feat: add mastery buttons with auto-advance and completion toast"
```

---

### Task 7: Card View — Filter Mode

**Files:**
- Modify: `french-flashcard/pages/cards/cards.js`
- Modify: `french-flashcard/pages/cards/cards.wxml`
- Modify: `french-flashcard/pages/cards/cards.wxss`

- [ ] **Step 1: Add filter toggle handler to `cards.js`**

Add this method to the Page object:

```js
  /** Toggle between all / unmastered filter */
  onToggleFilter: function () {
    var newMode = this.data.filterMode === 'all' ? 'unmastered' : 'all'
    var filteredCards

    if (newMode === 'unmastered') {
      filteredCards = this.allCards.filter(function(c) { return !c.mastered })
      if (filteredCards.length === 0) {
        wx.showToast({ title: '全部已掌握！', icon: 'success' })
        return
      }
    } else {
      filteredCards = this.allCards.slice()
    }

    this.setData({
      filterMode: newMode,
      cards: filteredCards,
      currentIndex: 0,
      flipped: false
    })
    this._updateProgress()
  },
```

- [ ] **Step 2: Add filter toggle to `cards.wxml`**

Add inside the `.top-bar` view, between the progress text and lesson title:

```html
    <view class="filter-toggle" bindtap="onToggleFilter">
      <text class="filter-text {{filterMode === 'all' ? 'filter-active' : ''}}">全部</text>
      <text class="filter-divider">|</text>
      <text class="filter-text {{filterMode === 'unmastered' ? 'filter-active' : ''}}">未掌握</text>
    </view>
```

- [ ] **Step 3: Add filter styles to `cards.wxss`**

```css
/* Filter toggle */
.filter-toggle {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.filter-text {
  font-size: 26rpx;
  color: #999;
  padding: 4rpx 12rpx;
}

.filter-text.filter-active {
  color: #364fc7;
  font-weight: bold;
}

.filter-divider {
  color: #ddd;
  font-size: 26rpx;
}
```

- [ ] **Step 4: Verify in DevTools**

Expected:
- Filter toggle appears in top bar: "全部 | 未掌握"
- Default: "全部" is active (blue)
- Mark some cards as mastered, then tap "未掌握" → only unmastered cards shown
- If all cards mastered, tapping "未掌握" shows toast "全部已掌握！"
- Tap "全部" → back to all cards

- [ ] **Step 5: Commit**

```bash
git add pages/cards/
git commit -m "feat: add filter toggle for all/unmastered cards"
```

---

### Task 8: Polish and Final Verification

**Files:**
- Possibly modify any file for bug fixes or visual tweaks

- [ ] **Step 1: Full flow test**

In DevTools, run through the complete flow:
1. Home → see 2 books
2. Tap book → see lessons with "0/N 已掌握"
3. Tap lesson → see cards, flip works, swipe works
4. Mark some mastered, some not → progress updates
5. Reach last card → toast → back to lessons → progress updated
6. Re-enter same lesson → resumes at last visited card
7. Use filter → only unmastered cards shown

- [ ] **Step 2: Fix any visual or functional issues found**

Address any spacing, font, animation, or logic bugs discovered during testing.

- [ ] **Step 3: Add `.gitignore`**

```
node_modules/
.superpowers/
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: polish and final verification pass"
```
