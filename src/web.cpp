#include "web.h"
#include "config.h"
#include "settings.h"
#include "machine.h"
#include "console.h"
#include "radar.h"
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <ArduinoOTA.h>
#include <Update.h>

// Everything here is built into the ESP32 Arduino core: WebServer for the page,
// ArduinoOTA for PlatformIO's network upload, Update for the page's upload card.
// No outside libraries.

static WebServer server(80);
static String whereAmI = "network not started";
static bool apMode = false;
static bool uploadRefused = false;

// ---------------------------------------------------------------------------
// The page. One file, no internet needed. It asks the machine for its state
// and any new console lines about once a second, and every button is just a
// console command, so the page and the USB console can never disagree.
// ---------------------------------------------------------------------------

static const char PAGE[] PROGMEM = R"HTML(<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DropSpider</title>
<style>
 :root{--bg:#121016;--card:#1d1a23;--line:#332e3d;--ink:#ece9f2;--dim:#9a93a8;--go:#4ac47a;--warn:#e8b44a;--bad:#e2604f;--act:#7a5cff}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:16px;max-width:760px;margin:auto}
 h1{font-size:20px;margin:0 0 2px}
 .sub{color:var(--dim);font-size:13px;margin-bottom:14px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:14px}
 h2{font-size:13px;margin:0 0 10px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}
 .state{font-size:24px;font-weight:600;margin:0 0 6px}
 .chip{display:inline-block;padding:3px 10px;border-radius:999px;font-size:13px;font-weight:600;margin:2px 4px 2px 0}
 .ok{background:rgba(74,196,122,.16);color:var(--go)} .wa{background:rgba(232,180,74,.16);color:var(--warn)} .no{background:rgba(226,96,79,.16);color:var(--bad)}
 .row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--line);font-size:14px}
 .row:last-child{border-bottom:0} .row span:first-child{color:var(--dim)}
 button{font:inherit;font-weight:600;border:0;border-radius:10px;padding:12px 8px;color:#fff;background:#3a3548;cursor:pointer}
 button.p{background:var(--act)} button.d{background:var(--bad)}
 .g{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));margin-bottom:8px}
 label{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:6px 0;font-size:14px;border-bottom:1px solid var(--line)}
 label small{display:block;color:var(--dim);font-size:12px}
 input{background:#100e15;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:8px;font:inherit}
 input[type=number]{width:110px;text-align:right}
 #log{background:#0b0a0e;border:1px solid var(--line);border-radius:8px;height:260px;overflow:auto;font:12px/1.4 ui-monospace,Consolas,monospace;padding:8px;white-space:pre-wrap;margin:0 0 8px}
 .cl{display:flex;gap:8px} .cl input{flex:1;font-family:ui-monospace,Consolas,monospace}
 .big{font-size:22px;font-weight:700;text-align:center;margin:6px 0}
 a{color:#a995ff}
 canvas{display:block;width:100%;background:#0b0a0e;border:1px solid var(--line);border-radius:8px}
 .key{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
</style></head><body>
<h1>DropSpider</h1>
<div class="sub" id="where">&nbsp;</div>

<div class="card">
 <div class="state" id="state">...</div>
 <div id="chips"></div>
 <div class="row"><span>Drops so far</span><b id="drops">-</b></div>
 <div class="row"><span>Last fired by</span><b id="trig">-</b></div>
 <div class="row"><span>Last rewind</span><b id="rw">-</b></div>
 <div class="row"><span>Last drop, measured by the rewind</span><b id="meas">-</b></div>
 <div class="row"><span>Limit switch</span><b id="lsw">-</b></div>
 <div class="row"><span>Running for</span><b id="up">-</b></div>
</div>

<div class="card">
 <h2>Radar</h2>
 <div id="rchips"></div>
 <canvas id="scope"></canvas>
 <div class="g" style="margin-top:8px">
  <button id="rzoom" onclick="rzoomT()">Show 3 m</button>
  <button onclick="rflipT()">Flip left and right</button>
  <button id="rpause" onclick="rpauseT()">Freeze</button>
 </div>
 <div id="rtab"></div>
 <h2 style="margin-top:14px">Last 60 seconds</h2>
 <canvas id="tl"></canvas>
 <div class="sub" id="rhealth" style="margin-top:8px"></div>
 <div class="sub">Watch only: the drop is still fired by the trigger line on GPIO33, not by this radar (roadmap task 4). Seen from the sensor looking out. Each ripple is one frame the sensor sent, about 10 a second; no ripples means it has gone quiet. The shaded strip is the door window, 1 m wide; it turns red when someone inside it is coming closer fast enough to arrive within 0.75 s, the rule task 4 will use. Distances run along the radar's tilted view, not the floor.</div>
</div>

<div class="card">
 <h2>Run</h2>
 <div class="g">
  <button class="p" onclick="c('drop')">Drop it now</button>
  <button id="armb" onclick="c(armed?'disarm':'arm')">Arm</button>
  <button class="d" onclick="c('stop')">Stop</button>
  <button onclick="c('off')">Motor and servo off</button>
  <button onclick="c('clear')">Clear fault</button>
 </div>
</div>

<div class="card">
 <h2>Bench: finger servo</h2>
 <div class="big" id="sdeg">-</div>
 <div class="g">
  <button onclick="nudge(-5)">-5&deg;</button><button onclick="nudge(-1)">-1&deg;</button>
  <button onclick="nudge(1)">+1&deg;</button><button onclick="nudge(5)">+5&deg;</button>
 </div>
 <div class="g">
  <button onclick="c('servo '+st.settings.setlock)">Go to lock angle</button>
  <button onclick="c('servo '+st.settings.setrel)">Go to release angle</button>
  <button onclick="c('setlock '+st.servoDeg)">Store as lock</button>
  <button onclick="c('setrel '+st.servoDeg)">Store as release</button>
 </div>
 <div class="sub">Lock = finger level in the teeth, resting on the ledge. Release = clear of the teeth toward the floor. Store, then Save settings.</div>
</div>

<div class="card">
 <h2>Bench: motor</h2>
 <div class="g">
  <button onclick="c('jog -1600')">-1 turn</button><button onclick="c('jog -200')">-1/8</button>
  <button onclick="c('jog 200')">+1/8</button><button onclick="c('jog 1600')">+1 turn</button>
 </div>
 <div class="g">
  <button onclick="c('rewind')">Rewind</button><button onclick="c('lock')">Lock</button><button onclick="c('rel')">Release</button>
 </div>
 <div class="sub">+ is the rewind direction. A rewind locks by itself once it reaches the switch. The motor stays powered after a jog or release until Lock or Off. Release winds the spool up 1/12 turn while the finger swings out, then holds the spider on the motor.</div>
</div>

<div class="card">
 <h2>Settings</h2>
 <div id="sets"></div>
 <div class="g" style="margin-top:10px">
  <button class="p" onclick="c('save')">Save settings</button>
  <button onclick="if(confirm('Load factory values? (not saved until Save)')){built=0;c('defaults')}">Factory values</button>
 </div>
</div>

<div class="card">
 <h2>Console</h2>
 <pre id="log"></pre>
 <div class="cl"><input id="cmd" placeholder="type a command, e.g. status or help" onkeydown="if(event.key==='Enter'){c(this.value);this.value=''}"><button onclick="const i=document.getElementById('cmd');c(i.value);i.value=''">Send</button></div>
</div>

<div class="card">
 <h2>Network</h2>
 <label>Network name<input id="ssid"></label>
 <label>Password<input type="password" id="pass"></label>
 <div class="g" style="margin-top:8px"><button onclick="wifi()">Save and restart</button></div>
 <div class="sub">Leave the name empty and save to go back to the network built into the firmware. If it cannot join, it makes its own network DropSpider-setup, page at 192.168.4.1.</div>
</div>

<div class="card">
 <h2>Firmware</h2>
 <div class="row"><span>Update over the network</span><a href="/update">Open the update page</a></div>
 <div class="sub">User admin, password from secrets.ini. The motor and servo switch off before the update starts.</div>
</div>

<script>
const SETS=[
 ["setlock","Finger lock angle","degrees"],["setrel","Finger release angle","degrees"],
 ["line","Line length","mm, barrel knot to stop bead, line straight not pulled"],["rpm","Rewind speed","rpm, 30 to 600"],
 ["dir","Rewind direction","0 or 1, flip if the clutch just slips"],["settle","Hang at the bottom","ms before rewind"],
 ["rearm","Lockout after a scare","ms"],["limit","Limit switch fitted","1 = the switch stops the rewind"],
 ["liminv","Limit switch reads backwards","1 = flip it"],
 ["dropmm","Drop distance","mm the spider travels, 100 to line minus 70"],
 ["droprpm","Drop top speed","rpm, 100 to 900. 610 rpm is about 1 m/s"],
 ["dropacc","Drop start rate","steps/s&sup2;, 20000 to 400000. 100000 is about 1 g"],
 ["dropdec","Drop stop rate","steps/s&sup2;, 10000 to 200000. Keep low: the motor has to stop the spider"],
 ["relms","Finger travel before the drop","ms, 100 to 600"]];
let st=null,armed=false,built=0,since=0;
function c(cmd){cmd=(cmd||'').trim();if(!cmd)return;fetch('/api/cmd',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'c='+encodeURIComponent(cmd)}).then(tick)}
function nudge(d){if(!st)return;c('servo '+Math.max(0,Math.min(180,st.servoDeg+d)))}
function wifi(){const s=document.getElementById('ssid').value,p=document.getElementById('pass').value;
 fetch('/api/wifi',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'ssid='+encodeURIComponent(s)+'&pass='+encodeURIComponent(p)}).then(()=>alert('Saved. Restarting.'))}
function ms(v){if(v<1000)return v+' ms';const s=v/1000;return s<60?s.toFixed(1)+' s':s<3600?Math.floor(s/60)+' min '+Math.round(s%60)+' s':Math.floor(s/3600)+' h '+Math.floor(s%3600/60)+' min'}
function chip(t,k){return '<span class="chip '+k+'">'+t+'</span>'}
function build(s){let h='';for(const[k,l,hint]of SETS){h+='<label><span>'+l+'<small>'+hint+'</small></span><input type="number" id="f_'+k+'" value="'+s[k]+'" onchange="c(\''+k+' \'+this.value)"></label>'}
 document.getElementById('sets').innerHTML=h;built=1}
function tick(){fetch('/api/status?since='+since).then(r=>r.json()).then(s=>{
 st=s;armed=!!s.armed;
 document.getElementById('where').textContent=s.where;
 document.getElementById('state').textContent=s.state;
 document.getElementById('drops').textContent=s.drops;
 document.getElementById('trig').textContent=s.trigger+(s.triggerAgo?' ('+ms(s.triggerAgo)+' ago)':'');
 document.getElementById('rw').textContent=s.lastRewind?(s.lastRewind+' steps of '+s.rewindSteps+(s.lastRewindLimit?', stopped by the switch':'')):'none yet';
 document.getElementById('meas').textContent=s.measuredDrop?('about '+s.measuredDrop+' mm (set '+s.settings.dropmm+')'):'not yet';
 document.getElementById('up').textContent=ms(s.uptime);
 document.getElementById('lsw').textContent=(s.limit?'closed':'open')+', closed '+s.limitCloses+' times since power-up';
 document.getElementById('sdeg').textContent=s.servoDeg+'°'+(s.servoOn?' holding':' (servo off)');
 document.getElementById('armb').textContent=armed?'Disarm':'Arm';
 let h=armed?chip('armed','ok'):chip('not armed','wa');
 h+=s.limitFitted?(s.limit?chip('spider home (switch pressed)','ok'):s.home?chip('spider home (seated on the finger)','ok'):chip('switch open, spider not home','wa')):chip('limit switch off in settings'+(s.limit?', reads pressed':', reads open'),'wa');
 h+=s.sensor?chip('trigger line (GPIO33): someone there','wa'):chip('trigger line (GPIO33): clear','ok');
 if(s.driverOn)h+=chip('motor powered','wa');
 if(s.fault)h+=chip(s.fault+(s.faultRun>1?' ('+s.faultRun+' in a row)':''),'no');
 document.getElementById('chips').innerHTML=h;
 if(s.log&&s.log.length){const L=document.getElementById('log');const atEnd=L.scrollTop+L.clientHeight>=L.scrollHeight-4;L.textContent+=s.log.join('\n')+'\n';if(atEnd)L.scrollTop=L.scrollHeight}
 since=s.next;
 if(!built)build(s.settings);else for(const[k]of SETS){const f=document.getElementById('f_'+k);if(f&&document.activeElement!==f)f.value=s.settings[k]}
}).catch(()=>{})}
tick();setInterval(tick,800);

// ---- radar view: /api/radar about 8 times a second, drawn every animation frame
const RC=['#4ac47a','#e8b44a','#a995ff'];
let rz=6,rfrozen=false,rbusy=false,rlast=null,lastFrames=-1,lastCloses=-1;
let rflip=false;try{rflip=localStorage.getItem('rflip')==='1'}catch(e){}
const trails=[[],[],[]];let ripples=[],hist=[];
function rzoomT(){rz=rz===6?3:6;document.getElementById('rzoom').textContent=rz===6?'Show 3 m':'Show 6 m'}
function rflipT(){rflip=!rflip;try{localStorage.setItem('rflip',rflip?'1':'0')}catch(e){}}
function rpauseT(){rfrozen=!rfrozen;document.getElementById('rpause').textContent=rfrozen?'Live':'Freeze'}
function fit(cv,ratio){const d=devicePixelRatio||1,w=cv.clientWidth,h=Math.round(w*ratio);
 if(cv.width!==Math.round(w*d)||cv.height!==Math.round(h*d)){cv.width=Math.round(w*d);cv.height=Math.round(h*d);cv.style.height=h+'px'}
 const x=cv.getContext('2d');x.setTransform(d,0,0,d,0,0);return[x,w,h]}
// speed worked out from the dot's own trail over the last 0.7 s, in m/s: + = coming closer
function closing(tr){if(!tr.length)return null;const p1=tr[tr.length-1];let p0=null;
 for(const q of tr){if(p1.t-q.t<=700){p0=q;break}}
 if(!p0||p1.t-p0.t<250)return null;const dt=(p1.t-p0.t)/1000;
 return{dr:(Math.hypot(p0.x,p0.y)-Math.hypot(p1.x,p1.y))/1000/dt,dy:(p0.y-p1.y)/1000/dt}}
function wouldFire(now){return trails.some(tr=>{if(!tr.length)return false;const p=tr[tr.length-1];if(now-p.t>400)return false;
 const c=closing(tr);return c&&Math.abs(p.x)<500&&c.dy>0.3&&p.y/1000/c.dy<0.75})}
function rpoll(){if(document.hidden||rbusy||rfrozen)return;rbusy=true;
 fetch('/api/radar').then(r=>r.json()).then(d=>{const now=performance.now();rlast=d;
  if(lastFrames>=0&&d.r.frames>lastFrames){const nf=Math.min(d.r.frames-lastFrames,4);for(let i=0;i<nf;i++)ripples.push(now-i*100)}
  lastFrames=d.r.frames;
  d.r.t.forEach((p,i)=>{const tr=trails[i];if(!p){tr.length=0;return}const q=tr[tr.length-1];
   if(q&&Math.hypot(q.x-p[0],q.y-p[1])>1500)tr.length=0;   // a new person took this slot
   tr.push({t:now,x:p[0],y:p[1],v:p[2]});while(tr.length&&now-tr[0].t>4000)tr.shift()});
  let near=null,n=0;d.r.t.forEach(p=>{if(p){n++;const r=Math.hypot(p[0],p[1])/1000;if(near===null||r<near)near=r}});
  const flick=lastCloses>=0&&d.closes>lastCloses;lastCloses=d.closes;
  hist.push({t:now,n,near,out:d.out,lim:d.lim||flick,busy:d.busy,talk:d.r.talking});
  while(hist.length&&now-hist[0].t>60000)hist.shift();
  rtable(d,now)}).catch(()=>{}).finally(()=>{rbusy=false})}
function rtable(d,now){const r=d.r;let h='';
 r.t.forEach((p,i)=>{if(!p)return;const c=closing(trails[i]);
  h+='<div class="row"><span><span class="key" style="background:'+RC[i]+'"></span>Person '+(i+1)+'</span><b>'+(Math.hypot(p[0],p[1])/1000).toFixed(2)+' m away'
  +(c?(c.dr>0.1?', coming closer '+c.dr.toFixed(1)+' m/s':c.dr<-0.1?', moving away '+(-c.dr).toFixed(1)+' m/s':', standing'):'')+'</b></div>'
  +'<div class="row"><span>&nbsp;&nbsp;across '+(p[0]/1000).toFixed(2)+' m, out '+(p[1]/1000).toFixed(2)+' m</span><span>sensor says '+p[2]+' cm/s</span></div>'});
 document.getElementById('rtab').innerHTML=h||(r.talking?'<div class="row"><span>Nobody in view</span><b>-</b></div>':'');
 const n=r.t.filter(Boolean).length,f=wouldFire(now);
 let c=r.talking?chip('radar talking, '+r.fps.toFixed(1)+' frames/s','ok'):chip(r.frames?'radar silent '+ms(r.age):'no radar frames yet','no');
 if(r.talking)c+=n?chip(n+(n>1?' people':' person')+' in view','wa'):chip('nobody in view','ok');
 if(f)c+=chip('would fire now (preview)','no');
 document.getElementById('rchips').innerHTML=c;
 document.getElementById('rhealth').textContent=!r.bytes?'Nothing heard on RX2 (GPIO16) since power-up: check the LD2450 has 5 V and its TX wire goes to RX2.'
  :!r.frames?r.bytes+' bytes heard on RX2 but no LD2450 frames: wrong sensor on that pin, or a loose wire.'
  :'Frames '+r.frames+', bad '+r.bad+', bytes '+r.bytes+'. "Sensor says" is the radar\'s own speed reading; check its sign against the trail (test S2).'}
function rdraw(){requestAnimationFrame(rdraw);if(document.hidden)return;
 const cv=document.getElementById('scope');if(!cv.clientWidth)return;const[x,w,h]=fit(cv,.6);const now=performance.now();
 const cx=w/2,by=h-12,R=Math.min(h-24,(w/2-34)/Math.sin(Math.PI/3)),k=R/(rz*1000),sx=rflip?-1:1;
 const P=(mx,my)=>[cx+sx*mx*k,by-my*k],a0=-Math.PI*5/6,a1=-Math.PI/6;
 x.clearRect(0,0,w,h);
 const fan=()=>{x.beginPath();x.moveTo(cx,by);x.arc(cx,by,R,a0,a1);x.closePath()};
 fan();x.fillStyle='rgba(122,92,255,.07)';x.fill();
 x.save();fan();x.clip();
 const fire=wouldFire(now),[d0]=P(-500,0),[d1]=P(500,0);
 x.fillStyle=fire?'rgba(226,96,79,.30)':'rgba(232,180,74,.08)';x.fillRect(Math.min(d0,d1),0,Math.abs(d1-d0),by);
 x.setLineDash([4,4]);x.strokeStyle=fire?'#e2604f':'rgba(232,180,74,.45)';x.beginPath();x.moveTo(d0,by);x.lineTo(d0,0);x.moveTo(d1,by);x.lineTo(d1,0);x.stroke();x.setLineDash([]);
 ripples=ripples.filter(t=>now-t<900);
 for(const t of ripples){const f=(now-t)/900;x.strokeStyle='rgba(169,149,255,'+(.4*(1-f)).toFixed(3)+')';x.beginPath();x.arc(cx,by,Math.max(1,f*R),a0,a1);x.stroke()}
 x.restore();
 x.strokeStyle='#332e3d';x.font='11px system-ui';x.fillStyle='#9a93a8';
 for(let m=1;m<=rz;m++){x.beginPath();x.arc(cx,by,m*1000*k,a0,a1);x.stroke();x.fillText(m+' m',cx+Math.cos(a1)*m*1000*k+4,by+Math.sin(a1)*m*1000*k+4)}
 x.beginPath();x.moveTo(cx,by);x.lineTo(cx+Math.cos(a0)*R,by+Math.sin(a0)*R);x.moveTo(cx,by);x.lineTo(cx+Math.cos(a1)*R,by+Math.sin(a1)*R);x.stroke();
 x.fillText('door window',Math.max(d0,d1)+4,14);
 trails.forEach((tr,i)=>{if(!tr.length)return;const c=RC[i];x.strokeStyle=c;x.lineWidth=2;
  for(let j=1;j<tr.length;j++){const[ax,ay]=P(tr[j-1].x,tr[j-1].y),[bx,bb]=P(tr[j].x,tr[j].y);
   x.globalAlpha=Math.max(0,1-(now-tr[j].t)/4000)*.8;x.beginPath();x.moveTo(ax,ay);x.lineTo(bx,bb);x.stroke()}
  x.globalAlpha=1;x.lineWidth=1;const p=tr[tr.length-1];if(now-p.t>1500)return;const[px,py]=P(p.x,p.y);
  x.fillStyle=c;x.beginPath();x.arc(px,py,7,0,Math.PI*2);x.fill();
  x.strokeStyle=c;x.globalAlpha=.5;x.beginPath();x.arc(px,py,10+3*Math.sin(now/180),0,Math.PI*2);x.stroke();x.globalAlpha=1;
  const cl=closing(tr);x.fillStyle='#ece9f2';x.font='600 12px system-ui';
  x.fillText((i+1)+'  '+(Math.hypot(p.x,p.y)/1000).toFixed(1)+' m'+(cl?(cl.dr>0.1?', closer':cl.dr<-0.1?', away':''):''),px+14,py-8)});
 x.fillStyle='#7a5cff';x.fillRect(cx-16,by,32,7);
 if(!rlast||!rlast.r.talking){x.fillStyle='rgba(11,10,14,.72)';x.fillRect(0,0,w,h);x.fillStyle='#e2604f';x.font='600 15px system-ui';x.textAlign='center';
  x.fillText(!rlast?'waiting for the board':rlast.r.frames?'radar silent':'no radar frames yet',cx,h/2);x.textAlign='left'}
 if(rfrozen){x.fillStyle='#e8b44a';x.font='600 12px system-ui';x.fillText('FROZEN',8,16)}
 rtl(now)}
function rtl(now){const cv=document.getElementById('tl');if(!cv.clientWidth)return;const[x,w,h]=fit(cv,.38);x.clearRect(0,0,w,h);
 const L=Math.min(150,w*.34),lanes=['people in view','nearest person','trigger line (GPIO33)','limit switch','motor or finger working'],lh=(h-16)/lanes.length;
 const T=t=>L+(w-L-4)*(1-(now-t)/60000);x.font='11px system-ui';
 lanes.forEach((l,i)=>{x.fillStyle='#9a93a8';x.fillText(l,4,i*lh+lh/2+4);x.strokeStyle='#332e3d';x.beginPath();x.moveTo(L,(i+1)*lh);x.lineTo(w,(i+1)*lh);x.stroke()});
 for(let s=0;s<=60;s+=15){const tx=T(now-s*1000);x.fillStyle='#9a93a8';x.fillText(s?'-'+s+' s':'now',Math.max(L,tx-(s?14:24)),h-3)}
 const Y=v=>lh+3+(lh-6)*Math.min(v,6)/6;
 for(let j=1;j<hist.length;j++){const a=hist[j-1],b=hist[j],x0=T(a.t),x1=T(b.t),ww=Math.max(1,x1-x0);
  if(!a.talk){x.fillStyle='rgba(226,96,79,.18)';x.fillRect(x0,3,ww,lh-6)}
  if(a.n){x.fillStyle='#4ac47a';const hh=(lh-6)*a.n/3;x.fillRect(x0,lh-3-hh,ww,hh)}
  if(a.out){x.fillStyle='#e8b44a';x.fillRect(x0,2*lh+3,ww,lh-6)}
  if(a.lim){x.fillStyle='#e2604f';x.fillRect(x0,3*lh+3,ww,lh-6)}
  if(a.busy){x.fillStyle='#7a5cff';x.fillRect(x0,4*lh+3,ww,lh-6)}
  if(a.near!==null&&b.near!==null){x.strokeStyle='#a995ff';x.lineWidth=2;x.beginPath();x.moveTo(x0,Y(a.near));x.lineTo(x1,Y(b.near));x.stroke();x.lineWidth=1}}}
setInterval(rpoll,120);requestAnimationFrame(rdraw);
</script></body></html>)HTML";

static const char UPDATE_PAGE[] PROGMEM = R"HTML(<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>DropSpider update</title>
<style>body{background:#121016;color:#ece9f2;font:16px system-ui,sans-serif;padding:16px;max-width:560px;margin:auto}
input,button{font:inherit;margin:8px 0}button{background:#7a5cff;color:#fff;border:0;border-radius:10px;padding:12px 18px}a{color:#a995ff}</style></head><body>
<h1>Firmware update</h1>
<p>Pick <b>.pio/build/nodemcu-32s/firmware.bin</b> from the repo, then Upload. The motor and servo switch off first; the board restarts when it is done and never rewinds on its own.</p>
<form method="POST" action="/update" enctype="multipart/form-data"><input type="file" name="firmware" accept=".bin"><br><button>Upload</button></form>
<p><a href="/">Back</a></p></body></html>)HTML";

// ---------------------------------------------------------------------------

static String jsonEscape(const String &in) {
  String out; out.reserve(in.length() + 8);
  for (size_t i = 0; i < in.length(); i++) {
    char c = in[i];
    if (c == '"') out += "\\\"";
    else if (c == '\\') out += "\\\\";
    else if ((uint8_t)c >= 0x20) out += c;
  }
  return out;
}

static void sendStatus() {
  MachineStatus m = machineStatus();
  uint32_t since = server.arg("since").toInt(), next = 0;
  String log = logJsonSince(since, next);
  String j = "{";
  j += "\"where\":\"" + jsonEscape(whereAmI) + "\"";
  j += ",\"state\":\"" + String(m.state) + "\"";
  j += ",\"busy\":" + String(m.busy);
  j += ",\"armed\":" + String(m.armed);
  j += ",\"sensor\":" + String(m.sensor);
  j += ",\"limit\":" + String(m.limitRaw);
  j += ",\"limitCloses\":" + String(m.limitCloses);
  j += ",\"limitFitted\":" + String(m.limitFitted);
  j += ",\"driverOn\":" + String(m.driverOn);
  j += ",\"servoOn\":" + String(m.servoAttached);
  j += ",\"servoDeg\":" + String(m.servoDeg);
  j += ",\"position\":" + String(m.position);
  j += ",\"rewindSteps\":" + String(m.rewindSteps);
  j += ",\"lastRewind\":" + String(m.lastRewindSteps);
  j += ",\"lastRewindLimit\":" + String(m.lastRewindByLimit);
  j += ",\"measuredDrop\":" + String(m.measuredDropMm);
  j += ",\"home\":" + String(m.home);
  j += ",\"drops\":" + String(m.drops);
  j += ",\"trigger\":\"" + String(triggerName(m.lastTrigger)) + "\"";
  j += ",\"triggerAgo\":" + String(m.lastTriggerAgoMs);
  j += ",\"fault\":\"" + jsonEscape(m.fault) + "\"";
  j += ",\"faultRun\":" + String(m.faultRun);
  j += ",\"uptime\":" + String(millis());
  j += ",\"settings\":{" + settingsJson() + "}";
  j += ",\"log\":[" + log + "],\"next\":" + String(next);
  j += "}";
  server.send(200, "application/json", j);
}

static void startNetwork() {
  String ssid = wifiSavedSsid(), pass = wifiSavedPass();
  if (!ssid.length()) { ssid = WIFI_SSID; pass = WIFI_PASS; }

  WiFi.setHostname(HOSTNAME);
  if (ssid.length()) {
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(true);
    WiFi.begin(ssid.c_str(), pass.c_str());          // DHCP: the router picks the address
    logf("[wifi] joining %s", ssid.c_str());
    uint32_t t0 = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_JOIN_TIMEOUT_MS) delay(250);
    if (WiFi.status() == WL_CONNECTED) {
      apMode = false;
      whereAmI = "on " + ssid + " at " + WiFi.localIP().toString() + ", also http://" HOSTNAME ".local";
      return;
    }
    logf("[wifi] could not join %s, making my own network instead", ssid.c_str());
  }
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  apMode = true;
  whereAmI = String("own network ") + AP_SSID + " (password " AP_PASSWORD "), page at " + WiFi.softAPIP().toString();
}

static void startOta() {
  ArduinoOTA.setHostname(HOSTNAME);
  ArduinoOTA.setPassword(OTA_PASS);
  ArduinoOTA.onStart([]() { machineSafeStop(); logf("[update] network update starting: motor and servo off"); });
  ArduinoOTA.onEnd([]() { logf("[update] done, restarting"); });
  ArduinoOTA.onError([](ota_error_t e) { logf("[update] failed, error %u", (unsigned)e); });
  ArduinoOTA.begin();                                 // also starts mDNS as dropspider.local
  MDNS.addService("http", "tcp", 80);
}

void webBegin() {
  startNetwork();
  startOta();

  server.on("/", HTTP_GET, []() { server.send_P(200, "text/html", PAGE); });
  server.on("/api/status", HTTP_GET, sendStatus);
  server.on("/api/radar", HTTP_GET, []() {             // small and fast: the page asks about 8 times a second
    MachineStatus m = machineStatus();
    String j = "{\"r\":" + radarJson() + ",\"out\":" + String(m.sensor) + ",\"lim\":" + String(m.limitRaw) +
               ",\"closes\":" + String(m.limitCloses) + ",\"busy\":" + String(m.busy) + "}";
    server.send(200, "application/json", j);
  });

  server.on("/api/cmd", HTTP_POST, []() {
    String out;
    consoleRun(server.arg("c"), &out);
    server.send(200, "text/plain", out);
  });

  server.on("/api/wifi", HTTP_POST, []() {
    wifiSave(server.arg("ssid"), server.arg("pass"));
    server.send(200, "text/plain", "ok");
    logf("[wifi] new network saved, restarting");
    delay(300);
    machineSafeStop();
    ESP.restart();
  });

  server.on("/update", HTTP_GET, []() {
    if (!server.authenticate(OTA_USER, OTA_PASS)) return server.requestAuthentication();
    server.send_P(200, "text/html", UPDATE_PAGE);
  });
  server.on("/update", HTTP_POST,
    []() {
      if (uploadRefused) { uploadRefused = false; return server.requestAuthentication(); }
      bool ok = !Update.hasError();
      server.send(200, "text/plain", ok ? "Update done. Restarting." : "Update FAILED. Old firmware kept.");
      if (ok) { delay(500); ESP.restart(); }
    },
    []() {
      HTTPUpload &up = server.upload();
      if (up.status == UPLOAD_FILE_START) {
        uploadRefused = !server.authenticate(OTA_USER, OTA_PASS);
        if (uploadRefused) return;
        machineSafeStop();
        logf("[update] web upload %s starting: motor and servo off", up.filename.c_str());
        Update.begin(UPDATE_SIZE_UNKNOWN);
      } else if (uploadRefused) {
        return;
      } else if (up.status == UPLOAD_FILE_WRITE) {
        Update.write(up.buf, up.currentSize);
      } else if (up.status == UPLOAD_FILE_END) {
        if (Update.end(true)) logf("[update] %u bytes written", up.totalSize);
        else logf("[update] failed: %s", Update.errorString());
      }
    });

  server.onNotFound([]() { server.send(404, "text/plain", "no such page"); });
  server.begin();
}

void webLoop() {
  ArduinoOTA.handle();
  server.handleClient();
}

String webWhereAmI() { return whereAmI; }
