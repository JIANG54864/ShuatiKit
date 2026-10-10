/**
 * 错题本逻辑测试（Node 环境，mock wx/Page 直接驱动 quiz 页面逻辑）
 * 覆盖：
 *  1. 错题本重做答对 → 自动移出
 *  2. 蒙对标记：答对后标记 → 留在错题本；取消 → 移出；统计口径一致
 *  3. 蒙对的题进错题本重做：答对(未标记) → 移出；再标记 → 保留
 *  4. 章节模式回看蒙对的题：状态正确显示、可取消标记
 *  5. 答错的题不能标记蒙对
 */
const path = require('path');
const MP = path.join(__dirname, 'shuati-miniprogram');

// ---- mock 环境 ----
const mem = {};
global.wx = {
  getStorageSync: k => mem[k],
  setStorageSync: (k, v) => { mem[k] = v; },
  removeStorageSync: k => { delete mem[k]; },
  vibrateShort() {},
  setNavigationBarTitle() {},
  showToast() {},
  pageScrollTo() {},
  showModal() {},
  navigateBack() {}
};
let pageConfig = null;
global.Page = cfg => { pageConfig = cfg; };

const store = require(path.join(MP, 'utils/store.js'));
const bank = require(path.join(MP, 'data/questions.js'));
require(path.join(MP, 'pages/quiz/quiz.js'));

let failures = 0;
function check(name, cond) {
  console.log(`${cond ? '✅' : '❌'} ${name}`);
  if (!cond) failures++;
}

function newPage(options) {
  const page = Object.assign({}, pageConfig, {
    data: JSON.parse(JSON.stringify(pageConfig.data)),
    setData(d) { Object.assign(this.data, d); }
  });
  page.onLoad(options);
  return page;
}

function tap(page, letter) {
  page.onOption({ currentTarget: { dataset: { letter } } });
}

const qs = bank.chapters[0].questions;
const CH1 = bank.chapters[0].id;

// ==== 场景1：错题本重做答对 → 自动移出 ====
store.resetAll();
store.recordAnswer(qs[0].id, qs[0].answer === 'A' ? 'B' : 'A', false);
store.recordAnswer(qs[1].id, qs[1].answer === 'A' ? 'B' : 'A', false);
check('场景1 初始错题本 2 题', store.getWrongIds().length === 2);
let page = newPage({ mode: 'wrong' });
check('场景1 错题本题目可重做(judged=false)', page.data.judged === false);
tap(page, page.data.q.answer);
page.next();
tap(page, page.data.q.answer);
check('场景1 重做答对后错题本清空', store.getWrongIds().length === 0);

// ==== 场景2：答对后标记蒙对 → 留在错题本 ====
store.resetAll();
page = newPage({ mode: 'chapter', chapter: CH1 });
tap(page, page.data.q.answer);
const luckyId = page.data.q.id;
check('场景2 答对后不在错题本', store.getWrongIds().length === 0);
page.onToggleLucky();
check('场景2 标记蒙对后进入错题本', store.getWrongIds().indexOf(luckyId) >= 0);
check('场景2 页面 lucky 状态同步', page.data.lucky === true);
check('场景2 stats.wrong 与错题本口径一致', store.getStats().wrong === store.getWrongIds().length);
check('场景2 蒙对仍计入答对数', store.getStats().correct === 1);
page.onToggleLucky();
check('场景2 取消标记后移出错题本', store.getWrongIds().length === 0);
page.onToggleLucky(); // 重新标记，供场景3/4使用
check('场景2 重新标记蒙对', store.getWrongIds().length === 1);

// ==== 场景3：蒙对的题在错题本重做 ====
page = newPage({ mode: 'wrong' });
check('场景3 错题本包含蒙对的题', page.data.total === 1 && page.data.q.id === luckyId);
tap(page, page.data.q.answer);
check('场景3 重做答对(未标记) → 移出错题本', store.getWrongIds().length === 0);
page.onToggleLucky();
check('场景3 重做后再标记蒙对 → 留在错题本', store.getWrongIds().length === 1);

// ==== 场景4：章节模式回看蒙对的题 ====
page = newPage({ mode: 'chapter', chapter: CH1 });
check('场景4 章节模式续到第一道未答题', page.data.idx === 1 && page.data.judged === false);
page.prev();
check('场景4 回看蒙对的题：judged+lucky 状态还原',
  page.data.q.id === luckyId && page.data.judged === true && page.data.lucky === true);
page.onToggleLucky();
check('场景4 回看时取消蒙对 → 移出错题本', store.getWrongIds().length === 0);

// ==== 场景5：答错的题不能标记蒙对 ====
store.resetAll();
page = newPage({ mode: 'chapter', chapter: CH1 });
tap(page, page.data.q.answer === 'A' ? 'B' : 'A');
page.onToggleLucky(); // 应被忽略
const rec = store.getAnswers()[page.data.q.id];
check('场景5 答错的题标记蒙对被忽略', rec.lucky === false && rec.correct === false);
check('场景5 答错的题仍在错题本', store.getWrongIds().length === 1);

store.resetAll();
console.log(failures ? `\n❌ ${failures} 项测试失败` : '\n✅ 全部测试通过');
process.exitCode = failures ? 1 : 0;
