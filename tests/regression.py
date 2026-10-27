"""Browser regression checks; requires Python Playwright and system Chromium.
Run a server from the repository: python -m http.server 8765 --bind 127.0.0.1
Then: python tests/regression.py
QA dependencies are not application dependencies.
"""
import asyncio, json, os, pathlib
from playwright.async_api import async_playwright
import traceback

ROOT=pathlib.Path(__file__).resolve().parents[1]
URL=os.environ.get('AMU_TEST_URL','http://127.0.0.1:8765/Halal-Income-Enhanced.html')
AXE_PATH=os.environ.get('AXE_PATH','/tmp/amu-qa/node_modules/axe-core/axe.min.js')
CHROMIUM_PATH=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium')
results=[]
errors=[]
async def check(name, fn):
 if os.environ.get("AMU_GROUP") and os.environ["AMU_GROUP"] not in name:return
 try:
  await fn()
  results.append({'name':name,'result':'passed'})
  print('PASS',name,flush=True)
 except Exception as e:
  results.append({'name':name,'result':'failed','error':traceback.format_exc()})
  print('FAIL',name,traceback.format_exc(),flush=True)
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(executable_path=CHROMIUM_PATH,args=['--no-sandbox'])
  ctx=await browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
  async def page_new(context=ctx):
   p=await context.new_page();p.on('pageerror',lambda e:errors.append(str(e)));await p.goto(URL);await p.wait_for_selector('html[data-ready=true]');return p
  page=await page_new()
  async def nav(tab,p=page):
   await p.evaluate('(tab)=>document.querySelector(".sidebar [data-tab="+tab+"]").click()',tab)
   await p.wait_for_selector('#view-'+tab+'.on')
  async def reset(p=page):
   await nav('sources',p);await p.locator('[data-quick=reset]').click();await p.wait_for_timeout(160)
  async def filtering():
   await reset();assert await page.locator('#sourcesGrid [data-card]').count()==30
   await page.locator('#searchInput').fill('tutoring');await page.wait_for_timeout(180)
   await page.select_option('#fCategory','Tutoring & Services');await page.select_option('#fInvestment','zero');await page.select_option('#fDevice','phone')
   await page.locator('[data-quick=quick]').click();await page.select_option('#sortSources','az')
   cards=page.locator('#sourcesGrid [data-card]');assert await cards.count()==2
   titles=await cards.locator('h3').all_text_contents();assert titles==sorted(titles)
   assert await page.locator('[data-remove-filter]').count()==5
   await page.reload();await page.wait_for_selector('html[data-ready=true]');assert await page.locator('#searchInput').input_value()=='tutoring';assert await page.locator('#sourcesGrid [data-card]').count()==2
   await page.locator('[data-remove-filter=query]').click();assert await page.locator('#searchInput').input_value()==''
   await reset();assert await page.locator('#sourcesGrid [data-card]').count()==30
  await check('Combined search, filters, quick tags, sorting, chip removal, reload and reset',filtering)
  async def table():
   await reset();await page.locator('[data-layout=table]').click();assert await page.locator('#sourcesTable').is_visible();assert await page.locator('#sourcesTable tbody tr').count()==30
   await page.locator('#columnPicker summary').click();await page.locator('[data-column=progress]').check();assert 'MY PROGRESS' in await page.locator('#sourcesTable thead').inner_text()
   await page.reload();await page.wait_for_selector('html[data-ready=true]');assert await page.locator('#sourcesTable').is_visible();assert 'MY PROGRESS' in await page.locator('#sourcesTable thead').inner_text()
   await page.locator('[data-layout=cards]').click();await page.select_option('#gridColumns','3');assert await page.locator('#sourcesGrid').get_attribute('data-columns')=='3'
  await check('Card/table layouts, column selection and layout persistence',table)
  async def bookmarks_compare():
   await reset()
   ids=await page.locator('#sourcesGrid [data-card]').evaluate_all('(xs)=>xs.slice(0,4).map(x=>x.dataset.card)')
   await page.locator('#sourcesGrid [data-fav="'+ids[0]+'"]').click()
   for id in ids[:3]: await page.locator('#sourcesGrid [data-compare="'+id+'"]').click()
   await page.locator('#sourcesGrid [data-compare="'+ids[3]+'"]').click();assert await page.locator('#utilityDialog').is_visible()
   await page.locator('[data-replace-compare]').first.click();assert await page.locator('#compareTrayCount').inner_text()=='3/3 selected'
   await nav('compare');values=[await page.locator('#cmp'+str(i)).input_value() for i in range(1,4)];assert len(set(values))==3;assert ids[3] in values
   await page.reload();await page.wait_for_selector('html[data-ready=true]');assert await page.locator('#cmp1').input_value()==ids[3]
   await nav('saved');assert await page.locator('#savedGrid [data-card]').count()==1
   await page.locator('#clearSaved').click();assert await page.locator('#savedGrid [data-card]').count()==0
   await page.locator('.toast-action',has_text='Undo').last.click();assert await page.locator('#savedGrid [data-card]').count()==1
  await check('Bookmarks, unique three-way comparison, replacement, reload and clear/undo',bookmarks_compare)
  note='Literal &amp; &#39; <script>alert("x")</script>\nاردو हिंदी العربية 🌿\n  spaces  \n'
  plan='academic-tutoring'
  async def openplan(p=page,id=plan):
   await p.evaluate('(id)=>document.querySelector("#sourcesGrid [data-open=\\\""+id+"\\\"]").click()',id)
   await p.wait_for_selector('#modal.on')
  async def notes_progress_history():
   await reset();await openplan();await page.locator('#noteInput').fill(note);await page.wait_for_timeout(550)
   assert 'Saved on this device' in await page.locator('#noteStatus').inner_text()
   await page.locator('[data-roadmap="0"]').check();await page.locator('[data-roadmap="2"]').check();await page.reload();await page.wait_for_selector('#modal.on')
   assert await page.locator('#noteInput').input_value()==note;assert await page.locator('[data-roadmap="0"]').is_checked();assert await page.locator('[data-roadmap="2"]').is_checked()
   await page.locator('#noteInput').fill('second version');await page.wait_for_timeout(550)
   await page.locator('#noteRecovery').click();await page.locator('.recovery-entry').nth(1).locator('summary').click();await page.locator('[data-restore-note="1"]').click()
   assert await page.locator('#noteInput').input_value()==note
   await page.locator('#mClose').click();await page.wait_for_timeout(300);assert await page.locator('#modal').get_attribute('aria-hidden')=='true'
   await nav('dashboard');assert await page.locator('#continuePanel').is_visible();assert plan in await page.locator('#continuePanel button').get_attribute('data-open')
  await check('Exact multilingual/entity notes, autosave, history restore, roadmap and resume',notes_progress_history)
  async def checklist_vault_widgets():
   await nav('dashboard');await page.locator('#widgetGrid [data-step=niche]').click();assert await page.locator('#widgetGrid [data-step=niche]').get_attribute('aria-pressed')=='true'
   await page.locator('#vaultInput').fill('Research &amp; العربية <b>idea</b>');await page.locator('#vaultForm button').click();assert 'Research &amp; العربية <b>idea</b>' in await page.locator('.vault-item').first.inner_text()
   await page.locator('[data-vault-delete="0"]').click();await page.locator('.toast-action',has_text='Undo').last.click();assert await page.locator('.vault-item').count()==1
   await page.locator('[data-whide=spotlight]').click();await page.wait_for_timeout(350);assert await page.locator('[data-widget=spotlight]').count()==0
   await page.locator('.toast-action',has_text='Undo').last.click();assert await page.locator('[data-widget=spotlight]').count()==1
   await nav('customize');before=await page.locator('#widgetList [data-wmove=down]').first.get_attribute('data-id');await page.locator('#widgetList [data-wmove=down]').first.click();assert await page.locator('#widgetList [data-wmove=down]').nth(1).get_attribute('data-id')==before
   await page.reload();await page.wait_for_selector('html[data-ready=true]');await nav('dashboard');assert await page.locator('.vault-item').count()==1
  await check('Checklist, vault exact text, delete/undo, widget hide/undo/reorder and persistence',checklist_vault_widgets)
  async def student():
   await nav('student');await page.locator('[data-preset=phone]').click();assert await page.locator('#studentGrid [data-card]').count()>0
   await page.locator('#weeklyHours').fill('7');await page.locator('#weeklyHours').dispatch_event('input');assert '7 h' in await page.locator('#hoursOutput').inner_text()
   hours=await page.locator('#studentGrid .meta').all_text_contents();assert all('8 hrs' not in x for x in hours)
   await page.reload();await page.wait_for_selector('html[data-ready=true]');assert await page.locator('#weeklyHours').input_value()=='7'
  await check('Student presets combined with persisted schedule matching',student)
  async def themes_motion():
   await nav('customize')
   for theme in ['dark','oled','neon','nature','light']:
    await page.locator('.theme-swatch[data-theme='+theme+']').click();assert await page.locator('html').get_attribute('data-theme')==theme
   await page.locator('[data-seg=motion] [data-val=off]').click();assert await page.evaluate('document.getAnimations().filter(x=>x.playState==="running").length')==0
   await page.locator('[data-seg=motion] [data-val=expressive]').click();await page.emulate_media(reduced_motion='reduce');await page.wait_for_timeout(100);assert await page.locator('html').get_attribute('data-motion')=='off';assert await page.evaluate('document.getAnimations().filter(x=>x.playState==="running").length')==0
   await page.emulate_media(reduced_motion='no-preference');await page.wait_for_timeout(100);await page.locator('[data-seg=motion] [data-val=subtle]').click()
   await page.wait_for_timeout(1500);assert await page.evaluate('document.getAnimations().filter(x=>x.playState==="running"&&x.effect.getTiming().iterations===Infinity).length')==0
  await check('All five themes, application motion off, OS reduced motion and no idle loops',themes_motion)
  async def dialogs_routing():
   await reset();trigger=page.locator('#sourcesGrid [data-open="'+plan+'"]');await trigger.click();await page.locator('#mFav').focus();await page.keyboard.press('Shift+Tab');assert await page.locator('#noteSave').evaluate('(x)=>x===document.activeElement')
   await page.keyboard.press('Tab');assert await page.locator('#mFav').evaluate('(x)=>x===document.activeElement')
   await page.keyboard.press('Escape');await page.wait_for_timeout(300);assert await trigger.evaluate('(x)=>x===document.activeElement')
   await page.go_forward();await page.wait_for_selector('#modal.on');assert '/plan/'+plan in page.url
   await page.go_back();await page.wait_for_timeout(300);assert not await page.locator('#modal').evaluate('(x)=>x.classList.contains("on")')
   await page.goto(URL+'#saved/plan/'+plan);await page.wait_for_selector('#modal.on');await page.keyboard.press('Escape');await page.wait_for_timeout(300);assert page.url.endswith('#saved')
   await page.locator('#helpBtn').click();await page.keyboard.press('Escape');assert await page.locator('#helpBtn').evaluate('(x)=>x===document.activeElement')
   await page.locator('#cmdkBtn').click();await page.locator('#paletteInput').fill('Academic Tutoring');await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');await page.wait_for_selector('#modal.on');await page.keyboard.press('Escape');await page.wait_for_timeout(250)
   await page.locator('#searchInput').fill('123');await page.keyboard.press('1');assert await page.locator('#searchInput').input_value()=='1231'
   await reset()
  await check('Dialog focus trap/restore, help, palette, shortcuts, history and deep links',dialogs_routing)
  exported={}
  async def backup():
   await nav('customize')
   async with page.expect_download() as info: await page.locator('#exportBackup').click()
   d=await info.value;path=ROOT/'qa'/'test-backup.json';await d.save_as(path);v=json.loads(path.read_text());exported.update(v);assert v['version']==2;assert v['notes'][plan]==note
   oldnote='Backup note &amp; اردو <b>literal</b>'
   v['notes'][plan]=oldnote;v['favorites']=['freelance-graphic-design'];v['vault']=['Imported idea'];v['settings']['theme']='neon'
   await page.locator('#backupInput').set_input_files({'name':'valid.json','mimeType':'application/json','buffer':json.dumps(v).encode()})
   assert await page.locator('#utilityDialog').is_visible();assert 'note conflict' in await page.locator('#utilityBody').inner_text()
   assert await page.locator('html').get_attribute('data-theme')=='light'
   await page.select_option('#importConflict','backup');await page.locator('#confirmImport').click();await reset();await openplan();assert await page.locator('#noteInput').input_value()==oldnote
   await page.locator('#noteRecovery').click();texts=await page.locator('.recovery-text').all_text_contents();assert note in texts
   await page.locator('#utilityClose').click();await page.locator('#mClose').click();await page.wait_for_timeout(250);await nav('customize')
   for invalid in [b'not json',b'{}',json.dumps({**v,'compare':['bad-id']}).encode(),json.dumps({**v,'compare':[plan,plan]}).encode(),json.dumps({**v,'notes':{plan:25}}).encode(),json.dumps({**v,'version':99}).encode()]:
    await page.locator('#backupInput').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':invalid});await page.wait_for_timeout(100);assert not await page.locator('#utilityDialog').is_visible()
   # Version 1 compatibility, no changes before confirmation/cancel.
   v['version']=1;await page.locator('#backupInput').set_input_files({'name':'v1.json','mimeType':'application/json','buffer':json.dumps(v).encode()});assert await page.locator('#utilityDialog').is_visible();await page.locator('#cancelImport').click()
   v['version']=2;v['notes'][plan]='Another imported note';await page.locator('#backupInput').set_input_files({'name':'appearance.json','mimeType':'application/json','buffer':json.dumps(v).encode()});await page.locator('#importAppearance').check();await page.locator('#confirmImport').click();assert await page.locator('html').get_attribute('data-theme')=='neon'
   await page.locator('.toast-action',has_text='Undo').last.click();assert await page.locator('html').get_attribute('data-theme')=='light';await reset();await openplan();assert await page.locator('#noteInput').input_value()==oldnote;await page.locator('#mClose').click();await page.wait_for_timeout(250)
  await check('Actual export download, import preview/merge/conflicts/recovery, invalid imports and v1 compatibility',backup)
  async def multitabs():
   other=await page_new();await reset();await reset(other)
   await openplan(page,'ai-content-writing');await openplan(other,'ai-content-writing')
   await page.locator('#noteInput').fill('Tab A العربية &amp;');await other.wait_for_function('document.querySelector("#noteInput").value==="Tab A العربية &amp;"',timeout=5000)
   await other.evaluate('()=>{const x=document.querySelector("#noteInput");x.value="Tab B unfinished";x.dispatchEvent(new Event("input",{bubbles:true}));}');await page.evaluate('()=>{document.querySelector("#noteInput").value="Tab A newer";document.querySelector("#noteSave").click();}');await other.wait_for_timeout(100)
   assert await other.locator('#noteInput').input_value()=='Tab B unfinished'
   await page.wait_for_function('document.querySelector("#noteInput").value==="Tab B unfinished"',timeout=5000)
   await page.locator('#noteRecovery').click();texts=await page.locator('.recovery-text').all_text_contents();assert 'Tab A newer' in texts;assert 'Tab B unfinished' in texts
   await page.locator('#utilityClose').click();await page.locator('#mClose').click();await other.locator('#mClose').click();await page.wait_for_timeout(250)
   await reset();await reset(other)
   # Concurrent edits to different entities survive without shared snapshot overwrites.
   await asyncio.gather(page.locator('#sourcesGrid [data-fav=extra-1]').click(),other.locator('#sourcesGrid [data-fav=extra-2]').click());await page.wait_for_timeout(300)
   await page.reload();await page.wait_for_selector('html[data-ready=true]');assert await page.locator('#sourcesGrid [data-fav=extra-1]').get_attribute('aria-pressed')=='true';assert await page.locator('#sourcesGrid [data-fav=extra-2]').get_attribute('aria-pressed')=='true'
   await other.close()
  await check('Two tabs: live sync, pending note drafts, conflict history and concurrent bookmarks',multitabs)
  async def storage_failures():
   for mode in ['corrupt','denied','quota']:
    c=await browser.new_context(viewport={'width':390,'height':844})
    if mode=='corrupt': await c.add_init_script("localStorage.setItem('hios.settings','{broken');localStorage.setItem('hios.favs',JSON.stringify(['academic-tutoring','bad']));")
    else: await c.add_init_script("Storage.prototype.setItem=function(){throw new DOMException('blocked','"+('QuotaExceededError' if mode=='quota' else 'SecurityError')+"')};"+("Storage.prototype.getItem=function(){throw new DOMException('blocked','SecurityError')};" if mode=='denied' else ''))
    p=await page_new(c);assert await p.locator('#sourcesGrid [data-card]').count()==30
    if mode=='corrupt': assert await p.evaluate("localStorage.getItem('hios.settings')")=='{broken'
    else:
     assert 'Session only' in await p.locator('#saveStatus').inner_text()
     await nav('sources',p);await p.locator('#sourcesGrid [data-fav=extra-1]').click();assert await p.locator('#sourcesGrid [data-fav=extra-1]').get_attribute('aria-pressed')=='true'
     await nav('customize',p)
     async with p.expect_download() as info: await p.locator('#exportBackup').click()
     assert await (await info.value).path()
    await c.close()
  await check('Corrupt legacy data retained; denied/quota storage stays usable and exportable',storage_failures)
  async def responsive():
   for width in [320,390,768,1024,1440]:
    await page.set_viewport_size({'width':width,'height':900})
    for tab in ['dashboard','sources','student','compare','path','saved','customize']:
     await nav(tab)
     overflow=await page.evaluate('document.documentElement.scrollWidth>innerWidth+1');assert not overflow,f'{tab} at {width}'
     if tab in ['dashboard','sources','compare','customize']:
      await page.screenshot(path=str(ROOT/'qa'/f'{tab}-{width}.png'),full_page=True)
    await nav('sources');await openplan();assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1');await page.screenshot(path=str(ROOT/'qa'/f'plan-{width}.png'));await page.locator('#mClose').click();await page.wait_for_timeout(250)
   await page.set_viewport_size({'width':640,'height':500});await page.evaluate('document.documentElement.style.fontSize="32px"')
   for tab in ['dashboard','sources','compare','customize']:
    await nav(tab);assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth+1'),tab+' 200% text'
   await page.reload()
  await check('Seven pages and plan dialog at 320/390/768/1024/1440; 200% text reflow',responsive)
  async def gestures():
   c=await browser.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True);p=await page_new(c);await nav('sources',p)
   async def pointer(kind,target,x=100,y=200):
    await p.locator(target).first.dispatch_event(kind,{'pointerId':7,'pointerType':'touch','isPrimary':True,'clientX':x,'clientY':y,'bubbles':True})
   target='#sourcesGrid [data-card=academic-tutoring] .ic';fav=p.locator('#sourcesGrid [data-fav=academic-tutoring]')
   await pointer('pointerdown',target);await pointer('pointermove',target,100,240);await p.wait_for_timeout(650);assert await fav.get_attribute('aria-pressed')=='false'
   await pointer('pointerdown',target);await pointer('pointercancel',target);await p.wait_for_timeout(650);assert await fav.get_attribute('aria-pressed')=='false'
   await pointer('pointerdown',target);await p.evaluate('document.dispatchEvent(new Event("scroll"))');await p.wait_for_timeout(650);assert await fav.get_attribute('aria-pressed')=='false'
   await pointer('pointerdown','#sourcesGrid [data-card=academic-tutoring] h3');await p.wait_for_timeout(650);assert await fav.get_attribute('aria-pressed')=='false'
   await pointer('pointerdown',target);await p.wait_for_timeout(650);assert await fav.get_attribute('aria-pressed')=='true';await pointer('pointerup',target)
   await p.wait_for_timeout(700);theme=await p.locator('html').get_attribute('data-theme');await p.locator('#sourcesGrid [data-card=academic-tutoring] h3').dblclick();assert await p.locator('html').get_attribute('data-theme')==theme
   # Real Chromium touch events through CDP to exercise pointer capture on rail.
   rail=await p.locator('#gestureRail').bounding_box();x=rail['x']+rail['width']*.8;y=rail['y']+rail['height']/2
   session=await c.new_cdp_session(p);await session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});await session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-100,'y':y}]});await session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});await p.wait_for_timeout(250);assert p.url.endswith('#student')
   await c.close()
  await check('Simulated touch: hold, move/scroll/pointercancel, text selection surface, no theme double-tap, rail swipe',gestures)
  async def accessibility():
   axe=pathlib.Path(AXE_PATH)
   if not axe.exists(): raise AssertionError('axe-core not installed for accessibility check')
   await page.set_viewport_size({'width':1440,'height':1000});await page.reload();await page.wait_for_selector('html[data-ready=true]');await page.add_script_tag(path=str(axe));reports=[]
   for tab in ['dashboard','sources','student','compare','path','saved','customize']:
    await nav(tab);await page.wait_for_timeout(300)
    r=await page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
    reports.extend({'page':tab,'id':x['id'],'impact':x['impact'],'nodes':[n['target'] for n in x['nodes']]} for x in r['violations'])
   (ROOT/'qa'/'accessibility.json').write_text(json.dumps(reports,indent=2))
   assert not reports,json.dumps(reports)[:3000]
  await check('Automated axe WCAG A/AA checks across seven pages',accessibility)
  async def migration_offline():
   c=await browser.new_context();legacy={'settings':{'theme':'dark','hue':190,'widgets':{'vault':{'on':True,'wide':True}}},'favs':['academic-tutoring'],'notes':{'academic-tutoring':'Legacy &amp; العربية\n'},'checklist':['niche','tools'],'vault':['https://hello.example.com/path.some العربية','Legacy idea'],'compare':['academic-tutoring','ai-content-writing']}
   p=await c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));await p.goto(URL);await p.evaluate('(data)=>{localStorage.clear();for(const [k,v] of Object.entries(data))localStorage.setItem("hios."+k,JSON.stringify(v));localStorage.setItem("hios.op.corrupt",JSON.stringify({id:"corrupt",at:1,patch:{"settings":7,"settings.widgets.stats.on":true}}));}',legacy)
   await p.reload();await p.wait_for_selector('html[data-ready=true]');assert await p.locator('html').get_attribute('data-theme')=='dark';await nav('saved',p);assert await p.locator('#savedGrid [data-card]').count()==1
   await p.locator('#savedGrid [data-open=academic-tutoring]').click();assert await p.locator('#noteInput').input_value()=='Legacy &amp; العربية\n';await p.locator('#mClose').click();await p.wait_for_timeout(250);await nav('dashboard',p)
   assert await p.locator('.vault-item').count()==2;assert 'https://hello.example.com/path.some العربية' in await p.locator('.vault-list').inner_text()
   await p.locator('#vaultInput').fill('new.example.net العربية');await p.locator('#vaultForm button').click();await p.reload();assert 'new.example.net العربية' in await p.locator('.vault-list').inner_text()
   assert await p.evaluate('JSON.parse(localStorage.getItem("hios.notes"))["academic-tutoring"]')=='Legacy &amp; العربية\n'
   await c.close()
   c=await browser.new_context(offline=True)
   await c.route('**/Halal-Income-Enhanced.html',lambda route:route.fulfill(body=(ROOT/'Halal-Income-Enhanced.html').read_text(),content_type='text/html'))
   p=await c.new_page();p.on('pageerror',lambda e:errors.append(str(e)));requests=[];p.on('request',lambda r:requests.append((r.url,r.resource_type)));await p.goto(URL+'#sources');await p.wait_for_selector('html[data-ready=true]');assert await p.locator('#sourcesGrid [data-card]').count()==30;await openplan(p);await p.locator('#noteInput').fill('Offline note &amp;');await p.wait_for_timeout(550);await p.reload();await p.wait_for_selector('#modal.on');assert await p.locator('#noteInput').input_value()=='Offline note &amp;';assert all(kind=='document' and url.startswith(URL) for url,kind in requests);await c.close()
  await check('Legacy migration, malformed journal, dotted multilingual vault text and network-disabled HTML runtime',migration_offline)
  async def themes_dialog_axe():
   await page.set_viewport_size({'width':390,'height':844});await nav('customize');issues=[]
   if not await page.evaluate('typeof axe!=="undefined"'):await page.add_script_tag(path=AXE_PATH)
   async def scan(label):
    await page.wait_for_timeout(350)
    r=await page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
    issues.extend({'view':label,'id':v['id'],'nodes':[n['target'] for n in v['nodes']]} for v in r['violations'])
   for theme in ['light','dark','oled','neon','nature']:
    await page.locator('.theme-swatch[data-theme='+theme+']').click();await scan('studio-'+theme)
    await nav('sources');await scan('explorer-'+theme);await openplan();await scan('plan-'+theme);await page.locator('#noteRecovery').click();await scan('history-'+theme);await page.locator('#utilityClose').click();await page.locator('#mClose').click();await page.wait_for_timeout(250);await nav('customize')
   await page.locator('.theme-swatch[data-theme=light]').click();await page.locator('#helpBtn').click();await scan('help');await page.keyboard.press('Control+k');assert await page.locator('#palette.on').count()==1;assert await page.locator('#helpOverlay.on').count()==0;await scan('palette');await page.keyboard.press('Escape')
   (ROOT/'qa'/'theme-dialog-accessibility.json').write_text(json.dumps(issues,indent=2));assert not issues,json.dumps(issues)[:4000]
  await check('Mobile axe scans: five themes, plan/history dialogs, help and palette stacking',themes_dialog_axe)
  await check('No uncaught browser JavaScript errors',lambda:assert_async(not errors,str(errors)))
  await browser.close()
 (ROOT/'qa'/'results.json').write_text(json.dumps(results,indent=2))
 print(f'{sum(x["result"]=="passed" for x in results)}/{len(results)} groups passed')
 if any(x['result']=='failed' for x in results):raise SystemExit(1)
async def assert_async(v,msg):assert v,msg
asyncio.run(main())
