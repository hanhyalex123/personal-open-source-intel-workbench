from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
import sys

frontend_url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5173'
out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('docs/assets')
out_dir.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    try:
        browser = p.chromium.launch(channel='chrome', headless=True)
    except Exception:
        browser = p.chromium.launch(headless=True)

    page = browser.new_page(viewport={'width': 1600, 'height': 1200}, locale='zh-CN')
    page.set_default_timeout(60000)

    page.goto(frontend_url, wait_until='domcontentloaded')
    page.get_by_role('heading', name='封面', level=1).wait_for()
    page.locator('.project-summary-card').first.wait_for()
    page.screenshot(path=str(out_dir / 'screenshot-home.png'))

    page.get_by_role('button', name='线索台').click()
    page.get_by_role('heading', name='线索台', level=1).wait_for()
    page.get_by_role('heading', name='当前', level=2).wait_for()
    page.screenshot(path=str(out_dir / 'screenshot-sync-monitor.png'))

    page.get_by_role('button', name='文档台').click()
    page.get_by_role('heading', name='文档台', level=1).wait_for()
    page.locator('.docs-workbench-page').wait_for()
    page.locator('.docs-project-rail__item').first.wait_for()
    try:
        page.get_by_role('heading', name='解读', level=2).wait_for(timeout=15000)
    except PlaywrightTimeoutError:
        page.wait_for_timeout(1500)
    page.screenshot(path=str(out_dir / 'screenshot-docs-workbench.png'))

    browser.close()
