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
