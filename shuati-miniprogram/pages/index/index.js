const bank = require('../../data/questions.js');
const store = require('../../utils/store.js');

Page({
  data: {
    title: bank.title,
    source: bank.source,
    total: bank.total,
    stats: { answered: 0, correct: 0, wrong: 0, rate: 0 },
    chapters: []
  },

  onShow() {
    this.refresh();
  },

  refresh() {
    const stats = store.getStats();
    const chapters = bank.chapters.map(c => {
      const p = store.chapterProgress(c.questions);
      return {
        id: c.id,
        name: c.name,
        count: c.questions.length,
        answered: p.answered,
        correct: p.correct,
        percent: Math.round((p.answered / c.questions.length) * 100)
      };
    });
    this.setData({ stats, chapters });
  },

  goChapter(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/quiz/quiz?chapter=${id}` });
  },

  goRandom() {
    wx.navigateTo({ url: '/pages/quiz/quiz?mode=random' });
  },

  goWrong() {
    const n = store.getWrongIds().length;
    if (!n) {
      wx.showToast({ title: '错题本还是空的，先去刷题吧', icon: 'none' });
      return;
    }
    wx.navigateTo({ url: '/pages/quiz/quiz?mode=wrong' });
  },

  reset() {
    wx.showModal({
      title: '清空记录',
      content: '将清除全部答题记录和错题本，且不可恢复。确定清空吗？',
      confirmText: '清空',
      confirmColor: '#F0453A',
      success: r => {
        if (r.confirm) {
          store.resetAll();
          this.refresh();
          wx.showToast({ title: '已清空', icon: 'success' });
        }
      }
    });
  }
});
