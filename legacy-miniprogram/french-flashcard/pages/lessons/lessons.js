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
