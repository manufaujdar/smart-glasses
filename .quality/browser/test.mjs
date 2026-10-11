import {test as base, expect} from '@playwright/test';
export {expect};
export const test = base.extend({
  page: async ({page}, use) => {
    await page.route('**/*', route => {
      const url = new URL(route.request().url());
      return ['127.0.0.1', 'localhost'].includes(url.hostname) ? route.continue() : route.abort();
    });
    await use(page);
  }
});
