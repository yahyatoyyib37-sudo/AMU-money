"""Verify a large multilingual note survives import, storage and actual export."""
import asyncio,json,pathlib
from playwright.async_api import async_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
async def main():
 text=('&amp; العربية हिंदी <b>literal</b>\n'*18000)+'  trailing  \n'
 v={'app':'halal-money-plan','version':1,'settings':{},'favorites':[],'notes':{'academic-tutoring':text},'checklist':[],'vault':[],'compare':[]}
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=await b.new_page();await page.goto('http://127.0.0.1:8765/Halal-Income-Enhanced.html#customize')
  await page.locator('#backupInput').set_input_files({'name':'large.json','mimeType':'application/json','buffer':json.dumps(v).encode()});await page.locator('#confirmImport').click();await page.locator('.sidebar [data-tab=sources]').click();await page.locator('#sourcesGrid [data-open=academic-tutoring]').click();assert await page.locator('#noteInput').input_value()==text;await page.reload();assert await page.locator('#noteInput').input_value()==text;await page.locator('#mClose').click();await page.wait_for_timeout(250);await page.locator('.sidebar [data-tab=customize]').click()
  async with page.expect_download() as info:await page.locator('#exportBackup').click()
  file=await (await info.value).path();out=json.loads(pathlib.Path(file).read_text());assert out['notes']['academic-tutoring']==text
  await b.close()
 (ROOT/'qa'/'large-backup-results.json').write_text(json.dumps({'characters':len(text),'import_reload_export_exact_round_trip':'passed'}))
 print('PASS large exact-text backup round trip:',len(text),'characters')
asyncio.run(main())
