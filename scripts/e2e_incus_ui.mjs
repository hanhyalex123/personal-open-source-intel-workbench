import { mkdir } from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright-core";

const frontendUrl = process.argv[2];
const artifactDir = process.argv[3];

if (!frontendUrl || !artifactDir) {
  throw new Error("Usage: node scripts/e2e_incus_ui.mjs <frontend-url> <artifact-dir>");
}

await mkdir(artifactDir, { recursive: true });

let browser;
try {
  browser = await chromium.launch({ channel: "chrome", headless: true });
} catch (_error) {
  browser = await chromium.launch({ headless: true });
}

const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
page.setDefaultTimeout(60000);

async function saveScreenshot(filename) {
  await page.screenshot({
    path: path.join(artifactDir, filename),
    fullPage: true,
  });
}

try {
  await page.goto(frontendUrl, { waitUntil: "networkidle" });
  const docsNavButton = page.locator(".sidebar__nav-item").filter({ hasText: "文档解读" }).first();
  await docsNavButton.waitFor();
  await page.locator(".homepage-topline").waitFor();
  await saveScreenshot("01-home.png");

  await docsNavButton.click();
  await page.locator("h1").filter({ hasText: "文档解读" }).first().waitFor();
  await page.locator(".docs-workbench-page").waitFor();
  await page.getByText("当前页面快照").first().waitFor();
  await page.locator(".docs-pages-list__item").first().waitFor();
  await saveScreenshot("02-docs-workbench.png");

  await page.locator(".docs-pages-list__item").first().click();
  await page.locator(".docs-page-diff").waitFor();
  await saveScreenshot("03-page-diff.png");
} finally {
  await browser.close();
}
