import {test, expect} from './test.mjs';
import AxeBuilder from '@axe-core/playwright';
const url = 'http://127.0.0.1:4214/';

test('synthetic comparison retains reading position and failed-save state', async ({page}) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(url);
  await page.locator('#loadDemo').click();
  await expect(page.locator('#comparePair')).toBeEnabled();
  await page.locator('#comparePair').click();
  await page.locator('#sensitivity').evaluate(el => {
    for (let node = el.parentElement; node; node = node.parentElement)
      if (node.tagName === 'DETAILS') node.open = true;
  });
  await page.locator('#sensitivity').scrollIntoViewIfNeeded();
  await page.locator('#sensitivity').focus();
  const before = await page.evaluate(() => scrollY);
  await page.locator('#sensitivity').press('ArrowRight');
  await expect.poll(() => page.evaluate(() => scrollY)).toBeCloseTo(before, 0);
  await page.evaluate(() => {
    window.savedSet = Storage.prototype.setItem;
    Storage.prototype.setItem = function () { throw Error('Synthetic storage rejection'); };
  });
  await page.locator('#saveResult').click();
  await expect(page.locator('#saveStatus')).toContainText('Could not save');
  await expect(page.locator('#historyList .history-item')).toHaveCount(0);
  await page.evaluate(() => { Storage.prototype.setItem = window.savedSet; });
  await page.locator('#saveResult').click();
  await expect(page.locator('#historyList .history-item')).toHaveCount(1);
  const audit = await new AxeBuilder({page}).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(audit.violations.map(v => ({id: v.id, targets: v.nodes.map(n => n.target)}))).toEqual([]);
  expect(errors).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
