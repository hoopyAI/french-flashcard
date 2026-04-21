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
    if (progress.mastered.indexOf(cardId) === -1) {
      progress.mastered.push(cardId)
    }
  } else {
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
