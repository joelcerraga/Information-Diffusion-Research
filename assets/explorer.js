"use strict";
(() => {
const $=id=>document.getElementById(id),D=window.RESEARCH_DATA,mode=document.body.dataset.explorer;
let csvRows=[],csvName='research.csv',busy=false;
const palette=['#14756e','#102b3e','#b68432','#5998a2'];
const config={responsive:true,displaylogo:false,toImageButtonOptions:{format:'png',scale:2},modeBarButtonsToRemove:['sendDataToCloud']};
const base={paper_bgcolor:'#fff',plot_bgcolor:'#fff',font:{family:'Arial, sans-serif',size:12,color:'#294550'},margin:{l:65,r:20,t:35,b:60},showlegend:false};
const camera=()=>({eye:window.innerWidth<600?{x:2.2,y:2.1,z:1.5}:{x:1.65,y:1.6,z:1.05}});
const axis=text=>({title:{text,font:{size:11}},gridcolor:'#e5eded',zerolinecolor:'#9bb2b7'});
const scene=(x,y,z)=>({xaxis:axis(x),yaxis:axis(y),zaxis:axis(z),camera:camera(),aspectmode:'manual',aspectratio:{x:1.3,y:1,z:.8}});
const text=(id,value)=>{$(id).textContent=value;};
const metric=(value,detail)=>{$('metric').replaceChildren(Object.assign(document.createElement('strong'),{textContent:value}),document.createTextNode(detail));};
const line=(x,y,name,color)=>({type:'scatter',mode:'lines',x,y,name,line:{color,width:2.5}});
const plot=(id,traces,layout)=>Plotly.react(id,traces,{...base,...layout},config);
const phase=()=> $('sample').value;
const eventType=()=> $('communication').value;
const sampleNote=()=>phase()==='holdout'?' Later-period estimates are post-audit chronological transfer.':'';

function response(rebuild){
 const rows=D.curves.filter(r=>r.asset===$('asset').value&&r.event_type===eventType()&&r.phase===phase()).sort((a,b)=>a.horizon-b.horizon);
 const cov=D.coverage.filter(r=>r.asset===$('asset').value&&r.event_type===eventType()&&(phase()==='pooled'||r.phase===phase()));
 const n=cov.reduce((v,r)=>v+r.accepted,0),planned=cov.reduce((v,r)=>v+r.planned,0);
 text('status',`${$('asset').value} · ${eventType()} · ${n}/${planned} planned events accepted (${(100*n/planned).toFixed(1)}%).${sampleNote()}`);
 text('context-text','These surfaces describe associations with an ex-post rate surprise. The factor uses information through +20 minutes. No single empirical adjustment speed passed every reporting criterion.');
 text('reading','The horizontal axes are completed minutes after release and rate surprise in development standard deviations (SD). Height is β(h) × surprise, in basis points (bp), relative to a zero-surprise prediction. The intercept is excluded. The gold line selects one surprise slice.');
 text('limits','The shaded companion band is simultaneous across the 20 horizons within the selected sample, asset and communication type. It does not adjust across all views or include first-stage factor uncertainty. Missing-window exclusions and the post-audit evaluation chronology limit interpretation.');
 text('caption3d','Interactive figure 1. Fitted response by horizon and rate surprise. This is a model surface over a selected surprise range.');
 text('caption2d','Selected surprise slice and 95% wild-bootstrap simultaneous band across the 20 horizons.');
 text('control-note','The surprise range follows the accepted observations. Coefficients are associations; the graph does not measure a fraction of information absorbed.');
 $('download').disabled=!rows.length;$('reset').disabled=!rows.length;csvName=`response-${$('asset').value}-${eventType()}-${phase()}.csv`;csvRows=rows;
 if(!rows.length){
  Plotly.purge('plot3d');Plotly.purge('plot2d');$('plot3d').innerHTML='<p class="empty">Too few accepted events for the planned response-curve inference.</p>';$('plot2d').innerHTML='';metric('Not estimated','The minimum sample-size rule remains in force.');$('surprise').disabled=true;return;
 }
 $('surprise').disabled=false;
 if(!$('plot3d').classList.contains('js-plotly-plot')){$('plot3d').innerHTML='';$('plot2d').innerHTML='';}
 const range=D.ranges.find(r=>r.asset===$('asset').value&&r.event_type===eventType()&&r.phase===phase());
 const lo=range.min,hi=range.max;
 if(rebuild){$('surprise').min=String(lo);$('surprise').max=String(hi);$('surprise').value=String(Math.max(lo,Math.min(hi,1)));}
 const s=Number($('surprise').value),h=rows.map(r=>r.horizon),grid=Array.from({length:31},(_,i)=>lo+(hi-lo)*i/30);
 text('surprise-output',s.toFixed(2)+' SD');
 const z=grid.map(v=>rows.map(r=>v*r.beta)),slice=rows.map(r=>s*r.beta);
 plot('plot3d',[{type:'surface',x:h,y:grid,z,colorscale:[[0,'#ab633e'],[.5,'#f5f8f7'],[1,'#177d77']],cmid:0,colorbar:{title:{text:'bp'},thickness:10,len:.6},hovertemplate:'Minute %{x}<br>Surprise %{y:.2f} SD<br>Response %{z:.2f} bp<extra></extra>'},{type:'scatter3d',mode:'lines',x:h,y:h.map(()=>s),z:slice,line:{color:'#cf9b3e',width:6},hovertemplate:'Response %{z:.2f} bp<extra></extra>'}],{margin:{l:0,r:15,t:10,b:0},scene:scene('Event time (min)','Surprise (SD)','Response (bp)'),uirevision:`response-${phase()}-${eventType()}-${$('asset').value}`});
 const lower=rows.map(r=>Math.min(s*r.sim_low,s*r.sim_high)),upper=rows.map(r=>Math.max(s*r.sim_low,s*r.sim_high));
 plot('plot2d',[{...line(h,lower,'Lower band','#fff'),line:{width:0},hoverinfo:'skip'},{...line(h,upper,'95% simultaneous band','#fff'),line:{width:0},fill:'tonexty',fillcolor:'rgba(20,117,110,.16)',showlegend:true},{...line(h,slice,'Estimated slice','#14756e'),showlegend:true}],{xaxis:axis('Minutes after release'),yaxis:axis('Response (bp)'),showlegend:true,legend:{orientation:'h',y:1.2,font:{size:10}}});
 metric(slice.at(-1).toFixed(2)+' bp',`Estimated 20-minute response at ${s.toFixed(2)} SD. Accepted surprise range: ${lo.toFixed(2)} to ${hi.toFixed(2)} SD.`);
}

function lag(){
 const rows=D.lags.filter(r=>r.phase===phase()&&r.event_type===eventType());
 const pairs=[['SPX','NSX'],['NSX','SPX'],['SPX','EURUSD'],['EURUSD','SPX']];
 const selected=$('pair').value,parts=selected.split('|');
 const selectedRows=rows.filter(r=>r.source===parts[0]&&r.target===parts[1]).sort((a,b)=>a.lag_minutes-b.lag_minutes);
 text('context-text','Lagged correlations are exploratory descriptions. Shared news, quote timing and common contemporaneous movement can produce these patterns. They do not establish causation or an executable lead.');
 text('reading','Each separate 3D line is one directed asset pair. Positive lag means the source series precedes the target series. The pair axis is categorical: the plot does not interpolate a surface between pairs. Select a pair to inspect its two-dimensional correlation curve.');
 text('limits','These are within-event minute-return correlations from accepted paired windows. The largest correlation is often at zero lag. No confidence band or multiple-comparison adjustment is implied, and predictive usefulness would require separate validation with information available in real time.');
 text('status',`${eventType()} · ${phase()==='pooled'?'Pooled 2018–2025':'Development 2018–2022'} · ${selectedRows[0].events} paired events for ${parts.join(' → ')}.`);
 text('control-note','Positive lag: source precedes target. A peak at zero describes contemporaneous co-movement.');
 const traces=pairs.map(([a,b],i)=>{const r=rows.filter(x=>x.source===a&&x.target===b).sort((a,b)=>a.lag_minutes-b.lag_minutes);return {type:'scatter3d',mode:'lines+markers',x:r.map(x=>x.lag_minutes),y:r.map(()=>i),z:r.map(x=>x.correlation),name:a+' → '+b,line:{color:palette[i],width:selected===a+'|'+b?7:3},marker:{color:palette[i],size:3},hovertemplate:`${a} → ${b}<br>Lag %{x} min<br>Correlation %{z:.3f}<extra></extra>`};});
 const sc=scene('Lag (min)','Asset pair','Correlation');sc.yaxis={...axis('Asset pair'),tickvals:[0,1,2,3],ticktext:pairs.map(p=>p.join(' → ')),tickfont:{size:9}};sc.zaxis.range=[-1,1];
 plot('plot3d',traces,{margin:{l:0,r:10,t:10,b:0},scene:sc,uirevision:'lag-'+phase()+eventType()});
 plot('plot2d',[{...line(selectedRows.map(r=>r.lag_minutes),selectedRows.map(r=>r.correlation),parts.join(' → '),'#14756e'),mode:'lines+markers'}],{xaxis:{...axis('Lag (minutes; positive = source leads)'),dtick:1},yaxis:{...axis('Correlation'),range:[-1,1]},shapes:[{type:'line',x0:0,x1:0,y0:-1,y1:1,line:{color:'#b68432',dash:'dot',width:1}}]});
 const zero=selectedRows.find(r=>r.lag_minutes===0);metric(zero.correlation.toFixed(3),'Zero-lag correlation for '+parts.join(' → ')+'.');
 text('caption3d','Interactive figure 2. Discrete lead–lag correlation curves across directed asset pairs.');text('caption2d','Selected pair across −5 to +5 minutes. The vertical line marks contemporaneous movement.');
 csvRows=selectedRows;csvName=`lead-lag-${parts.join('-')}-${eventType()}-${phase()}.csv`;
}

function lab(){
 const f=+$('fraction').value,k=+$('rate').value,A=+$('amplitude').value,d=+$('delay').value;
 const h=Array.from({length:20},(_,i)=>i+1),rates=Array.from({length:40},(_,i)=>.01+.99*i/39);
 const g=(t,r)=>t<1?0:1-(1-f)*Math.exp(-r*(t-1));
 text('context-text','Synthetic teaching model. All parameters are controlled assumptions, not estimates from the Federal Reserve sample.');
 text('fraction-output',f.toFixed(2));text('rate-output',k.toFixed(2)+' / min');text('amplitude-output',A+' bp');text('delay-output',d+' min');
 text('status','G(h) = 1 − (1 − f) exp[−k(h − 1)] for h ≥ 1. The response is A × G(h).');
 text('reading','The surface shows the fraction of a chosen total response reached at each time and adjustment rate. The gold line marks the selected rate. The companion chart compares the latent response with a quote delayed by the chosen number of minutes.');
 text('limits','The first-minute fraction describes the first observed minute rather than an instantaneous jump. A delayed quote can resemble slow adjustment even if the underlying response is fast. Synthetic recovery does not establish that empirical prices follow this model family.');
 text('control-note','The displayed t90 belongs only to this synthetic mechanism. At zero total response, a time to absorb a price change has no economic interpretation.');
 const sc=scene('Event time (min)','Rate (per min)','Adjustment (%)');sc.zaxis.range=[0,100];
 plot('plot3d',[{type:'surface',x:h,y:rates,z:rates.map(r=>h.map(t=>100*g(t,r))),colorscale:[[0,'#eff8f5'],[.5,'#6ebbb0'],[1,'#15516a']],cmin:0,cmax:100,colorbar:{title:{text:'%'},thickness:10,len:.6},hovertemplate:'Minute %{x}<br>Rate %{y:.2f}/min<br>Adjustment %{z:.1f}%<extra></extra>'},{type:'scatter3d',mode:'lines',x:h,y:h.map(()=>k),z:h.map(t=>100*g(t,k)),line:{color:'#cf9b3e',width:6},hoverinfo:'skip'}],{margin:{l:0,r:15,t:10,b:0},scene:sc,uirevision:'lab'});
 plot('plot2d',[{...line(h,h.map(t=>A*g(t,k)),'Latent response','#14756e'),showlegend:true},{...line(h,h.map(t=>A*g(t-d,k)),'Delayed quote','#b68432'),line:{color:'#b68432',width:2,dash:'dash'},showlegend:true}],{showlegend:true,legend:{orientation:'h',y:1.2,font:{size:10}},xaxis:axis('Minutes after release'),yaxis:axis('Synthetic response (bp)')});
 const t90=f>=.9?1:1+Math.log((1-f)/.1)/k;
 metric(A===0?'Undefined':t90.toFixed(2)+' min',A===0?'No total price response is specified.':`Synthetic latent time to 90% of the total response.${t90>20?' Beyond the displayed window.':''}`);
 text('caption3d','Interactive figure 3. Synthetic adjustment fractions across horizons and rates.');text('caption2d','Synthetic latent and delayed quote responses at the chosen parameters.');
 csvRows=h.map(t=>({minute:t,first_minute_fraction:f,rate_per_minute:k,total_response_bp:A,delay_minutes:d,latent_response_bp:A*g(t,k),delayed_quote_bp:A*g(t-d,k)}));csvName='synthetic-diffusion-scenario.csv';
}

function update(rebuild=false){
 try{if(mode==='response-surface')response(rebuild);else if(mode==='lead-lag')lag();else lab();}
 catch(error){text('status','This graph could not load. The static previews and paper remain available from the graph gallery.');console.error(error);}
}
function download(){if(!csvRows.length)return;const keys=Object.keys(csvRows[0]);const esc=v=>'"'+String(v??'').replaceAll('"','""')+'"';const csv=[keys.map(esc).join(','),...csvRows.map(r=>keys.map(k=>esc(r[k])).join(','))].join('\r\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));a.download=csvName;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
$('empirical-controls').hidden=mode==='diffusion-laboratory';$('response-controls').hidden=mode!=='response-surface';$('lag-controls').hidden=mode!=='lead-lag';$('lab-controls').hidden=mode!=='diffusion-laboratory';
if(mode==='lead-lag'){$('asset').hidden=true;document.querySelector('label[for=asset]').hidden=true;for(const option of [...$('sample').options])if(!['pooled','development'].includes(option.value))option.remove();}
['asset','communication','sample','pair'].forEach(id=>$(id).addEventListener('change',()=>update(true)));
['surprise','fraction','rate','amplitude','delay'].forEach(id=>$(id).addEventListener('input',()=>{if(!busy){busy=true;requestAnimationFrame(()=>{update();busy=false;});}}));
$('download').addEventListener('click',download);$('reset').addEventListener('click',()=>Plotly.relayout('plot3d',{'scene.camera':camera()}));
update(true);window.researchReady=true;
})();
