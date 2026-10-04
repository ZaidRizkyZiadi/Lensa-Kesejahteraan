/* Hero scroll, latar prosedural (tanpa karakter), cerita, detail sumber, penempatan grafik Dash */
(function(){"use strict";
var $=function(i){return document.getElementById(i)},B=document.body,P=window.P3DATA||{},SRC=window.P3SOURCES||[];
function snd(f){try{var a=new Audio("/assets/sfx/"+f);a.volume=.6;a.play().catch(function(){});}catch(e){}}

/* ---------- hero: menu muncul hanya setelah digeser ---------- */
var hero=$("intro-hero"),active=true,moving=false;B.classList.add("hero-on");
window.p3HeroActive=function(){return active};
function started(){var l=$("loading-screen");return !l||l.classList.contains("dismissed")||l.style.display==="none"||getComputedStyle(l).display==="none";}
function pageOpen(){return document.querySelector(".p3r-slink-screen.active,.p3r-slink-screen.circle-transitioning,.portfolio-modal.open");}
function replayMenu(){["menu-column","menu-profile-header"].forEach(function(i){var e=$(i);if(e){e.classList.remove("menu-entered");void e.offsetWidth;e.classList.add("menu-entered");}});}
function hide(){if(!active||moving||!started())return;moving=true;B.classList.remove("hero-on");replayMenu();hero.classList.add("away");setTimeout(function(){active=false;moving=false;},950);}
function show(){if(active||moving||pageOpen())return;moving=true;active=true;hero.classList.remove("away");B.classList.add("hero-on");setTimeout(function(){moving=false;},950);}
var t0=setInterval(function(){if(started()){hero.classList.add("in");clearInterval(t0);}},150);
$("hero-cue").addEventListener("click",hide);
window.addEventListener("wheel",function(e){if(!started())return;if(active&&e.deltaY>15)hide();else if(!active&&e.deltaY<-15)show();},{passive:true});
document.addEventListener("keydown",function(e){if(active&&started()&&["ArrowDown","Enter"," ","PageDown"].indexOf(e.key)>-1){e.preventDefault();hide();}});
var ty=0;window.addEventListener("touchstart",function(e){ty=e.touches[0].clientY;},{passive:true});
window.addEventListener("touchend",function(e){var d=ty-e.changedTouches[0].clientY;if(d>50)hide();else if(d<-50)show();},{passive:true});

/* ---------- cerita (webstory) dari data ---------- */
var st=P.stories||{};["belanja","peta"].forEach(function(k){var el=$("story-"+k);if(el&&st[k])el.innerHTML=st[k];});

/* ---------- detail sumber (halaman SUMBER) ---------- */
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
/* isi URL boleh lebih dari satu baris (pisah dengan \n); setiap alamat http(s) dijadikan tautan, teks lain tetap teks biasa */
function links(v){return String(v).split("\n").map(function(line){var out="",last=0,re=/https?:\/\/\S+/g,m;
  while((m=re.exec(line))){out+=esc(line.slice(last,m.index))+'<a href="'+esc(m[0])+'" target="_blank" rel="noopener">'+esc(m[0])+'</a>';last=m.index+m[0].length;}
  return out+esc(line.slice(last));}).join("<br>");}
var FIELDS=[["Nama data","judul"],["Tahun data","tahun"],["URL","url"],["Tanggal akses","akses"],["Satuan","satuan"],["Dipakai untuk","dipakai"],["File olahan","file"],["Catatan","catatan"]];
function openSrc(i){var d=SRC[i];if(!d)return;$("src-title").textContent=d.phrase;
  $("src-body").innerHTML=FIELDS.map(function(f){var v=d[f[1]];if(v===undefined)return"";
    var h=v===""?'<span class="empty">BELUM DIISI (isi di SOURCES pada app.py)</span>':v==="-"?'<span class="na">tidak berlaku</span>':f[1]==="url"?links(v):esc(v);
    return'<div class="p3-src-row"><span class="k">'+f[0]+'</span><span>'+h+'</span></div>';}).join("");
  var el=$("src-detail");el.classList.add("open");el.setAttribute("aria-hidden","false");snd("navigation.wav");}
function closeSrc(){var el=$("src-detail");el.classList.remove("open");el.setAttribute("aria-hidden","true");snd("close-menu.mp3");}
function srcOpen(){return $("src-detail").classList.contains("open");}
document.addEventListener("click",function(e){var r=e.target.closest&&e.target.closest(".p3r-mail-row");if(r&&$("contact-page").classList.contains("active")&&!srcOpen()){openSrc(parseInt(r.getAttribute("data-idx"),10));return;}
  if(e.target.closest&&(e.target.closest("#src-close")||e.target===$("src-detail")))closeSrc();});
window.addEventListener("keydown",function(e){
  if(srcOpen()){e.stopImmediatePropagation();e.preventDefault();if(e.key==="Escape"||e.key==="Enter")closeSrc();return;}
  if(e.key==="Enter"&&$("contact-page").classList.contains("active")){var r=document.querySelector(".p3r-mail-row.active");if(r){e.stopImmediatePropagation();e.preventDefault();openSrc(parseInt(r.getAttribute("data-idx"),10));}}},true);

/* ---------- latar prosedural bergaya P3R (pengganti video; tanpa karakter) ---------- */
var TH={menu:{a:"#0b2fa8",b:"#001660",g:"110,215,255",s:"255,255,255"},belanja:{a:"#f1f4f8",b:"#c3cfdf",g:"2,158,235",s:"6,52,190",light:1},
 peta:{a:"#0a3bd0",b:"#00155e",g:"80,200,255",s:"255,255,255"},korelasi:{a:"#25cbf7",b:"#0a7fd0",g:"255,255,255",s:"2,18,66"},
 sumber:{a:"#080c18",b:"#0a1630",g:"22,120,255",s:"22,207,251",dots:1}};
var CV=[];
function mk(before,name,fixed,screen){if(!before||!before.parentNode)return;var c=document.createElement("canvas");c.className="p3-bgc"+(fixed?" fixed":"");before.parentNode.insertBefore(c,before);
  var bub=[];for(var i=0;i<26;i++)bub.push({x:Math.random(),y:Math.random(),r:1+Math.random()*3,v:.4+Math.random()});
  CV.push({c:c,x:c.getContext("2d"),th:TH[name],name:name,screen:screen,bub:bub,dots:null,seed:Math.random()*50});}
mk($("background-video-intro"),"menu",true,null);
[["project-page","belanja"],["skill-page","korelasi"],["about-page","peta"],["contact-page","sumber"]].forEach(function(p){var s=$(p[0]);if(s)mk(s.querySelector(".slink-bg-video"),p[1],false,s);});
function draw(o,t){var c=o.c,x=o.x,th=o.th,W=Math.round(innerWidth/2),H=Math.round(innerHeight/2);if(c.width!==W||c.height!==H){c.width=W;c.height=H;o.dots=null;}
  var g=x.createLinearGradient(0,0,0,H);g.addColorStop(0,th.a);g.addColorStop(1,th.b);x.globalCompositeOperation="source-over";x.fillStyle=g;x.fillRect(0,0,W,H);
  x.globalCompositeOperation=th.light?"source-over":"lighter";
  for(var i=0;i<6;i++){var px=(.5+.45*Math.sin(t*.00018*(1+i*.3)+i*1.9+o.seed))*W,py=(.5+.4*Math.cos(t*.00015*(1+i*.25)+i*2.3))*H,r=(.22+.06*(i%3))*Math.max(W,H);
    var rg=x.createRadialGradient(px,py,0,px,py,r);rg.addColorStop(0,"rgba("+th.g+","+(th.light?.16:.2)+")");rg.addColorStop(1,"rgba("+th.g+",0)");x.fillStyle=rg;x.fillRect(0,0,W,H);}
  x.globalCompositeOperation="source-over";
  for(var j=0;j<5;j++){var w=(.03+.025*(j%3))*W,sx=((t*.012*(1+j*.35)+j*W*.37)%(W*1.5))-W*.25;x.save();x.translate(sx,H*.5);x.rotate(-.38);
    x.fillStyle="rgba("+th.s+","+(.06+.03*(j%2))+")";x.fillRect(-w/2,-H,w,H*2);x.restore();}
  x.fillStyle="rgba("+(th.light?"2,110,200":"255,255,255")+",.28)";
  o.bub.forEach(function(b){var py=(((b.y-t*b.v*.00004)%1)+1)%1*H,px=b.x*W+Math.sin(t*.001+b.x*9)*6;x.beginPath();x.arc(px,py,b.r,0,6.283);x.fill();});
  if(th.dots){if(!o.dots){var d=document.createElement("canvas");d.width=W;d.height=H;var q=d.getContext("2d");q.fillStyle="rgba(22,120,255,.38)";
      for(var gx=0;gx<W;gx+=9)for(var gy=0;gy<H;gy+=9){var rr=Math.max(0,(gx/W)*1.25-.3)*3.4;if(rr>.3){q.beginPath();q.arc(gx,gy,rr,0,6.283);q.fill();}}o.dots=d;}
    x.drawImage(o.dots,0,0);}}
var last=0;(function loop(t){requestAnimationFrame(loop);if(t-last<34)return;last=t;var anyActive=document.querySelector(".p3r-slink-screen.active");
  CV.forEach(function(o){var vis=o.name==="menu"?!anyActive:(o.screen.classList.contains("active")||o.screen.classList.contains("circle-transitioning"));if(vis)draw(o,t);});})(0);

/* ---------- kontrol UI zip -> grafik Dash ---------- */
window.p3SetYear=function(y){try{window.dash_clientside.set_props("year-store",{data:y});}catch(e){}};
window.p3SetFocus=function(i){var gd=document.querySelector("#slot-treemap .js-plotly-plot");if(!gd||!window.Plotly)return;
  Plotly.restyle(gd,{level:["","Total Pengeluaran/Makanan","Total Pengeluaran/Bukan Makanan"][i]||""});};

/* ---------- tempatkan grafik saat halaman terbuka, ubah ukuran, animasikan ---------- */
var MAP={"project-page":["slot-treemap","wrap-treemap","treemap"],"about-page":["slot-map","wrap-map","map"],"skill-page":["slot-splom","wrap-splom","splom"]};
function tween(d,fn,done){var s0=null;requestAnimationFrame(function s(ts){if(s0===null)s0=ts;var p=Math.min((ts-s0)/d,1);fn(1-Math.pow(1-p,3));if(p<1)requestAnimationFrame(s);else if(done)done();});}
function animate(kind,slot,tries){tries=tries||0;var gd=slot.querySelector(".js-plotly-plot"),Pl=window.Plotly;
  if(!gd||!gd._fullData||!Pl){if(tries<15)setTimeout(function(){animate(kind,slot,tries+1)},250);return;}
  Pl.Plots.resize(gd);
  if(kind==="treemap"){[1,2,3].forEach(function(d,i){setTimeout(function(){Pl.restyle(gd,{maxdepth:d});},i*520);});setTimeout(function(){Pl.restyle(gd,{maxdepth:-1});},1750);}
  else if(kind==="map"){var ca=gd._fullLayout&&gd._fullLayout.coloraxis;if(!ca||typeof ca.cmax!=="number")return;var lo=ca.cmin,hi=ca.cmax;
    tween(1800,function(e){Pl.relayout(gd,{"coloraxis.cmax":lo+(hi-lo)*Math.max(e,.03)});},function(){Pl.relayout(gd,{"coloraxis.cmax":hi});});}
  else if(kind==="splom"){tween(900,function(e){Pl.restyle(gd,{"marker.size":Math.max(.1,7*e)});},function(){Pl.restyle(gd,{"marker.size":7});});}}
function mount(id){var m=MAP[id],slot=$(m[0]),w=$(m[1]);if(!slot||!w)return false;if(w.parentNode!==slot)slot.appendChild(w);
  slot.querySelectorAll(".js-plotly-plot").forEach(function(g){window.Plotly&&Plotly.Plots.resize(g);});return true;}
Object.keys(MAP).forEach(function(id){var el=$(id),was=false;if(!el)return;
  new MutationObserver(function(){var c=el.classList,opening=c.contains("circle-transitioning")||c.contains("active");
    if(opening)mount(id);if(c.contains("active")&&!was){was=true;setTimeout(function(){animate(MAP[id][2],$(MAP[id][0]));},350);}
    if(!opening)was=false;}).observe(el,{attributes:true,attributeFilter:["class"]});});
window.addEventListener("resize",function(){document.querySelectorAll(".p3-slot .js-plotly-plot").forEach(function(g){window.Plotly&&Plotly.Plots.resize(g);});});
})();