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
