import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const port=Number(process.env.DOTS_DEMO_PORT||9024);
if(!Number.isInteger(port)||port<1024||port>65535)throw new Error('DOTS_DEMO_PORT must be an integer from 1024 to 65535.');
const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8','.png':'image/png','.gif':'image/gif','.mp4':'video/mp4','.ttf':'font/ttf','.md':'text/plain; charset=utf-8'};
http.createServer((req,res)=>{
  let local;try{local=decodeURIComponent(new URL(req.url,'http://localhost').pathname)}catch{res.writeHead(400);res.end();return}
  const target=path.resolve(root,'.'+(local==='/'?'/index.html':local));
  if(target!==root&&!target.startsWith(root+path.sep)){res.writeHead(403);res.end();return}
  fs.stat(target,(err,stat)=>{if(err||!stat.isFile()){res.writeHead(404);res.end('File not found');return}
    const range=req.headers.range;const headers={'Content-Type':types[path.extname(target)]||'application/octet-stream','Cache-Control':'no-cache','Accept-Ranges':'bytes'};
    if(range){const match=/^bytes=(\d+)-(\d*)$/.exec(range);if(!match){res.writeHead(416);res.end();return}const start=Number(match[1]),end=match[2]?Math.min(Number(match[2]),stat.size-1):stat.size-1;if(start>end||start>=stat.size){res.writeHead(416);res.end();return}res.writeHead(206,{...headers,'Content-Range':`bytes ${start}-${end}/${stat.size}`,'Content-Length':end-start+1});fs.createReadStream(target,{start,end}).pipe(res)}
    else{res.writeHead(200,{...headers,'Content-Length':stat.size});fs.createReadStream(target).pipe(res)}
  });
}).listen(port,'127.0.0.1',()=>console.log(`Dots demo: http://127.0.0.1:${port}`));
