#include "web.h"
#include "config.h"
#include "settings.h"
#include "machine.h"
#include "console.h"
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
 <div class="row"><span>Running for</span><b id="up">-</b></div>
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
 <div class="sub">+ is the rewind direction. The motor stays powered after a jog, rewind or release until Lock or Off. Release winds the spool up 1/12 turn while the finger swings out, then holds the spider on the motor.</div>
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
 document.getElementById('sdeg').textContent=s.servoDeg+'°'+(s.servoOn?' holding':' (servo off)');
 document.getElementById('armb').textContent=armed?'Disarm':'Arm';
 let h=armed?chip('armed','ok'):chip('not armed','wa');
 h+=s.limitFitted?(s.limit?chip('spider home (switch pressed)','ok'):s.home?chip('spider home (seated on the finger)','ok'):chip('switch open, spider not home','wa')):chip('limit switch off in settings'+(s.limit?', reads pressed':', reads open'),'wa');
 h+=s.sensor?chip('radar: someone there','wa'):chip('radar: clear','ok');
 if(s.driverOn)h+=chip('motor powered','wa');
 if(s.fault)h+=chip(s.fault+(s.faultRun>1?' ('+s.faultRun+' in a row)':''),'no');
 document.getElementById('chips').innerHTML=h;
 if(s.log&&s.log.length){const L=document.getElementById('log');const atEnd=L.scrollTop+L.clientHeight>=L.scrollHeight-4;L.textContent+=s.log.join('\n')+'\n';if(atEnd)L.scrollTop=L.scrollHeight}
 since=s.next;
 if(!built)build(s.settings);else for(const[k]of SETS){const f=document.getElementById('f_'+k);if(f&&document.activeElement!==f)f.value=s.settings[k]}
}).catch(()=>{})}
tick();setInterval(tick,800);
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
