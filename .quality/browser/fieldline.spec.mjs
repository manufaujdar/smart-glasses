import {test, expect} from './test.mjs';
import AxeBuilder from '@axe-core/playwright';

test('browser preferences persist and govern synthetic preview only', async ({page}) => {
  await page.route('**/api/**', route => route.fulfill({
    contentType: 'application/json', body: JSON.stringify({adapters: [], state: {}, devices: []})
  }));
  await page.addInitScript(() => {
    navigator.mediaDevices.getUserMedia = async constraints => {
      window.constraints = constraints;
      return new MediaStream();
    };
    HTMLMediaElement.prototype.play = async () => {};
    window.WebSocket = class { constructor() {} };
    window.SpeechRecognition = class { start() { window.recognitionLanguage = this.lang; } };
  });
  await page.goto('/');
  await page.getByText('Browser preferences', {exact: true}).click();
  await page.locator('#preview-audio').uncheck();
  await page.locator('#speech-language').selectOption('en-IN');
  await page.reload();
  await expect(page.locator('#preview-audio')).not.toBeChecked();
  await expect(page.locator('#speech-language')).toHaveValue('en-IN');
  await page.locator('#start-preview').click();
  expect(await page.evaluate(() => window.constraints.audio)).toBe(false);
  await page.locator('#listen').click();
  expect(await page.evaluate(() => window.recognitionLanguage)).toBe('en-IN');
  await page.locator('#preview-audio').evaluate(el => { el.closest('details').open = true; });
  const audit = await new AxeBuilder({page}).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
  expect(audit.violations.map(v => ({id: v.id, targets: v.nodes.map(n => n.target)}))).toEqual([]);
});
