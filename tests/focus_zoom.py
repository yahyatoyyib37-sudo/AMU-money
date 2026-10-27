"""Focused follow-up checks for keyboard recovery and simulated pinch zoom."""
import asyncio,json,pathlib
from playwright.async_api import async_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page(viewport={'width':1440,'height':1000});await page.goto('http://127.0.0.1:8765/Halal-Income-Enhanced.html#sources')
  await page.locator('#sourcesGrid [data-fav=academic-tutoring]').click();await page.locator('.sidebar [data-tab=saved]').click();await page.locator('#clearSaved').click();assert await page.locator('#view-saved h2').evaluate('(x)=>x===document.activeElement')
  await page.locator('.toast-action',has_text='Undo').last.click();assert await page.locator('#view-saved h2').evaluate('(x)=>x===document.activeElement');assert await page.locator('#savedGrid [data-card]').count()==1
  await page.locator('.sidebar [data-tab=dashboard]').click();await page.locator('[data-whide=spotlight]').click();await page.wait_for_timeout(300);assert await page.locator('#widgetGrid').evaluate('(x)=>x.contains(document.activeElement)');await page.locator('.toast-action',has_text='Undo').last.click();assert await page.locator('#view-dashboard h1').evaluate('(x)=>x===document.activeElement')
  await page.set_viewport_size({'width':390,'height':844});await page.evaluate("document.querySelector('.sidebar [data-tab=sources]').click()")
  cdp=await page.context.new_cdp_session(page);await cdp.send('Emulation.setPageScaleFactor',{'pageScaleFactor':2});assert await page.evaluate('visualViewport.scale')==2
  await page.locator('#searchInput').fill('academic tutoring');await page.wait_for_timeout(200);assert await page.locator('#sourcesGrid [data-card]').count()==1;await page.locator('#sourcesGrid [data-open=academic-tutoring]').focus();await page.keyboard.press('Enter');await page.wait_for_selector('#modal.on');await page.keyboard.press('Escape');await page.wait_for_timeout(300);assert not await page.locator('#modal').evaluate('(x)=>x.classList.contains("on")');await cdp.send('Emulation.setPageScaleFactor',{'pageScaleFactor':1})
  await b.close()
 (ROOT/'qa'/'focus-zoom-results.json').write_text(json.dumps({'keyboard_focus_after_clear_hide_undo':'passed','simulated_pinch_zoom_200_percent_keyboard':'passed','note':'CDP page-scale simulation; not a physical device or desktop browser zoom test.'},indent=2))
 print('PASS keyboard recovery after clear/hide/undo; simulated 200% pinch zoom keyboard interaction')
asyncio.run(main())
