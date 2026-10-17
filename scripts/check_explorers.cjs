const {chromium}=require('playwright');
const path=require('path'),fs=require('fs');
(async()=>{
 const root=path.resolve(__dirname,'..'),out=path.join(root,'outputs','validation');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:process.env.RESEARCH_CHROMIUM_PATH||undefined,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader','--no-zygote','--single-process']});
 const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});const errors=[];const network=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
 await page.goto('file://'+path.join(root,'interactive-explorers.html'));await page.waitForFunction(()=>window.researchReady===true);
 await page.waitForTimeout(1800);await page.screenshot({path:path.join(out,'explorer-response.png'),fullPage:true});
 const checks=[];
 async function capture(name,type){checks.push({name,pass:await page.evaluate(type=>document.getElementById('plot3d').data?.[0]?.type===type,type)});}
 await capture('Response surface renders','surface');checks.push({name:'Axes retain scientific labels and units',pass:await page.evaluate(()=>document.getElementById('plot3d')._fullLayout.scene.xaxis.title.text==='Event time (min)'&&document.getElementById('plot2d')._fullLayout.yaxis.title.text==='Response (bp)')});await page.selectOption('#asset','EURUSD');await page.selectOption('#eventType','Minutes');await capture('Asset and event-type selection updates','surface');
 await page.selectOption('#phase','validation');checks.push({name:'Insufficient-sample state explicit',pass:await page.locator('#plot3d').innerText().then(t=>t.includes('Insufficient'))});
 await page.selectOption('#phase','holdout');await page.click('[data-mode="paths"]');await capture('Observed event paths render','scatter3d');await page.selectOption('#window','extended');const n=await page.locator('#event option').count();if(n>1)await page.selectOption('#event',{index:1});await page.screenshot({path:path.join(out,'explorer-paths.png'),fullPage:true});
 checks.push({name:'Selected event appears in caption',pass:await page.evaluate(()=>document.getElementById('caption2d').textContent.includes(document.getElementById('event').value.slice(-10)))});
 await page.click('[data-mode="lab"]');await capture('Synthetic laboratory renders','surface');await page.locator('#delay').fill('3');await page.locator('#delay').dispatchEvent('input');checks.push({name:'Quote-delay control updates',pass:await page.locator('#delay-value').innerText().then(t=>t==='3 min')});await page.screenshot({path:path.join(out,'explorer-laboratory.png'),fullPage:true});
 await page.click('#reset');await page.setViewportSize({width:390,height:844});await page.waitForTimeout(1000);await page.screenshot({path:path.join(out,'explorer-mobile.png'),fullPage:true});checks.push({name:'Mobile page has no horizontal overflow',pass:await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)});
 const result={checks,errors,external_network_requests:network,passed:checks.every(c=>c.pass)&&!errors.length&&!network.length};fs.writeFileSync(path.join(out,'explorer-checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));await browser.close();if(!result.passed)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
