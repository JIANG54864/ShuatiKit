/**
 * 答题记录存储（wx.storage 本地缓存）
 * 结构：{ [qid]: { sel: 'A', correct: true, lucky: false, ts: 1699999999 } }
 * lucky = 答对但被用户标记为「蒙对」
 * 错题本 = 最近一次答错 或 标记了蒙对的题目集合
 *（重新答对且未标记蒙对时自动移出；重新作答会重置蒙对标记）
 */
const ANSWERS_KEY = 'sq_answers';

function getAnswers() {
  return wx.getStorageSync(ANSWERS_KEY) || {};
}

function recordAnswer(qid, sel, correct) {
  const answers = getAnswers();
  // 覆盖旧记录：蒙对标记随本次作答重置，答对后可重新标记
  answers[qid] = { sel, correct, lucky: false, ts: Date.now() };
  wx.setStorageSync(ANSWERS_KEY, answers);
}

/** 标记/取消「蒙对」（仅对答对的记录生效） */
function setLucky(qid, lucky) {
  const answers = getAnswers();
  if (!answers[qid]) return;
  answers[qid].lucky = !!(lucky && answers[qid].correct);
  wx.setStorageSync(ANSWERS_KEY, answers);
}

/** 是否计入错题本：答错 或 蒙对 */
function isWrong(rec) {
  return !rec.correct || !!rec.lucky;
}

function getStats() {
  const answers = getAnswers();
  const ids = Object.keys(answers);
  const correct = ids.filter(k => answers[k].correct).length;
  return {
    answered: ids.length,
    correct,
    wrong: ids.filter(k => isWrong(answers[k])).length,
    rate: ids.length ? Math.round((correct / ids.length) * 100) : 0
  };
}

function getWrongIds() {
  const answers = getAnswers();
  return Object.keys(answers).filter(k => isWrong(answers[k]));
}

function chapterProgress(questions) {
  const answers = getAnswers();
  let answered = 0;
  let correct = 0;
  questions.forEach(q => {
    const rec = answers[q.id];
    if (rec) {
      answered += 1;
      if (rec.correct) correct += 1;
    }
  });
  return { answered, correct };
}

function resetAll() {
  wx.removeStorageSync(ANSWERS_KEY);
}

module.exports = {
  getAnswers,
  recordAnswer,
  setLucky,
  getStats,
  getWrongIds,
  chapterProgress,
  resetAll
};
