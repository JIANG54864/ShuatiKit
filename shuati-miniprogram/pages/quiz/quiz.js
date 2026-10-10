const bank = require('../../data/questions.js');
const store = require('../../utils/store.js');

function allQuestions() {
  const list = [];
  bank.chapters.forEach(c => {
    c.questions.forEach(q => {
      list.push(Object.assign({}, q, { chapterName: c.name }));
    });
  });
  return list;
}

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const t = arr[i];
    arr[i] = arr[j];
    arr[j] = t;
  }
  return arr;
}

Page({
  data: {
    list: [],
    idx: 0,
    total: 0,
    q: null,
    selected: '',
    judged: false,
    isCorrect: false,
    lucky: false,
    sessionRight: 0,
    sessionTotal: 0,
    percent: 0,
    isLast: false,
    chapterName: ''
  },

  onLoad(options) {
    let list = [];
    let title = '刷题';
    const answers = store.getAnswers();
    let startIdx = 0;

    // 错题本/随机刷题是「重做模式」：不沿用历史判定，题目重新可作答
    // （否则错题本里的题永远是已判定状态，答对也无法移出错题本）
    this.freshMode = options.mode === 'wrong' || options.mode === 'random';

    if (options.mode === 'wrong') {
      const map = {};
      allQuestions().forEach(q => { map[q.id] = q; });
      list = store.getWrongIds().map(id => map[id]).filter(Boolean);
      title = '错题本';
    } else if (options.mode === 'random') {
      list = shuffle(allQuestions());
      title = '随机刷题';
    } else {
      const ch = bank.chapters.find(c => c.id === options.chapter);
      if (ch) {
        list = ch.questions.map(q => Object.assign({}, q, { chapterName: ch.name }));
        title = ch.name;
        // 顺序练习：自动续到第一道未作答的题
        const firstUnanswered = list.findIndex(q => !answers[q.id]);
        if (firstUnanswered > 0) startIdx = firstUnanswered;
      }
    }

    if (!list.length) {
      wx.showToast({ title: '没有题目', icon: 'none' });
      setTimeout(() => wx.navigateBack(), 900);
      return;
    }

    this.setData({ list, total: list.length });
    wx.setNavigationBarTitle({ title });
    this.showQuestion(startIdx);
  },

  showQuestion(idx) {
    const q = this.data.list[idx];
    // 重做模式下忽略历史记录，让用户重新作答
    const rec = this.freshMode ? null : store.getAnswers()[q.id];
    this.setData({
      idx,
      q,
      chapterName: q.chapterName || '',
      selected: rec ? rec.sel : '',
      judged: !!rec,
      isCorrect: rec ? !!rec.correct : false,
      lucky: rec ? !!rec.lucky : false,
      percent: Math.round(((idx + 1) / this.data.total) * 100),
      isLast: idx === this.data.total - 1
    });
    wx.pageScrollTo({ scrollTop: 0, duration: 150 });
  },

  onOption(e) {
    if (this.data.judged) return;
    const letter = e.currentTarget.dataset.letter;
    const q = this.data.q;
    const correct = letter === q.answer;
    store.recordAnswer(q.id, letter, correct);
    this.setData({
      selected: letter,
      judged: true,
      isCorrect: correct,
      lucky: false,
      sessionTotal: this.data.sessionTotal + 1,
      sessionRight: this.data.sessionRight + (correct ? 1 : 0)
    });
    wx.vibrateShort({ type: correct ? 'light' : 'heavy' });
  },

  // 蒙对标记：答对的题也可以标记为「蒙对」，标记后保留在错题本继续攻克
  onToggleLucky() {
    if (!this.data.judged || !this.data.isCorrect) return;
    const lucky = !this.data.lucky;
    store.setLucky(this.data.q.id, lucky);
    this.setData({ lucky });
    wx.showToast({
      title: lucky ? '已标记蒙对，保留在错题本' : '已取消蒙对标记',
      icon: 'none'
    });
  },

  prev() {
    if (this.data.idx > 0) this.showQuestion(this.data.idx - 1);
  },

  next() {
    if (!this.data.judged) {
      wx.showToast({ title: '先选一个答案吧', icon: 'none' });
      return;
    }
    if (this.data.idx < this.data.total - 1) {
      this.showQuestion(this.data.idx + 1);
    } else {
      this.finish();
    }
  },

  finish() {
    const { sessionRight, sessionTotal } = this.data;
    const content = sessionTotal
      ? `本次作答 ${sessionTotal} 题，答对 ${sessionRight} 题，正确率 ${Math.round((sessionRight / sessionTotal) * 100)}%`
      : '本次没有作答新题';
    wx.showModal({
      title: '🎉 练习完成',
      content,
      confirmText: '返回首页',
      cancelText: '再翻翻看',
      success: r => {
        if (r.confirm) wx.navigateBack();
      }
    });
  }
});
