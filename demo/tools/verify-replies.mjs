import {createRequire} from 'node:module';
import {homedir} from 'node:os';
import {join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {mkdir,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';

let require=createRequire(import.meta.url),chromium;
try{({chromium}=require('playwright'))}catch{
  require=createRequire(join(homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/package.json'));
  ({chromium}=require('playwright'));
}
const root=dirname(dirname(fileURLToPath(import.meta.url)));
const out=join(root,'.impeccable/review');await mkdir(out,{recursive:true});
const options=process.env.DOTS_BROWSER_PATH?{executablePath:process.env.DOTS_BROWSER_PATH}:process.platform==='win32'?{executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'}:{};
const browser=await chromium.launch({headless:true,...options});
const context=await browser.newContext({viewport:{width:1440,height:1120},acceptDownloads:true});
const errors=[];
async function open(url,reducedMotion){
  const page=await context.newPage();if(reducedMotion)await page.emulateMedia({reducedMotion});
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(url);await page.evaluate(async()=>{await dotDemo.ready;await dotDemo.allDotsReady;dotDemo.pause()});return page;
}
const base=process.env.DOTS_DEMO_URL||'http://127.0.0.1:9024';
try{
  const page=await open(`${base}/?example=calendar-chaos`);
  const fixtures=[
    ['paragraph','Your build is ready. I fixed the navigation, checked the mobile layout, and left the details in your conversation.'],
    ['list','Here is the plan:\n\n- Review the draft with the team.\n- Book the train.\n- Buy the groceries before dinner.\n- Reply to the venue about access and their longer setup instructions.\n- Take a break.\n\nEverything else can wait.'],
    ['unicode','Tomorrow’s plan — Rīga, café, and a little breathing room.\n\n1. Meet Zoë at 09:30.\n2. Check the tickets.\n\nYou’re all set.'],
    ['numbered','A numbered reply:\n\n9. Meet the team.\n10. Check the longer item with room for its number.\n11. Take a break.'],
    ['word','A'.repeat(280)],
    ['long','This is a deliberately long response that remains available in the conversation. '.repeat(48).slice(0,4000)]
  ];
  for(const [name,value] of fixtures){
    const result=await page.evaluate(value=>{
      dotDemo.setAnswer(value);dotDemo.renderAt(9,{format:'screen',export:true,hold:true});
      return {state:dotDemo.state,layout:dotDemo.replyLayout(value),data:dotDemo.canvas.toDataURL('image/png').split(',')[1]};
    },value);
    assert.equal(result.state.customAnswer,value.trim());assert.equal(result.state.example,'');
    assert(result.layout.rows.length);assert(result.layout.rows.every(row=>row.y+result.layout.lineHeight<=760));
    if(name==='long'){assert.equal(result.layout.truncated,true);assert.match(result.layout.rows.at(-1).text,/…$/)}
    else assert.equal(result.layout.truncated,false);
    if(name==='numbered'){const items=result.layout.rows.filter(row=>row.marker);assert.equal(new Set(items.map(row=>row.x)).size,1);assert(items.every(row=>row.x>=96));}
    await writeFile(join(out,`reply-${name}.png`),Buffer.from(result.data,'base64'));
  }
  await page.evaluate(()=>{dotDemo.setAnswer('Here is your reply.\n\n- One thing.\n- Another thing.\n\nA perfectly ordinary answer.');dotDemo.pause()});
  for(const dot of ['artist','curious','bookish','cool']){
    await page.locator(`[data-dot="${dot}"]`).click();assert.equal((await page.evaluate(()=>dotDemo.state)).dot,dot);
    assert.match(await page.locator('#scene').getAttribute('aria-label'),/perfectly ordinary answer/);
  }
  const downloadPromise=page.waitForEvent('download');await page.locator('#save-screen').click();
  const download=await downloadPromise;assert.equal(download.suggestedFilename(),'dot-reply-cool-screen.png');
  await download.saveAs(join(out,'reply-downloaded.png'));
  assert.equal(await page.locator('#download-film span').textContent(),'Save picture');
  await page.locator('[data-example="wife-noo"]').click();
  assert.equal((await page.evaluate(()=>dotDemo.state)).example,'wife-noo');
  assert.match(await page.locator('#scene').getAttribute('aria-label'),/FICTIONAL DEMO.*NOO.*Nothing sent/);
  for(const t of [0,4,8.4,12]){
    const data=await page.evaluate(t=>{dotDemo.renderAt(t,{format:'screen',export:true});return dotDemo.canvas.toDataURL('image/png').split(',')[1]},t);
    await writeFile(join(out,`noo-${t}.png`),Buffer.from(data,'base64'));
  }
  await page.evaluate(()=>dotDemo.renderAt(12,{format:'scene',export:true}));
  await page.screenshot({path:join(out,'reply-desktop.png'),fullPage:true});
  const mobile=await open(`${base}/?example=calendar-chaos`);await mobile.setViewportSize({width:390,height:844});
  await mobile.locator('#edit-toggle').click();
  await mobile.screenshot({path:join(out,'reply-mobile-editor.png'),fullPage:true});
  assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth),390);
  const dimensions=await mobile.locator('#answer').boundingBox();assert(dimensions.width>=340);
  const reduced=await open(`${base}/?example=wife-noo`,'reduce');
  assert.equal((await reduced.evaluate(()=>dotDemo.state)).seconds,12);
  await reduced.locator('#edit-toggle').click();await reduced.locator('#answer').fill('A calmer reply.');
  await reduced.locator('button[type="submit"]').click();
  const state=await reduced.evaluate(()=>dotDemo.state);assert.equal(state.playing,false);assert.equal(state.seconds,9);
  assert.deepEqual(errors,[]);
  console.log('Generic reply fixtures, all characters, actual screen download, NOO timeline, mobile editor, and reduced-motion reply verified.');
}finally{await browser.close()}
