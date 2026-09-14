/* FCMO AI Newsletter — autonomous surface freshness v1
   Deterministic downstream enhancement. Reads only the sanitized public corpus. */
(()=>{
  'use strict';
  const dataNode=document.getElementById('fcmo-data');
  if(!dataNode)return;
  let D; try{D=JSON.parse(dataNode.textContent)}catch{return}
  const records=Array.isArray(D.records)?D.records:[];
  const publications=Array.isArray(D.publication_memory)?D.publication_memory:[];
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const timeValue=s=>{const n=Date.parse(s||'');return Number.isFinite(n)?n:0};
  const day=s=>String(s||'').slice(0,10);
  const latestPublished=[...publications].filter(x=>x&&x.published&&x.date).sort((a,b)=>String(b.date).localeCompare(String(a.date)))[0]||null;
  const anchorTime=latestPublished?Date.parse(latestPublished.date+'T23:59:59Z'):Math.max(0,...records.map(r=>Math.max(timeValue(r.last_verified_at),timeValue(r.event_at))));
  const activityTime=r=>Math.max(timeValue(r?.last_verified_at),timeValue(r?.event_at));
  const activityDay=r=>day(new Date(activityTime(r)||0).toISOString());
  const publicLeadId=()=>{const href=document.querySelector('.lead-body h2 a[href*="/news/en/FCMO-"]')?.getAttribute('href')||'';const m=href.match(/(FCMO-[A-Z0-9]+)/);return m?m[1]:null};
  const freshnessScore=r=>{const ageDays=Math.max(0,(anchorTime-activityTime(r))/86400000);return Number(r.importance||0)*3+Math.max(0,21-ageDays)*0.65};
  function currentSignals(){const leadId=publicLeadId();const sorted=[...records].sort((a,b)=>freshnessScore(b)-freshnessScore(a)||activityTime(b)-activityTime(a)||Number(b.importance||0)-Number(a.importance||0)||String(a.id).localeCompare(String(b.id)));return [...(leadId?sorted.filter(r=>r.id===leadId):[]),...sorted.filter(r=>r.id!==leadId)].slice(0,10)}
  function enhanceSignalField(){
    const plot=document.getElementById('plot');if(!plot)return;const figure=plot.closest('.signal-figure'),signals=currentSignals();if(!signals.length)return;
    plot.querySelectorAll('.signal-node').forEach(n=>n.remove());plot.dataset.fcmoFreshness='recent-public';plot.dataset.fcmoLatestPublication=latestPublished?.date||'';
    const title=figure?.querySelector('.signal-title strong');if(title)title.textContent='Signal Field / current public signals';
    const key=figure?.querySelector('.signal-title span');if(key)key.innerHTML='x = evidence · y = consequence<br>recency breaks historical lock-in · orange = lead';
    if(figure)figure.setAttribute('aria-label','Signal Field — current public signals ranked by consequence and recent verified activity');
    const xs={A:82,B:58,C:34,D:18},ys={10:8,9:12,8:18,7:34,6:50,5:65,4:74,3:78,2:80,1:82},groups=new Map(),positions=new Map();
    for(const s of signals){const k=`${s.evidence}|${s.importance}`;(groups.get(k)||groups.set(k,[]).get(k)).push(s)}
    for(const members of groups.values()){const n=members.length,spreadX=Math.min(20,6+(n-1)*3),spreadY=Math.min(20,4+(n-1)*3.2);members.forEach((s,j)=>{const frac=n===1?0:j/(n-1)-.5,baseX=xs[s.evidence]??30,baseY=ys[s.importance]??72;positions.set(s.id,{x:Math.max(8,Math.min(94,baseX+frac*spreadX)),y:Math.max(8,Math.min(78,baseY+frac*spreadY))})})}
    const leadId=publicLeadId();
    signals.forEach((s,i)=>{const p=positions.get(s.id)||{x:30,y:72},button=document.createElement('button'),isLead=s.id===leadId;button.className='signal-node'+(isLead?' lead':'');button.style.setProperty('--x',p.x.toFixed(2)+'%');button.style.setProperty('--y',p.y.toFixed(2)+'%');button.style.setProperty('--s',(isLead?32:Math.max(14,12+Number(s.importance||0)*1.25))+'px');button.dataset.n=String(i+1).padStart(2,'0');button.dataset.fcmoSignalId=s.id;button.dataset.fcmoActivity=activityDay(s);button.setAttribute('aria-label',`${s.title}. Evidence ${s.evidence}; consequence ${s.importance} of 10; public activity ${activityDay(s)}.`);const read=()=>{const idx=document.getElementById('read-index'),rt=document.getElementById('read-title'),rm=document.getElementById('read-meta');if(idx)idx.textContent=button.dataset.n;if(rt)rt.textContent=s.title;if(rm)rm.innerHTML=`Evidence ${esc(s.evidence)}<br>Impact ${Number(s.importance||0)} / 10<br>Activity ${esc(activityDay(s))}`};button.onmouseenter=read;button.onfocus=read;button.onclick=()=>{location.hash='#/brief/'+s.id};plot.appendChild(button)});
    const first=signals[0],node=plot.querySelector('.signal-node');if(first&&node){const idx=document.getElementById('read-index'),rt=document.getElementById('read-title'),rm=document.getElementById('read-meta');if(idx)idx.textContent=node.dataset.n;if(rt)rt.textContent=first.title;if(rm)rm.innerHTML=`Evidence ${esc(first.evidence)}<br>Impact ${Number(first.importance||0)} / 10<br>Activity ${esc(activityDay(first))}`}
  }
  function publicationActivityMarkup(){const latestEvent=records.reduce((m,r)=>String(r.event_at||'')>m?String(r.event_at||''):m,'').slice(0,10);const recent=[...publications].filter(x=>x&&x.date&&String(x.date)>latestEvent).sort((a,b)=>String(b.date).localeCompare(String(a.date))).slice(0,8);if(!recent.length)return '';return `<section class="fcmo-activity-clock" data-fcmo-publication-activity="${esc(recent[0].date)}"><div class="fcmo-clock-head"><span class="eyebrow">Latest public activity</span><h2>Publication clock</h2><p>New verification and editorial activity is shown here without rewriting the original date of a development.</p></div>${recent.map(e=>`<a class="fcmo-clock-row" href="#/edition/${encodeURIComponent(e.date)}"><time>${esc(e.date)}</time><span><strong>${e.published?'Published edition':'Research snapshot'}</strong><small>${esc((e.preamble||[]).map(x=>x.text||'').join(' ').slice(0,180))}</small></span><b>${e.published?'ISSUED':'SNAPSHOT'} →</b></a>`).join('')}</section>`}
  function enhanceChronology(){const grid=document.querySelector('.chronology-grid');if(!grid||document.querySelector('.fcmo-activity-clock'))return;const hero=document.querySelector('.hero-mini p');if(hero)hero.textContent='Two clocks: current publication and verification activity first; original development dates remain intact below.';const markup=publicationActivityMarkup();if(markup)grid.insertAdjacentHTML('beforebegin',markup);grid.dataset.fcmoOriginChronology='true'}
  function reorderLibrary(){
    const list=document.getElementById('rlist'),sort=document.getElementById('rsort'),count=document.getElementById('rcount');if(!list||!sort)return;
    const newest=sort.querySelector('option[value="newest"]');if(newest)newest.textContent='Latest verified';if(!sort.dataset.fcmoInitialized){sort.value='newest';sort.dataset.fcmoInitialized='1'}if(sort.value!=='newest')return;
    const byId=new Map(records.map(r=>[r.id,r])),cards=[...list.querySelectorAll('a[href*="#/brief/"],a[href*="/brief/"]')];
    const ranked=cards.map((el,i)=>{const m=(el.getAttribute('href')||'').match(/FCMO-[A-Z0-9]+/),r=m&&byId.get(m[0]);return {el,r,i}}).sort((a,b)=>(activityTime(b.r)-activityTime(a.r))||Number(b.r?.importance||0)-Number(a.r?.importance||0)||a.i-b.i);
    if(ranked.some((x,i)=>x.el!==cards[i]))ranked.forEach(x=>list.appendChild(x.el));list.dataset.fcmoLibrarySort='latest-verified';
    const maxRecord=records.reduce((best,r)=>activityTime(r)>activityTime(best)?r:best,null);if(count&&maxRecord)count.innerHTML=`<b>${cards.length} visible</b><span>${records.length} total public briefs · latest dossier verification ${esc(activityDay(maxRecord))}</span>`;
    const shell=list.closest('.research-shell')||list.parentElement;if(shell&&!shell.querySelector('.fcmo-library-clock')&&latestPublished)shell.insertAdjacentHTML('afterbegin',`<div class="fcmo-library-clock" data-fcmo-library-edition="${esc(latestPublished.date)}"><b>Current edition: ${esc(latestPublished.date)}</b><span>The Library contains promoted public dossiers; edition-only investigations remain in Publication Memory until they become canonical public records.</span></div>`)
  }
  function routeName(){return location.hash.replace(/^#\/?/,'').split(/[/?]/)[0]||'home'}
  function enhance(){const route=routeName();if(route==='home')enhanceSignalField();else if(route==='chronology')enhanceChronology();else if(route==='research')setTimeout(reorderLibrary,0)}
  window.addEventListener('hashchange',()=>setTimeout(enhance,0));
  document.addEventListener('input',e=>{if(routeName()==='research'&&e.target?.closest?.('.library-tools'))setTimeout(reorderLibrary,0)});
  document.addEventListener('change',e=>{if(routeName()==='research'&&e.target?.closest?.('.library-tools'))setTimeout(reorderLibrary,0)});
  enhance();
})();
