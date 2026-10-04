/* A deterministic thinking-to-reply performance. No accounts or device connection. */
(() => {
  'use strict';
  const canvas = document.getElementById('scene');
  const ctx = canvas.getContext('2d', {alpha:false});
  const ink = '#1d2925', ground = '#dfe9e3', paper = '#f2f3ed';
  const duration = 16;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const q = id => document.getElementById(id);
  const calendarExample={sender:'heidot',text:'Here are your reminders:\n\n- Tonight: Date with Paula.\n- Tomorrow morning: Breakfast with Amy.\n- Lunch: With your wife.\n\nYour calendar needs a lawyer.'};
  const nooExample={sender:'heidot',notice:'FICTIONAL DEMO · DRAFT ONLY',messages:[
    {role:'assistant',at:2.8,text:'Okay, understood. Texting your wife about your date with Paula tonight.',status:'Draft ready · Waiting for approval'},
    {role:'user',at:8,text:'NOO'},
    {role:'assistant',at:10.6,text:'Cancelled. Nothing sent.'}
  ]};
  const presets={'calendar-chaos':calendarExample,'wife-noo':nooExample};
  const requestedExample=new URLSearchParams(location.search).get('example');
  let example=presets[requestedExample]?requestedExample:'';
  const companions = {
    artist:{name:'Artist',description:'a black beret',src:'beret-dot.png',style:'plain',eyeX:.102,eyeY:.121,bob:1,tilt:1},
    curious:{name:'Curious',description:'googly eyes',src:'curious-dot.png',style:'raised',eyeX:.14,eyeY:-.15,bob:1.35,tilt:1.2},
    bookish:{name:'Bookish',description:'round glasses',src:'bookish-dot.png',style:'glasses',eyeX:.12,eyeY:.1,bob:.5,tilt:.55},
    cool:{name:'Cool',description:'sunglasses and a heart-shaped body',src:'cool-dot.png',style:'sunglasses',eyeX:.12,eyeY:.08,bob:.65,tilt:1.25}
  };
  Object.values(companions).forEach(dot=>{dot.image=new Image();dot.loaded=false});
  let selectedDot=example?'cool':'artist';
  let playing = !reduced&&!example, format = 'scene', mode = 'smooth', seconds = reduced||example ? (example==='wife-noo'?12:9) : 0;
  let baseTime = performance.now(), baseSeconds = seconds, lastState = '', customAnswer = '';
  let assetsReady = false;
  const clamp = (v,a=0,b=1) => Math.min(b,Math.max(a,v));
  const ease = t => 1 - Math.pow(1-clamp(t),4);
  const smooth = t => {t=clamp(t);return t*t*(3-2*t)};
  const lerp = (a,b,t) => a+(b-a)*t;
  function roundRect(c,x,y,w,h,r){c.beginPath();c.roundRect(x,y,w,h,r)}
  function circle(c,x,y,r,color=ink){c.beginPath();c.arc(x,y,r,0,Math.PI*2);c.fillStyle=color;c.fill()}
  function text(c,str,x,y,size=24,weight=500,align='left',color=ink){c.font=`${weight} ${size}px Figtree`;c.textAlign=align;c.textBaseline='alphabetic';c.fillStyle=color;c.fillText(str,x,y)}
  function dotMark(c,x,y,s=1,color=ink){c.save();c.translate(x,y);c.scale(s,s);[[0,0],[18,-10],[18,10],[36,0]].forEach(([a,b])=>circle(c,a,b,6,color));c.restore()}
  function drawCompanion(c,dot,size,t,awake,thinking,answer,motion){
    if(dot.loaded)c.drawImage(dot.image,-size/2,-size/2,size,size);
    const unit=size/760;
    const blinkCenters=[1.65,4.3,8.8,11.3,13.2,15.15];let openness=lerp(.11,1,awake);
    for(const b of blinkCenters)openness*=1-.93*Math.max(0,1-Math.abs(t-b)/.115);
    const gazeX=(Math.sin(t*1.7)*11*thinking)*motion*unit;
    const gazeY=(-14*thinking+8*(1-awake))*unit;
    const eyeY=size*dot.eyeY;
    c.fillStyle='#151b18';c.strokeStyle='#151b18';c.lineCap='round';
    if(dot.style==='sunglasses'){
      c.lineWidth=7*unit;
      c.beginPath();c.moveTo(-size*dot.eyeX+52*unit,eyeY);c.quadraticCurveTo(0,eyeY-13*unit,size*dot.eyeX-52*unit,eyeY);c.stroke();
      [-1,1].forEach(side=>{
        c.beginPath();c.ellipse(side*size*dot.eyeX,eyeY,58*unit,53*unit,-side*.08,0,Math.PI*2);c.fill();
        c.save();c.globalAlpha=.2;c.strokeStyle='#f2f3ed';c.lineWidth=4*unit;
        c.beginPath();c.moveTo(side*size*dot.eyeX-23*unit,eyeY-20*unit);c.lineTo(side*size*dot.eyeX-6*unit,eyeY-29*unit);c.stroke();c.restore();
      });
    }else{
      [-1,1].forEach(side=>{
        let h=(dot.style==='raised'?38:28)*openness*unit;
        if(side===1&&t>10.1&&t<10.52)h=5*unit;
        c.beginPath();c.ellipse(side*size*dot.eyeX+gazeX,eyeY+gazeY,(dot.style==='raised'?28:13)*unit,Math.max(3*unit,h),-.06*side,0,Math.PI*2);c.fill();
      });
      if(dot.style==='glasses'){
        c.lineWidth=6*unit;
        [-1,1].forEach(side=>{c.beginPath();c.arc(side*size*dot.eyeX,eyeY,55*unit,0,Math.PI*2);c.stroke()});
        c.beginPath();c.moveTo(-size*dot.eyeX+55*unit,eyeY-5*unit);c.quadraticCurveTo(0,eyeY-18*unit,size*dot.eyeX-55*unit,eyeY-5*unit);c.stroke();
      }
    }
    if(answer>.2){
      c.save();c.globalAlpha=answer;c.lineWidth=5*unit;
      // The raised-eyed dot's smile belongs on its body, below its eye globes.
      const mouthY=dot.style==='raised'?size*.17:eyeY+53*unit;
      c.beginPath();c.arc(dot.style==='sunglasses'?7*unit:0,mouthY,18*unit,.13*Math.PI,dot.style==='sunglasses'?.72*Math.PI:.87*Math.PI);c.stroke();c.restore();
    }
  }
  function drawAvatar(id){
    const avatar=document.querySelector(`[data-dot="${id}"] .dot-avatar`);
    const ac=avatar.getContext('2d');ac.clearRect(0,0,120,112);ac.save();ac.translate(60,56);
    drawCompanion(ac,companions[id],112,9,1,0,1,0);ac.restore();
  }
  function activeReply(opts={}){
    if(opts.reply!==undefined){
      const value=typeof opts.reply==='string'?{text:opts.reply}:opts.reply;
      return value&&typeof value.text==='string'?{sender:value.sender||'heidot',text:value.text}:null;
    }
    if(customAnswer)return {sender:'heidot',text:customAnswer};
    return (opts.example??example)==='calendar-chaos'?calendarExample:null;
  }
  function replyBlocks(value){
    const blocks=[];let paragraph=[];
    const clean=line=>line.replace(/\*\*(.*?)\*\*/g,'$1').replace(/`([^`]+)`/g,'$1');
    const flush=()=>{if(paragraph.length){blocks.push({type:'paragraph',text:clean(paragraph.join(' '))});paragraph=[]}};
    for(const line of String(value).replace(/\r\n?/g,'\n').trim().split('\n')){
      if(!line.trim()){flush();continue}
      const item=line.match(/^\s*(?:([-*•])|(\d+)[.)])\s+(.+)$/);
      if(item){flush();blocks.push({type:'item',marker:item[2]?item[2]+'.':'•',text:clean(item[3])});continue}
      const heading=line.match(/^\s*#{1,6}\s+(.+)$/);
      if(heading){flush();blocks.push({type:'heading',text:clean(heading[1])});continue}
      paragraph.push(line.trim());
    }
    flush();return blocks;
  }
  function wrapReply(c,value,width,size,weight){
    c.font=`${weight} ${size}px Figtree`;
    const lines=[];let line='';
    for(const word of value.split(/\s+/)){
      if(line&&c.measureText(line+' '+word).width<=width){line+=' '+word;continue}
      if(line){lines.push(line);line=''}
      for(const letter of word){
        if(line&&c.measureText(line+letter).width>width){lines.push(line);line=''}
        line+=letter;
      }
    }
    if(line)lines.push(line);
    return lines;
  }
  function replyLayout(c,value,width=1320,height=760){
    const blocks=replyBlocks(value);let layout;
    for(const size of [64,60,56,52,48]){
      const lineHeight=Math.round(size*1.38),groupGap=Math.round(size*.48),itemGap=Math.round(size*.22);
      c.font=`500 ${size}px Figtree`;
      const markerWidths=blocks.filter(block=>block.type==='item').map(block=>block.marker==='•'?18:c.measureText(block.marker).width);
      const listIndent=markerWidths.length?Math.ceil(Math.max(...markerWidths)+size*.36):0;
      let y=0,previous='';const rows=[];
      for(const block of blocks){
        if(rows.length)y+=block.type==='item'&&previous==='item'?itemGap:groupGap;
        const indent=block.type==='item'?listIndent:0,weight=block.type==='heading'?650:500;
        const lines=wrapReply(c,block.text,width-indent,size,weight);
        lines.forEach((line,i)=>{rows.push({text:line,x:indent,y,marker:i===0?block.marker:'',weight});y+=lineHeight});
        previous=block.type;
      }
      layout={rows,size,lineHeight,height:y,truncated:false};
      if(y<=height)return layout;
    }
    const visible=layout.rows.filter(row=>row.y+layout.lineHeight<=height);
    if(visible.length){
      const row=visible.at(-1);c.font=`${row.weight} ${layout.size}px Figtree`;
      let line=row.text;while(line&&c.measureText(line+'…').width>width-row.x)line=Array.from(line).slice(0,-1).join('');
      row.text=line.replace(/[.,;: ]+$/,'')+'…';
    }
    return {...layout,rows:visible,truncated:true};
  }
  function setDot(id){
    if(!companions[id]?.loaded)return false;
    selectedDot=id;
    document.querySelectorAll('.dot-choice').forEach(button=>{const active=button.dataset.dot===id;button.classList.toggle('active',active);button.setAttribute('aria-pressed',active)});
    const reply=activeReply(),conversation=activeConversation();
    canvas.setAttribute('aria-label',conversation?`${conversation.notice}. ${conversation.sender}, represented by ${companions[id].name}: ${conversation.messages.map(message=>`${message.role}: ${message.text}`).join(' ')}`:reply?`${reply.sender}, represented by ${companions[id].name}: ${replyBlocks(reply.text).map(block=>block.text).join(' ')}`:`A grayscale plush ${companions[id].name} dot with ${companions[id].description} thinks, then answers on a TRMNL X e-ink display.`);
    const suffix=id==='artist'?'':`-${id}`;
    q('download-film').href=example?`exports/${example}-poster-${id}.png`:`exports/dots-on-paper${suffix}.mp4`;
    q('download-film').querySelector('span').textContent=example||customAnswer?'Save picture':'Download film';
    q('download-film').setAttribute('aria-label',`Save ${companions[id].name}'s ${example||customAnswer?'picture':'film'}`);
    q('save-screen').href=example?`exports/${example}-screen-1872x1404-${id}.png`:`exports/screen-1872x1404${suffix}.png`;
    lastState='';renderAt(seconds);ui(seconds);return true;
  }
  function setExample(id){
    if(id!==''&&!presets[id])return false;
    example=id;customAnswer='';q('answer').value=presets[id]?.text||'Good ideas deserve a little paper.';
    document.querySelector('h1').textContent='A little dot. A lot to say.';
    document.title=example?'dots on paper — simulated reply':'dots on paper — a TRMNL X daydream';
    document.querySelectorAll('[data-example]').forEach(button=>{const active=button.dataset.example===example;button.classList.toggle('active',active);button.setAttribute('aria-pressed',active)});
    setDot(selectedDot);return true;
  }
  function setAnswer(value){
    customAnswer=String(value).trim().slice(0,4000);example='';q('answer').value=customAnswer;
    document.querySelectorAll('[data-example]').forEach(button=>{button.classList.toggle('active',false);button.setAttribute('aria-pressed',false)});
    document.querySelector('h1').textContent='A little dot. A lot to say.';document.title='dots on paper — a TRMNL X daydream';setDot(selectedDot);
  }
  document.querySelectorAll('.dot-choice').forEach(button=>button.onclick=()=>setDot(button.dataset.dot));
  document.querySelectorAll('[data-example]').forEach(button=>button.onclick=()=>{pause();seconds=button.dataset.example==='wife-noo'?12:9;setExample(button.dataset.example)});
  function activeConversation(opts={}){return opts.conversation??((opts.example??example)==='wife-noo'?nooExample:null)}

  // Stable fine fibers belong to the e-paper surface, never to an animated shader.
  const fibers = document.createElement('canvas');fibers.width=468;fibers.height=351;
  const fc=fibers.getContext('2d');const pixels=fc.createImageData(468,351);let seed=79037;
  for(let i=0;i<pixels.data.length;i+=4){seed=(Math.imul(seed,1664525)+1013904223)>>>0;const n=(seed>>>24)%17;pixels.data[i]=29;pixels.data[i+1]=41;pixels.data[i+2]=37;pixels.data[i+3]=n>12?8:0}fc.putImageData(pixels,0,0);

  function stateAt(t){return t<2.15?'Daydreaming':t<5.65?'Thinking':t<6.8?'An idea!':'Reply'}
  function answerLayout(c){
    const value=customAnswer||'Good ideas deserve a little paper.';
    if(!customAnswer||customAnswer==='Good ideas deserve a little paper.')return {lines:['Good ideas deserve','a little paper.'],size:91};
    let layout;
    for(const size of [91,74,68,62,56,50]){
      c.font=`600 ${size}px Figtree`;const lines=[];let line='';
      for(const word of value.split(/\s+/)){
        if(line&&c.measureText(line+' '+word).width<=1510){line+=' '+word;continue}
        if(line){lines.push(line);line=''}
        for(const letter of word){if(line&&c.measureText(line+letter).width>1510){lines.push(line);line=''}line+=letter}
      }
      if(line)lines.push(line);
      layout={lines,size};
      if(lines.length<=2||(lines.length<=3&&size<=74))return layout;
    }
    return layout;
  }
  function drawScreen(c,t,opts={}){
    if(opts.screenImage){c.drawImage(opts.screenImage,0,0,1872,1404);return}
    const conversation=activeConversation(opts);
    if(conversation){drawConversationScreen(c,t,conversation,opts);return}
    const reply=activeReply(opts);
    if(reply){drawReplyScreen(c,t,reply,opts);return}
    const dot=companions[opts.dot]||companions[selectedDot];
    const stepped=(opts.mode||mode)==='ink';
    if(stepped)t=Math.floor(t*5)/5;
    const motion=reduced&&!opts.export?0:1;
    c.save();c.fillStyle=paper;c.fillRect(0,0,1872,1404);
    c.globalAlpha=.75;c.drawImage(fibers,0,0,1872,1404);c.globalAlpha=1;
    dotMark(c,111,111,1.18);text(c,'dots',173,126,44,700);
    const awake=smooth((t-.6)/1.0)*(1-smooth((t-14.3)/1.1));
    const thinking=smooth((t-2.15)/.5)*(1-smooth((t-5.65)/.5));
    const aha=smooth((t-5.65)/.28)*(1-smooth((t-6.75)/.4));
    const answer=ease((t-6.75)/.65)*(opts.hold?1:1-smooth((t-14.0)/.8));
    const bob=(Math.sin(t*2.5)*8*awake+Math.sin(t*4.2)*10*thinking)*motion*dot.bob;
    const jump=Math.sin(clamp((t-5.7)/.95)*Math.PI)*-51*motion;
    const tilt=(Math.sin(t*2.15)*.035*thinking-Math.sin(clamp((t-5.7)/1.0)*Math.PI)*.055)*motion*dot.tilt;
    const squish=1+Math.sin(clamp((t-5.5)/1.25)*Math.PI*2)*.07*motion;
    const size=lerp(760,690,answer);
    const cy=lerp(666,597,answer)+bob+jump;
    // A soft contact shadow keeps the dot sitting on a sheet of paper.
    c.save();c.globalAlpha=.1;c.fillStyle=ink;c.beginPath();c.ellipse(936,lerp(926,dot.style==='sunglasses'?838:855,answer),238*(2-squish),24,0,0,Math.PI*2);c.fill();c.restore();
    c.save();c.translate(936,cy);c.rotate(tilt);c.scale(2-squish,squish);
    drawCompanion(c,dot,size,t,awake,thinking,answer,motion);
    c.restore();
    if(thinking>.01){
      c.save();c.globalAlpha=thinking;
      for(let i=0;i<3;i++){const pulse=(Math.sin(t*5.5-i*1.35)+1)/2;circle(c,1284+i*53,420-(i*22)-pulse*13*motion,12+5*pulse)}
      c.restore();
    }
    if(aha>.01){
      c.save();c.globalAlpha=aha;c.translate(1264,396);c.rotate(t*.07);c.strokeStyle=ink;c.lineWidth=6;c.lineCap='round';
      for(let i=0;i<6;i++){const a=i*Math.PI/3;c.beginPath();c.moveTo(Math.cos(a)*21,Math.sin(a)*21);c.lineTo(Math.cos(a)*43,Math.sin(a)*43);c.stroke()}c.restore();
    }
    const {lines,size:typeSize}=answerLayout(c);
    c.save();c.globalAlpha=1-answer;
    const state=t<2.15||t>=14?'A thought is coming.':t<5.65?'Let me think.':'Oh. I’ve got it.';
    text(c,state,936,1107,74,500,'center');c.restore();
    if(answer>.001){
      c.save();roundRect(c,100,978,1672,(lines.length>2?284:245)*answer,0);c.clip();c.globalAlpha=answer;
      lines.forEach((line,i)=>text(c,line,936,1048+i*(typeSize+14),typeSize,600,'center'));
      c.restore();
    }
    c.strokeStyle='#c2cbc2';c.lineWidth=2;c.beginPath();c.moveTo(108,1264);c.lineTo(1764,1264);c.stroke();
    // A three-dot footer acknowledges the chat's reply without extra UI.
    [0,1,2].forEach(i=>circle(c,1697+i*28,1315,5,i===Math.floor(t/5)%3?ink:'#a4afa5'));
    if(stepped){
      // Deliberately stylized low-frame-rate refresh, avoiding full-field flashing.
      const changed=Math.floor(t*5)%2;
      c.save();c.globalAlpha=changed?.016:.028;c.fillStyle=ink;c.fillRect(0,0,1872,1404);c.restore();
    }
    c.restore();
  }
  function drawReplyScreen(c,t,reply,opts){
    const dot=companions[opts.dot]||companions[selectedDot];
    if((opts.mode||mode)==='ink')t=Math.floor(t*5)/5;
    const motion=reduced&&!opts.export?0:1;
    const thinking=smooth((t-2.15)/.5)*(1-smooth((t-5.65)/.5));
    const answer=ease((t-6.75)/.65)*(opts.hold?1:1-smooth((t-14.0)/.8));
    const awake=smooth((t-.6)/1.0)*(1-smooth((t-14.3)/1.1));
    const bob=Math.sin(t*2.5)*3*awake*motion*dot.bob;
    const tilt=Math.sin(t*2.15)*.028*thinking*motion*dot.tilt;
    c.save();c.fillStyle=paper;c.fillRect(0,0,1872,1404);
    c.globalAlpha=.75;c.drawImage(fibers,0,0,1872,1404);c.globalAlpha=1;
    dotMark(c,111,111,1.18);text(c,'dots',173,126,44,700);
    // Sender and message share a normal reading column; the mascot is an avatar.
    c.save();c.translate(205,294+bob);c.rotate(tilt);drawCompanion(c,dot,218,t,awake,thinking,answer,motion);c.restore();
    const senderLines=wrapReply(c,String(reply.sender).slice(0,80),1320,46,650);
    text(c,senderLines[0]||'heidot',358,286,46,650);
    text(c,answer>.5?'Reply':thinking>.1?'Thinking…':'Getting ready',358,332,27,500,'left','#59665d');
    if(thinking>.01){
      c.save();c.globalAlpha=thinking;
      for(let i=0;i<3;i++){const pulse=(Math.sin(t*5.5-i*1.35)+1)/2;circle(c,364+i*37,467,7+3*pulse)}c.restore();
    }
    const layout=replyLayout(c,reply.text);
    c.save();c.globalAlpha=answer;
    roundRect(c,350,399,1350,Math.min(840,layout.height+65)*answer,0);c.clip();
    for(const row of layout.rows){
      const baseline=456+row.y;
      if(row.marker==='•')circle(c,370,baseline-layout.size*.30,5);
      else if(row.marker)text(c,row.marker,358,baseline,layout.size,500);
      text(c,row.text,358+row.x,baseline,layout.size,row.weight);
    }
    c.restore();
    const notice=opts.notice||(layout.truncated?'Reply continues in the conversation.':'');
    if(notice)text(c,notice,358,1318,24,500,'left','#59665d');
    c.restore();
  }
  function drawConversationScreen(c,t,conversation,opts){
    const dot=companions[opts.dot]||companions[selectedDot];
    if((opts.mode||mode)==='ink')t=Math.floor(t*5)/5;
    const motion=reduced&&!opts.export?0:1;
    const visible=conversation.messages.filter(message=>t>=message.at);
    const thinking=visible.length?0:1,answer=visible.length?1:0;
    c.save();c.fillStyle=paper;c.fillRect(0,0,1872,1404);
    c.globalAlpha=.75;c.drawImage(fibers,0,0,1872,1404);c.globalAlpha=1;
    dotMark(c,111,111,1.18);text(c,'dots',173,126,44,700);
    c.save();c.translate(205,294+Math.sin(t*2.5)*3*motion);drawCompanion(c,dot,218,t,1,thinking,answer,motion);c.restore();
    text(c,conversation.sender||'heidot',358,286,46,650);
    text(c,thinking?'Thinking…':'Conversation',358,332,27,500,'left','#59665d');
    if(thinking){for(let i=0;i<3;i++)circle(c,364+i*37,467,8+2*Math.sin(t*5-i))}
    let y=456;
    for(const message of visible){
      const appear=ease((t-message.at)/.22);
      c.save();c.globalAlpha=appear;
      if(message.role==='user'){
        const bubbleWidth=306,bubbleHeight=160,x=1372;
        roundRect(c,x,y-72,bubbleWidth,bubbleHeight,32);c.fillStyle=ink;c.fill();
        text(c,message.text,x+bubbleWidth/2,y+37,92,650,'center',paper);
        text(c,'You',x+bubbleWidth,y-93,27,500,'right','#59665d');
        y+=bubbleHeight+60;
      }else{
        const layout=replyLayout(c,message.text,1320,460);
        for(const row of layout.rows)text(c,row.text,358+row.x,y+row.y,layout.size,row.weight);
        y+=layout.height+14;
        if(message.status){text(c,message.status,358,y,27,500,'left','#59665d');y+=35}
        y+=60;
      }
      c.restore();
    }
    c.restore();
  }
  const screen=document.createElement('canvas');screen.width=1872;screen.height=1404;
  const sc=screen.getContext('2d',{alpha:false});
  function drawStudio(c,t,opts){
    c.fillStyle=ground;c.fillRect(0,0,1600,1200);
    text(c,'A little dot. A lot to say.',800,133,80,650,'center');
    text(c,'Your digital companion. A little more tangible.',800,184,25,400,'center','#4c6056');
    const x=258,y=245,w=1084,h=834;
    c.save();c.shadowColor='rgba(21,38,27,.23)';c.shadowBlur=44;c.shadowOffsetY=35;
    roundRect(c,x,y,w,h,39);c.fillStyle='#242a27';c.fill();c.restore();
    const rim=c.createLinearGradient(x,y,x+w,y+h);rim.addColorStop(0,'#4b514d');rim.addColorStop(.3,'#242a27');rim.addColorStop(.85,'#161c19');rim.addColorStop(1,'#343e37');
    roundRect(c,x,y,w,h,39);c.fillStyle=rim;c.fill();
    c.save();roundRect(c,x+6,y+5,w-12,h-10,34);c.strokeStyle='rgba(255,255,255,.12)';c.lineWidth=1.2;c.stroke();c.restore();
    drawScreen(sc,t,opts);
    const sx=x+35,sy=y+31,sw=1014,sh=760.5;
    c.save();roundRect(c,sx,sy,sw,sh,5);c.clip();c.drawImage(screen,sx,sy,sw,sh);
    c.strokeStyle='rgba(0,0,0,.17)';c.lineWidth=4;roundRect(c,sx,sy,sw,sh,5);c.stroke();c.restore();
    // Small tactile gesture bar in the lower bezel, without a fabricated front logo.
    roundRect(c,752,1051,96,4,2);c.fillStyle='#58635b';c.fill();
    text(c,'dots on paper',258,1154,24,600);
    text(c,opts.studioNotice||'TRMNL X',1342,1154,18,500,'right','#4c6056');
  }
  function renderAt(t,opts={}){
    if(!assetsReady)return;
    t=Math.min(Math.max(Number(t)||0,0),duration);
    // A reply is a retained result, not another trip around the thinking loop.
    if(!opts.screenImage)t=Math.min(t,activeConversation(opts)?12:9);
    const f=opts.format||format,w=f==='screen'?1872:1600,h=f==='screen'?1404:1200;
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}
    if(f==='screen')drawScreen(ctx,t,opts);else drawStudio(ctx,t,opts);
    return t;
  }
  const nativeImages=new Map();
  async function renderNativeAt(t,opts,uri){
    let image=nativeImages.get(uri);
    if(!image){image=new Image();image.src=uri;await image.decode();nativeImages.set(uri,image)}
    return renderAt(t,{...opts,screenImage:image});
  }
  function ui(t){
    q('scrub').value=t;q('time').textContent=`0:${String(Math.floor(t)).padStart(2,'0')} / 0:16`;
    const conversation=activeConversation();
    const visible=conversation?.messages.filter(message=>t>=message.at);
    const state=conversation?(visible.length===0?'Thinking':visible.length===1?'Draft ready':visible.length===2?'Interrupted':'Nothing sent'):stateAt(t);q('state-label').textContent=state;
    if(state!==lastState){const reply=activeReply();q('spoken-state').textContent=conversation?`${conversation.notice}. ${visible.at(-1)?.text||state}`:`${reply?.sender||companions[selectedDot].name}: `+(state==='Reply'?(reply?.text||'Good ideas deserve a little paper.'):state);lastState=state}
  }
  function updatePlay(){q('pause-icon').toggleAttribute('hidden',!playing);q('play-icon').toggleAttribute('hidden',playing);q('play').setAttribute('aria-label',playing?'Pause animation':'Play animation');q('play').title=playing?'Pause animation':'Play animation'}
  function pause(){playing=false;updatePlay()}
  function play(){if(seconds>=duration)seconds=0;playing=true;baseSeconds=seconds;baseTime=performance.now();updatePlay()}
  function restart(){seconds=reduced?(example==='wife-noo'?12:9):0;baseSeconds=seconds;baseTime=performance.now();if(!reduced)play();renderAt(seconds);ui(seconds)}
  function select(prefix,value){
    const names=prefix==='format'?['scene-view','screen-view']:['smooth-mode','ink-mode'];
    names.forEach((id,i)=>{const on=i===(value===('format'===prefix?'scene':'smooth')?0:1);q(id).classList.toggle('active',on);q(id).setAttribute('aria-pressed',on)});
  }
  q('play').onclick=()=>playing?pause():play();q('replay').onclick=restart;
  q('scrub').oninput=e=>{pause();seconds=Number(e.target.value);baseSeconds=seconds;renderAt(seconds);ui(seconds)};
  ['scene','screen'].forEach(f=>q(f+'-view').onclick=()=>{format=f;select('format',f);q('stage').classList.toggle('screen-mode',f==='screen');renderAt(seconds)});
  ['smooth','ink'].forEach(m=>q(m+'-mode').onclick=()=>{mode=m;select('mode',m);renderAt(seconds)});
  q('edit-toggle').onclick=()=>{const open=q('answer-editor').hidden;q('answer-editor').hidden=!open;q('edit-toggle').setAttribute('aria-expanded',open);if(open)q('answer').focus()};
  q('answer-editor').onsubmit=e=>{e.preventDefault();const v=q('answer').value.trim();if(!v){q('answer').setCustomValidity('Give your dot a reply to show.');q('answer').reportValidity();return}setAnswer(v);q('answer').setCustomValidity('');restart()};
  q('answer').oninput=()=>q('answer').setCustomValidity('');q('reload').onclick=()=>location.reload();
  function saveCurrent(event,format){
    if(!customAnswer)return;
    event.preventDefault();pause();renderAt(9,{format,export:true,hold:true});
    const character=selectedDot;
    canvas.toBlob(blob=>{if(!blob)return;const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`dot-reply-${character}-${format}.png`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)},'image/png');
    renderAt(seconds);
  }
  q('download-film').onclick=event=>saveCurrent(event,'scene');q('save-screen').onclick=event=>saveCurrent(event,'screen');
  let resumeOnVisible=false;
  document.addEventListener('visibilitychange',()=>{if(document.hidden){resumeOnVisible=playing;pause()}else if(resumeOnVisible){play();resumeOnVisible=false}});
  let inView=true;new IntersectionObserver(entries=>{inView=entries[0].isIntersecting},{threshold:.03}).observe(canvas);
  function loop(now){if(playing&&assetsReady&&inView){seconds=Math.min(baseSeconds+(now-baseTime)/1000,duration);renderAt(seconds);ui(seconds);if(seconds>=duration)pause()}requestAnimationFrame(loop)}
  function loadDot(id){return new Promise((resolve,reject)=>{
    const dot=companions[id];dot.image.onload=()=>{dot.loaded=true;document.querySelector(`[data-dot="${id}"]`).disabled=false;drawAvatar(id);resolve(id)};
    dot.image.onerror=()=>reject(new Error(`The ${dot.name} character asset could not load`));dot.image.src=`assets/${dot.src}`;
  })}
  const dotLoads=Object.keys(companions).map(id=>loadDot(id));
  const allDotsReady=Promise.all(dotLoads);
  const ready=Promise.all([document.fonts.load('650 80px Figtree'),dotLoads[example?3:0]]).then(()=>{assetsReady=true;q('loading').hidden=true;q('stage').setAttribute('aria-busy','false');baseTime=performance.now();setExample(example);renderAt(seconds);ui(seconds);updatePlay()}).catch(error=>{q('loading').hidden=true;q('load-error').hidden=false;q('stage').setAttribute('aria-busy','false');console.error(error);throw error});
  allDotsReady.catch(error=>{console.error(error);q('spoken-state').textContent='A dot could not load. Reload the demo to try again.'});
  window.dotDemo={ready,allDotsReady,canvas,duration,renderAt,renderNativeAt,pause,play,restart,setDot,setExample,dots:Object.keys(companions),setAnswer,replyBlocks,replyLayout:(value,width,height)=>replyLayout(ctx,value,width,height),get state(){return {playing,seconds,format,mode,customAnswer,reduced,dot:selectedDot,example,reply:activeReply(),conversation:activeConversation()}}};
  requestAnimationFrame(loop);
})();
