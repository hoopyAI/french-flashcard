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
