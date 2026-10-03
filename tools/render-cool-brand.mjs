// Raster exports from our original vector source; optional Sharp dependency.
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(import.meta.url);
let sharp;
try{sharp=require('sharp');}catch(error){
  if(!process.env.DOTS_NODE_MODULES)throw new Error('Install optional development tools with npm ci, or set DOTS_NODE_MODULES.',{cause:error});
  sharp=require(path.join(process.env.DOTS_NODE_MODULES,'sharp'));
}
for(const [name,width] of [['logo-cool',1600],['icon-cool',512]]){
  const source=`brand/${name}.svg`;
  const metadata={source,renderer:'tools/render-cool-brand.mjs',creator:'Original Dots on Paper vector artwork',license:'MIT; Figtree lettering SIL OFL',transparent_background:true};
  const bytes=await sharp(path.join(root,source)).resize(width).png().withMetadata().withExif({IFD0:{ImageDescription:JSON.stringify(metadata)}}).toBuffer();
  await fs.writeFile(path.join(root,'brand',`${name}.png`),bytes);
  const info=await sharp(bytes).metadata();
  await fs.writeFile(path.join(root,'brand',`${name}.png.provenance.json`),JSON.stringify({...metadata,width:info.width,height:info.height,sha256:createHash('sha256').update(bytes).digest('hex')},null,2)+'\n');
}
console.log('Exported transparent Cool logo and 512-pixel icon from original vector sources.');
