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
  },

  /** Mark as not mastered, advance to next */
  onMarkNotMastered: function () {
    this._setMastered(false)
  },

  /** Mark as mastered, advance to next */
  onMarkMastered: function () {
    this._setMastered(true)
  },

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
})
