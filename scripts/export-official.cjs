const fs=require('fs'),path=require('path'),http=require('http');
const {chromium}=require('playwright');
const args=process.argv.slice(2),arg=(key,fallback)=>{const i=args.indexOf(key);return i<0?fallback:args[i+1]};
const root=path.resolve(__dirname,'..');
const raw=path.resolve(arg('--raw',path.join(root,'assets/official/source')));
const out=path.resolve(arg('--out',path.join(root,'.build/official')));
const vendor=arg('--vendor',null);
const vendorPaths=vendor?{'pixi.min.js':path.join(vendor,'pixi.min.js'),'pixi-spine.umd.js':path.join(vendor,'pixi-spine.umd.js')}:{'pixi.min.js':path.resolve(path.dirname(require.resolve('pixi.js')),'../browser/pixi.min.js'),'pixi-spine.umd.js':path.resolve(path.dirname(require.resolve('pixi-spine')),'../dist/pixi-spine.umd.js')};
const models=[['default','default'],['synesthesia','synesthesia'],['game','game']];
const server=http.createServer((req,res)=>{try{const url=decodeURIComponent(req.url.split('?')[0]);let file=url==='/'?path.join(__dirname,'spine-renderer.html'):url.startsWith('/vendor/')?vendorPaths[path.basename(url)]:path.join(raw,url.replace('/raw/',''));if(!file||!fs.statSync(file).isFile())throw Error();res.setHeader('Content-Type',file.endsWith('.html')?'text/html':file.endsWith('.js')?'application/javascript':file.endsWith('.png')?'image/png':'application/octet-stream');res.end(fs.readFileSync(file))}catch{res.statusCode=404;res.end('Not found')}});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({headless:true,executablePath:arg('--browser',undefined),args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  try{
    const page=await browser.newPage();page.on('pageerror',e=>console.error(e.message));page.on('console',m=>{if(m.type()==='error')console.error(m.text())});
    await page.goto(`http://127.0.0.1:${server.address().port}`);
    for(const [id,folder] of models){
      const skel=fs.readdirSync(path.join(raw,folder)).find(n=>n.endsWith('.skel'));
      const info=await page.evaluate(url=>window.loadPet(url),`/raw/${encodeURIComponent(folder)}/${encodeURIComponent(skel)}`);
      console.log(JSON.stringify({id,version:info.version,animations:info.animations}));fs.mkdirSync(path.join(out,id),{recursive:true});
      fs.writeFileSync(path.join(out,id,'model.json'),JSON.stringify(info,null,2));
      if(args.includes('--inspect'))continue;
      if(args.includes('--looks-only')){
        const {fit}=JSON.parse(fs.readFileSync(path.join(out,id,'manifest.json')));
        const dir=path.join(out,id,'Look');fs.mkdirSync(dir,{recursive:true});
        for(let i=0;i<16;i++){const data=await page.evaluate(v=>window.captureLook(v.direction,v.fit),{direction:i,fit});fs.writeFileSync(path.join(dir,`${String(i).padStart(4,'0')}.png`),Buffer.from(data.split(',')[1],'base64'))}
        continue;
      }
      const clips=info.animations.filter(a=>['Default','Relax','Move','Interact','Sit','Sleep'].includes(a.name));
      const bounds={minX:Infinity,minY:Infinity,maxX:-Infinity,maxY:-Infinity};
      for(const clip of clips)for(let i=0;i<=24;i++){
        const b=await page.evaluate(v=>window.measure(v.name,v.time),{name:clip.name,time:clip.duration*i/24});
        bounds.minX=Math.min(bounds.minX,b.x);bounds.minY=Math.min(bounds.minY,b.y);bounds.maxX=Math.max(bounds.maxX,b.x+b.width);bounds.maxY=Math.max(bounds.maxY,b.y+b.height);
      }
      const scale=Math.min(704/(bounds.maxX-bounds.minX),768/(bounds.maxY-bounds.minY));
      const fit={scale,x:384-(bounds.minX+bounds.maxX)/2*scale,y:800-bounds.maxY*scale};
      const manifest={id,fps:20,canvas:[768,832],bounds,fit,clips:{}};
      for(const clip of clips){
        const count=Math.max(1,Math.ceil(clip.duration*20)),dir=path.join(out,id,clip.name);fs.mkdirSync(dir,{recursive:true});
        for(let i=0;i<count;i++){
          const data=await page.evaluate(v=>window.capture(v.name,v.time,v.fit),{name:clip.name,time:i/20,fit});
          fs.writeFileSync(path.join(dir,`${String(i).padStart(4,'0')}.png`),Buffer.from(data.split(',')[1],'base64'));
        }
        manifest.clips[clip.name]={duration:clip.duration,frames:count};console.log(`${id}: ${clip.name} ${count} frames`);
      }
      fs.writeFileSync(path.join(out,id,'manifest.json'),JSON.stringify(manifest,null,2));
      const dir=path.join(out,id,'Look');fs.mkdirSync(dir,{recursive:true});
      for(let i=0;i<16;i++){const data=await page.evaluate(v=>window.captureLook(v.direction,v.fit),{direction:i,fit});fs.writeFileSync(path.join(dir,`${String(i).padStart(4,'0')}.png`),Buffer.from(data.split(',')[1],'base64'))}
    }
  }finally{await browser.close();server.close()}
})().catch(error=>{console.error(error);server.close();process.exitCode=1});
