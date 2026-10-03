// Optional marketing build: Playwright + Sharp. No cloud service or credentials.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require=createRequire(import.meta.url);
function dependency(name){
  try{return require(name);}catch(error){
    if(process.env.DOTS_NODE_MODULES)return require(path.join(process.env.DOTS_NODE_MODULES,name));
    throw new Error(`To rebuild brand PNGs, install ${name}, or set DOTS_NODE_MODULES to your development node_modules.`,{cause:error});
  }
}
const sharp=dependency('sharp');
const {chromium}=dependency('playwright');
const brand=path.join(root,'brand');
const haBrand=path.join(root,'custom_components','dots_on_paper','brand');
await fs.mkdir(haBrand,{recursive:true});
const provenance={source:'tools/build-brand.mjs',vector_source:'tools/build_brand.py',artwork:'Original Dots on Paper folded-sheet/four-dot identity',license:'MIT',external_messages_sent:false};
async function png(source,destination,options={}){
  const description={...provenance,source_artwork:options.source,scripted_scene:options.source?.includes('campaign/')||false};
  const buffer=await sharp(source).resize(options.width||512,options.height).png().withMetadata().withExif({IFD0:{ImageDescription:JSON.stringify(description),Software:'Dots on Paper brand build'}}).toBuffer();
  await fs.writeFile(destination,buffer);
  const meta=await sharp(buffer).metadata();
  await fs.writeFile(destination.replace(/\.png$/,'.provenance.json'),JSON.stringify({...description,width:meta.width,height:meta.height,sha256:createHash('sha256').update(buffer).digest('hex')},null,2)+'\n');
}
await png(path.join(brand,'icon.svg'),path.join(brand,'icon.png'),{source:'brand/icon.svg'});
await png(path.join(brand,'icon-dark.svg'),path.join(haBrand,'dark_icon.png'),{source:'brand/icon-dark.svg'});
await png(path.join(brand,'icon.svg'),path.join(haBrand,'icon.png'),{source:'brand/icon.svg'});
await png(path.join(brand,'logo.svg'),path.join(haBrand,'logo.png'),{width:1024,source:'brand/logo.svg'});
await png(path.join(brand,'logo-dark.svg'),path.join(haBrand,'dark_logo.png'),{width:1024,source:'brand/logo-dark.svg'});
const options={headless:true};
if(process.env.DOTS_BROWSER)options.executablePath=process.env.DOTS_BROWSER;else if(process.platform==='win32')options.channel='msedge';
const browser=await chromium.launch(options);
try{
  const page=await browser.newPage({viewport:{width:1280,height:640},deviceScaleFactor:1});
  await page.goto(pathToFileURL(path.join(brand,'social-preview.html')).href);
  await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(image=>image.decode()));});
  await png(await page.screenshot(),path.join(brand,'social-preview.png'),{width:1280,height:640,source:'brand/social-preview.html; campaign/media/dot-reminders-native.png (scripted scene)'});
  // A small/large contact sheet makes one bounded check cover the shipped marks.
  const review=await browser.newPage({viewport:{width:1000,height:530},deviceScaleFactor:1});
  const uri=name=>pathToFileURL(path.join(brand,name)).href;
  await review.goto(uri('social-preview.html'));
  await review.setContent(`<style>body{margin:0;font:16px sans-serif;background:#dfe9e3;color:#1d2925;padding:38px}section{display:flex;gap:34px;align-items:center;padding:30px 0}img{object-fit:contain}.dark{background:#1d2925;padding:26px}</style><img src="${uri('logo.svg')}" width="730" alt="Wordmark"><section><img src="${uri('icon.svg')}" width="256"><img src="${uri('icon.svg')}" width="64"><img src="${uri('icon.svg')}" width="32"><span class="dark"><img src="${uri('logo-dark.svg')}" width="390"></span></section>`);
  await review.evaluate(()=>Promise.all([...document.images].map(image=>image.decode())));
  await png(await review.screenshot(),path.join(brand,'review.png'),{width:1000,height:530,source:'brand/icon.svg, brand/logo.svg, brand/logo-dark.svg at large and small sizes'});
}finally{await browser.close();}
console.log('Built original brand icon, Home Assistant light/dark branding, and 1280×640 social preview.');
