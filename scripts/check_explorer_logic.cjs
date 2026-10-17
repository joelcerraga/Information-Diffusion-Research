// Exercise the actual explorer script with a small DOM/Plotly harness.
// This verifies chart data and control transitions, not browser/WebGL rendering.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..'),code=fs.readFileSync(path.join(root,'assets/explorer.js'),'utf8');
const research=JSON.parse(fs.readFileSync(path.join(root,'assets/research-data.js'),'utf8').split('window.RESEARCH_DATA=')[1].replace(/;\s*$/,''));
let checks=0;
function harness(mode){
 const els={},plots={},errors=[],downloads=[];
 function el(id){if(els[id])return els[id];return els[id]={value:'',textContent:'',innerHTML:'',hidden:false,disabled:false,handlers:{},options:[],classes:new Set(),classList:{contains(c){return els[id].classes.has(c);}},addEventListener(t,f){this.handlers[t]=f;},replaceChildren(...c){this.children=c;},click(){downloads.push(this.download);}};}
 for(const id of ['asset','communication','sample','surprise','fraction','rate','amplitude','delay','pair','plot3d','plot2d'])el(id);
 Object.assign(el('asset'),{value:'SPX'});el('communication').value='Statements';el('sample').value='pooled';el('surprise').value='1';el('fraction').value='.25';el('rate').value='.22';el('amplitude').value='-25';el('delay').value='0';el('pair').value='SPX|NSX';
 el('sample').options=['pooled','development','validation','holdout'].map(value=>({value,remove(){}}));
 const context={window:{RESEARCH_DATA:research,innerWidth:1440},document:{body:{dataset:{explorer:mode}},getElementById:el,querySelector:s=>el(s),createElement:tag=>el('created-'+tag),createTextNode:text=>({textContent:text})},Plotly:{react(id,traces,layout){plots[id]={traces,layout};el(id).classes.add('js-plotly-plot');},purge(id){delete plots[id];el(id).classes.clear();},relayout(){}},requestAnimationFrame:f=>f(),setTimeout:f=>f(),Blob:class{},URL:{createObjectURL:()=>'',revokeObjectURL(){}},console:{error:e=>errors.push(String(e))}};
 vm.runInNewContext(code,context);
 return {els,plots,errors,downloads,change(id,value,event='change'){el(id).value=String(value);el(id).handlers[event]();},download(){el('download').handlers.click();},check(){assert.deepEqual(errors,[]);assert.equal(context.window.researchReady,true);checks++;}};
}
const response=harness('response-surface');response.check();
assert(Math.abs(response.plots.plot2d.traces.at(-1).y.at(-1)+29.46)<.005);checks++;
response.change('surprise',-1,'input');
assert(response.plots.plot2d.traces[0].y.every((v,i)=>v<=response.plots.plot2d.traces[1].y[i]));checks++;
response.change('sample','validation');assert(!response.plots.plot3d);assert.equal(response.els.download.disabled,true);checks++;
response.change('sample','pooled');assert(response.plots.plot3d);assert.equal(response.els.download.disabled,false);checks++;
for(const asset of ['SPX','NSX','EURUSD'])for(const type of ['Statements','Minutes'])for(const sample of ['pooled','development','holdout']){response.change('asset',asset);response.change('communication',type);response.change('sample',sample);response.check();assert.equal(response.plots.plot2d.traces.at(-1).y.length,20);}
response.download();assert(response.downloads.at(-1).endsWith('.csv'));checks++;
const lag=harness('lead-lag');lag.check();assert.equal(lag.plots.plot3d.traces.length,4);assert(Math.abs(lag.plots.plot2d.traces[0].y[5]-.97501159242)<1e-9);checks++;
for(const pair of ['SPX|NSX','NSX|SPX','SPX|EURUSD','EURUSD|SPX'])for(const type of ['Statements','Minutes'])for(const sample of ['pooled','development']){lag.change('pair',pair);lag.change('communication',type);lag.change('sample',sample);lag.check();assert.equal(lag.plots.plot2d.traces[0].x.length,11);assert(lag.plots.plot2d.traces[0].x.every(Number.isFinite));}
const lab=harness('diffusion-laboratory');lab.check();
lab.change('delay',3,'input');assert.deepEqual(Array.from(lab.plots.plot2d.traces[1].y.slice(0,3)),[0,0,0]);checks++;
lab.change('amplitude',0,'input');assert.equal(lab.els.metric.children[0].textContent,'Undefined');checks++;
lab.change('amplitude',25,'input');lab.change('fraction',1,'input');assert(lab.plots.plot2d.traces[0].y.every(x=>x===25));assert.equal(lab.els.metric.children[0].textContent,'1.00 min');checks++;
lab.download();assert.equal(lab.downloads.at(-1),'synthetic-diffusion-scenario.csv');checks++;
console.log(`PASS: ${checks} explorer logic checks; response values/bands, missing-sample recovery, all asset/event/sample combinations, lag series, zero-response semantics, quote delay and CSV controls.`);
