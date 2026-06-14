# -*- coding: utf-8 -*-
"""SVG 고지도 HTML 생성 + 플레이 모드(직접 경로 그리고 채점).
경로 비교 답안(answer)은 Python(solver)이 계산해 주입한다. 단방향 흐름."""
import json


def build_map(cities, ghosts, selected, answer, start=None, show_ghosts=False,
              terrain=False, costs=None, barriers=None, cr=None, cart_center=None, geo=None, info=None, pedia=None, paths=None,
              force_mode=None, metrics=None, orbis=None, scenario=None):
    return (TEMPLATE
            .replace("%%SCENARIO%%", json.dumps(scenario or None, ensure_ascii=False))
            .replace("%%METRICS%%", json.dumps(metrics or {}, ensure_ascii=False))
            .replace("%%ORBIS%%", json.dumps(orbis, ensure_ascii=False))
            .replace("%%FORCEMODE%%", json.dumps(force_mode))
            .replace("%%PATHS%%", json.dumps(paths or {}, ensure_ascii=False))
            .replace("%%PEDIA%%", json.dumps(pedia or {}, ensure_ascii=False))
            .replace("%%INFO%%", json.dumps(info or {}, ensure_ascii=False))
            .replace("%%GEO%%", json.dumps(geo or {}, ensure_ascii=False))
            .replace("%%CITIES%%", json.dumps(cities, ensure_ascii=False))
            .replace("%%GHOSTS%%", json.dumps(ghosts if show_ghosts else [], ensure_ascii=False))
            .replace("%%SELECTED%%", json.dumps(selected, ensure_ascii=False))
            .replace("%%START%%", json.dumps(start, ensure_ascii=False))
            .replace("%%ANSWER%%", json.dumps(answer, ensure_ascii=False))
            .replace("%%TERRAIN%%", json.dumps(bool(terrain)))
            .replace("%%COSTS%%", json.dumps(costs or {}, ensure_ascii=False))
            .replace("%%BARRIERS%%", json.dumps(barriers or [], ensure_ascii=False))
            .replace("%%CR%%", json.dumps(cr or {}, ensure_ascii=False))
            .replace("%%CARTCENTER%%", json.dumps(cart_center, ensure_ascii=False)))


TEMPLATE = r"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root{ --parchment:#e9ddbf; --parchment-edge:#d8c8a0; --ink:#463827; --ink-soft:#6b5a3e;
    --route:#8a3d2a; --player:#2f6f7a; --gold:#b0822c; --sea:#a9bcb1; --ghost:#5a5f86; }
  *{box-sizing:border-box; -webkit-user-select:none; user-select:none;} html,body{margin:0}
  body{ font-family:"Noto Serif KR",serif; color:var(--ink); background:transparent; }
  .map-wrap{ position:relative; width:100%; }
  svg.map{ display:block; width:100%; height:auto; cursor:grab; touch-action:none; }
  svg.map.drag{ cursor:grabbing; } svg.map .city{ cursor:pointer; } svg.map.drag .city{ cursor:grabbing; }
  .panel{ position:absolute; background:rgba(233,221,191,.94); border:1px solid var(--ink-soft);
    border-radius:3px; box-shadow:0 3px 12px rgba(0,0,0,.35); }
  .zoom{ left:16px; bottom:16px; display:flex; flex-direction:column; padding:5px; gap:5px; z-index:5; }
  .zoom button{ width:30px; height:30px; border:1px solid var(--ink-soft); background:rgba(255,255,255,.25);
    color:var(--ink); font-family:"Noto Serif KR",serif; font-size:16px; border-radius:3px; cursor:pointer; line-height:1; }
  .zoom button.rst{ font-size:11px; }
  .viz{ right:16px; top:54px; display:none; flex-direction:column; padding:5px; gap:5px; z-index:5; }
  .viz.show{ display:flex; }
  .viz button{ width:104px; height:28px; border:1px solid var(--ink-soft); background:rgba(255,255,255,.25);
    color:var(--ink); font-family:"Noto Serif KR",serif; font-size:12px; border-radius:3px; cursor:pointer; line-height:1; }
  .viz button.on{ background:var(--player); color:#f3ece0; border-color:var(--player); }
  .mode{ left:50%; transform:translateX(-50%); top:14px; display:flex; padding:3px; gap:0; z-index:6; }
  .mode button{ border:1px solid var(--ink-soft); background:rgba(255,255,255,.3); color:var(--ink);
    font-family:"Noto Serif KR",serif; font-size:12px; padding:5px 13px; cursor:pointer; line-height:1; }
  .mode button:first-child{ border-radius:3px 0 0 3px; }
  .mode button:last-child{ border-radius:0 3px 3px 0; border-left:none; }
  .mode button.on{ background:var(--gold); color:#fff; border-color:var(--gold); }
  .pediaBtn{ position:absolute; right:16px; top:16px; width:36px; height:30px; z-index:7;
    border:1px solid var(--ink-soft); background:rgba(233,221,191,.94); border-radius:3px; cursor:pointer; font-size:15px; }
  .pedia{ right:16px; top:16px; width:344px; max-height:calc(100% - 32px); z-index:7; display:none;
    flex-direction:column; padding:0; overflow:hidden; }
  .pedia.show{ display:flex; }
  .pedia .pHd{ display:flex; align-items:center; justify-content:space-between; padding:9px 12px;
    border-bottom:1px solid var(--ink-soft); background:rgba(216,200,160,.55); }
  .pedia .pHd b{ font-size:14px; } .pedia .pX{ border:none; background:none; cursor:pointer; font-size:14px; color:var(--ink-soft); }
  .pedia .pBody{ padding:9px 13px 14px; overflow:auto; }
  .pedia .sec{ font-weight:700; font-size:12px; color:var(--route); letter-spacing:2px; margin:11px 0 3px; }
  .pedia .subsec{ font-weight:700; font-size:10.5px; color:var(--ink-soft); margin:7px 0 1px; letter-spacing:1px; }
  .pedia .ent{ cursor:pointer; font-size:12.5px; padding:2px 0 2px 6px; color:var(--ink); }
  .pedia .ent:hover{ color:var(--player); }
  .pedia .back{ cursor:pointer; color:var(--ink-soft); font-size:11px; margin-bottom:7px; display:inline-block; }
  .pedia .anm{ font-weight:700; font-size:16px; } .pedia .arg{ color:var(--route); font-size:11px; margin:2px 0 9px; letter-spacing:1px; }
  .pedia .abd{ font-size:13px; line-height:1.66; white-space:pre-wrap; }
  .game{ left:50%; transform:translateX(-50%); bottom:14px; padding:8px 12px 10px; width:248px; z-index:5; font-size:12px; display:none; }
  .game.show{ display:block; }
  .game.collapsed .body{ display:none; }
  .game .hd{ display:flex; align-items:center; justify-content:space-between; }
  .game .col{ border:none; background:none; cursor:pointer; font-size:14px; color:var(--ink-soft); padding:0 2px; line-height:1; }
  .game .ttl{ font-weight:700; font-size:13px; }
  .game .prog{ color:var(--ink-soft); margin-bottom:8px; }
  .game .btns{ display:flex; gap:6px; }
  .game button{ flex:1; padding:5px 0; border:1px solid var(--ink-soft); background:rgba(255,255,255,.3);
    color:var(--ink); font-family:"Noto Serif KR",serif; font-size:12px; border-radius:3px; cursor:pointer; }
  .game button.primary{ background:var(--player); color:#f3ece0; border-color:var(--player); }
  .game .score{ margin-top:8px; line-height:1.5; display:none; max-height:230px; overflow:auto; }
  .game .score.show{ display:block; }
  .game .score b{ color:var(--player); } .game .score .opt{ color:var(--route); font-weight:700; }
  .game .score table.legs{ width:100%; border-collapse:collapse; font-size:11px; }
  .game .score table.legs th{ text-align:left; color:var(--ink-soft); font-weight:700; border-bottom:1px solid var(--ink-soft); padding:1px 4px; }
  .game .score table.legs td{ padding:1px 3px; } .game .score table.legs td.c, .game .score table.legs th.c{ text-align:right; white-space:nowrap; }
  .game .score table.legs .hl{ color:var(--route); font-weight:700; }
  .game .score table.legs tr.tot td{ border-top:1px solid var(--ink-soft); }
  .game .score .ohead{ font-size:11px; color:var(--gold); font-weight:700; margin-bottom:3px; letter-spacing:1px; }
  .game .score .cmp{ margin-top:5px; }
  .game .khan{ display:none; margin-bottom:8px; padding:6px 8px; border:1px solid var(--gold);
    border-radius:3px; background:rgba(193,154,73,.10); }
  .game .khan.show{ display:block; }
  .game .khan .kh{ font-size:10px; color:var(--gold); font-weight:700; letter-spacing:2px; margin-bottom:2px; }
  .game .khan .kc{ font-size:11.5px; line-height:1.5; color:var(--ink); white-space:pre-wrap; }
  .game .score .stars{ font-size:20px; color:var(--gold); letter-spacing:2px; margin:2px 0 1px; }
  .game .score .stars .off{ color:var(--ink-soft); opacity:.45; }
  .game .score .rank{ font-weight:700; } .game .score .best{ color:var(--ink-soft); font-size:11px; }
  .game .score .lore{ font-size:11px; line-height:1.55; color:var(--ink-soft); margin-top:4px; white-space:pre-wrap; }
  #ghosts{ pointer-events:none; }
  .city .dot{ transition:r .15s; } .city:hover .dot{ r:6.5; }
  /* 강조·페이드·경로·출발표식은 '순행 그리기'(svg.draw)에서만. 탐험 모드는 깨끗한 지도. */
  svg.map.draw .city.dim{ opacity:.30; }
  svg.map.draw .city.dim .lbl, svg.map.draw .city.dim:hover .lbl{ opacity:0; }
  svg.map:not(.draw) .selring, svg.map:not(.draw) .startmark{ display:none; }
  svg.map:not(.draw) #player, svg.map:not(.draw) #answer{ display:none; }
  .city .lbl{ opacity:0; transition:opacity .12s; } .city:hover .lbl{ opacity:1; }
  .city text, #ghosts text{ pointer-events:none; paint-order:stroke; stroke:var(--parchment); stroke-width:3px; stroke-linejoin:round; }
</style></head><body><div class="map-wrap">
  <div class="panel game" id="game">
    <div class="hd"><span class="ttl">직접 순행해 보세요</span><button class="col" id="collapse" title="접기/펼치기">▾</button></div>
    <div class="body" id="gbody">
      <div class="khan" id="khan"><div class="kh">칸의 명</div><div class="kc" id="khanc"></div></div>
      <div class="prog" id="prog">출발지에서 시작해 순서대로 클릭</div>
      <div class="btns"><button class="primary" id="grade">채점</button><button id="reset">다시</button></div>
      <div class="score" id="score"></div>
    </div>
  </div>
  <div class="panel zoom">
    <button id="zin" aria-label="확대">+</button><button id="zout" aria-label="축소">&minus;</button>
    <button id="zrst" class="rst" aria-label="처음으로">처음</button>
  </div>
  <div class="panel viz" id="viz">
    <button id="vCart" title="중심(대도)에서의 이동 비용을 거리로 환산해 지도를 변형">비용 카토그램</button>
    <button id="vHeat" title="산맥·사막·고원의 이동 난이도를 옅은 음영으로">난이도 음영</button>
    <button id="vZone" title="대도에서의 이동 비용대(帶)를 점에서 유도한 부드러운 영향권으로">영향권</button>
  </div>
  <div class="panel mode" id="mode">
    <button id="mExplore" class="on" title="도시를 눌러 역사 설명 보기">탐험</button><button id="mDraw" title="강조된 도시를 순서대로 눌러 순행로 작성">순행 그리기</button>
  </div>
  <button class="pediaBtn" id="pediaBtn" title="백과사전">&#128214;</button>
  <div class="panel pedia" id="pedia">
    <div class="pHd"><b id="pTitle">백과사전</b><button class="pX" id="pX" title="닫기">&#10005;</button></div>
    <div class="pBody" id="pBody"></div>
  </div>
  <svg class="map" id="map" viewBox="0 0 1280 780" role="img" aria-label="칸이 명한 순행로 지도" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker>
      <radialGradient id="vig" cx="50%" cy="47%" r="72%"><stop offset="55%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#3a2f1c" stop-opacity="0.36"/></radialGradient>
      <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>
      <radialGradient id="heatG"><stop offset="0%" stop-color="#7a5a30" stop-opacity="0.42"/><stop offset="100%" stop-color="#7a5a30" stop-opacity="0"/></radialGradient>
      <radialGradient id="zoneA"><stop offset="0%" stop-color="#3f7a4f" stop-opacity="0.22"/><stop offset="100%" stop-color="#3f7a4f" stop-opacity="0"/></radialGradient>
      <radialGradient id="zoneB"><stop offset="0%" stop-color="#b0992c" stop-opacity="0.22"/><stop offset="100%" stop-color="#b0992c" stop-opacity="0"/></radialGradient>
      <radialGradient id="zoneC"><stop offset="0%" stop-color="#c0772a" stop-opacity="0.22"/><stop offset="100%" stop-color="#c0772a" stop-opacity="0"/></radialGradient>
      <radialGradient id="zoneD"><stop offset="0%" stop-color="#8a3d2a" stop-opacity="0.24"/><stop offset="100%" stop-color="#8a3d2a" stop-opacity="0"/></radialGradient>
      <clipPath id="mapclip"><rect x="38" y="106" width="1204" height="602"/></clipPath>
    </defs>
    <rect x="0" y="0" width="1280" height="780" fill="var(--parchment)"/>
    <rect x="0" y="0" width="1280" height="780" fill="var(--parchment-edge)" filter="url(#grain)" opacity="0.06"/>
    <rect x="0" y="0" width="1280" height="780" fill="url(#vig)"/>
    <g clip-path="url(#mapclip)"><g id="viewport">
      <g id="geo"></g><g id="zones"></g><g id="terrain"></g><g id="answer"></g><g id="player"></g><g id="cities"></g><g id="ghosts"></g>
    </g></g>
    <rect x="24" y="24" width="1232" height="732" fill="none" stroke="var(--ink-soft)" stroke-width="2.5"/>
    <rect x="30" y="30" width="1220" height="720" fill="none" stroke="var(--ink-soft)" stroke-width="0.8"/>
    <text x="640" y="72" text-anchor="middle" style="font-size:25px;font-weight:700;fill:var(--ink);letter-spacing:3px">칸이 명한 순행로</text>
    <line x1="540" y1="84" x2="740" y2="84" stroke="var(--ink-soft)" stroke-width="0.8"/>
    <text x="640" y="100" text-anchor="middle" style="font-size:12px;fill:var(--ink-soft);letter-spacing:7px">몽 골 제 국</text>
    <g transform="translate(110,690)" opacity="0.85">
      <circle r="22" fill="var(--parchment)" stroke="var(--ink-soft)" stroke-width="1"/>
      <polygon points="0,-22 4.5,0 0,7 -4.5,0" fill="var(--route)"/><polygon points="0,22 4.5,0 0,-7 -4.5,0" fill="var(--ink-soft)"/>
      <text x="0" y="-27" text-anchor="middle" style="font-size:11px;fill:var(--ink-soft)">북</text></g>
  </svg></div>
<script>
  var CITIES=%%CITIES%%, GHOSTS=%%GHOSTS%%, SELECTED=%%SELECTED%%, START=%%START%%, ANSWER=%%ANSWER%%;
  var TERRAIN=%%TERRAIN%%, COSTS=%%COSTS%%, BARRIERS=%%BARRIERS%%, CR=%%CR%%, CARTCENTER=%%CARTCENTER%%, GEO=%%GEO%%, INFO=%%INFO%%, PEDIA=%%PEDIA%%, PATHS=%%PATHS%%, FORCEMODE=%%FORCEMODE%%, METRICS=%%METRICS%%, ORBIS=%%ORBIS%%, SCENARIO=%%SCENARIO%%;
  var NS="http://www.w3.org/2000/svg";
  function el(t,a){var e=document.createElementNS(NS,t);for(var k in a)e.setAttribute(k,a[k]);return e;}
  var byName={}; CITIES.forEach(function(c){byName[c.n]=c;});

  // ---- 실제 지리 베이스맵(양피지 화풍): 바다 바탕 + 육지(양피지) + 호수 + 강. 최하단 레이어. ----
  (function(){ var gg=document.getElementById("geo"); if(!gg||!GEO||!GEO.land) return;
    gg.appendChild(el("rect",{x:"38",y:"106",width:"1204",height:"602",fill:"var(--sea)",opacity:"0.55"}));
    (GEO.land||[]).forEach(function(d){ gg.appendChild(el("path",{d:d,fill:"var(--parchment)",stroke:"var(--ink-soft)","stroke-width":"0.8","stroke-linejoin":"round","stroke-linecap":"round"})); });
    (GEO.lakes||[]).forEach(function(d){ gg.appendChild(el("path",{d:d,fill:"var(--sea)","fill-opacity":"0.85",stroke:"#6f8c88","stroke-width":"0.5"})); });
    (GEO.rivers||[]).forEach(function(d){ gg.appendChild(el("path",{d:d,fill:"none",stroke:"#7f9a96","stroke-width":"0.7","stroke-linejoin":"round","stroke-linecap":"round",opacity:"0.65"})); });
    // 역참(yam) 본선 — 옅은 금색 점선(옛 역참로). 엘치는 이 길 위에서만 압도적으로 빠르다.
    (GEO.yampaths||[]).forEach(function(d){ gg.appendChild(el("path",{d:d,fill:"none",stroke:"var(--gold)","stroke-width":"1.0","stroke-dasharray":"4 4","stroke-linejoin":"round","stroke-linecap":"round",opacity:"0.45"})); });
  })();

  // ---- 백과사전 시스템 (우상단 팝업: 색인 + 본문). 일반 항목=PEDIA, 도시 항목=INFO 자동. ----
  (function(){
    var btn=document.getElementById("pediaBtn"), pop=document.getElementById("pedia"), body=document.getElementById("pBody");
    function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
    function index(){
      var h="";
      (PEDIA.sections||[]).forEach(function(s){ h+='<div class="sec">'+esc(s.title)+'</div>';
        (s.entries||[]).forEach(function(e,i){ h+='<div class="ent" data-k="g|'+i+'|'+s.title+'">'+esc(e.title)+'</div>'; }); });
      var byReg={}, order=[]; for(var n in INFO){ if(n.charAt(0)==="_")continue; var r=(INFO[n]||{}).region||"기타";
        if(!byReg[r]){byReg[r]=[];order.push(r);} byReg[r].push(n); }
      h+='<div class="sec">도시</div>';
      order.forEach(function(r){ h+='<div class="subsec">'+esc(r)+'</div>';
        byReg[r].forEach(function(n){ h+='<div class="ent" data-k="c|'+n+'">'+esc(n)+'</div>'; }); });
      body.className="pBody"; body.innerHTML=h;
      [].forEach.call(body.querySelectorAll(".ent"),function(el){ el.onclick=function(){ openKey(el.getAttribute("data-k")); }; });
    }
    function article(title,sub,bd){ body.className="pBody";
      body.innerHTML='<span class="back">&#8249; 목록</span><div class="anm">'+esc(title)+'</div>'+
        (sub?'<div class="arg">'+esc(sub)+'</div>':'')+'<div class="abd">'+esc(bd)+'</div>';
      body.querySelector(".back").onclick=index; }
    function openKey(k){ var p=k.split("|");
      if(p[0]==="c"){ var i=INFO[p[1]]; if(i) article(p[1],i.region,i.desc); }
      else { var st=p.slice(2).join("|"), idx=+p[1], sec=(PEDIA.sections||[]).filter(function(s){return s.title===st;})[0];
        if(sec&&sec.entries[idx]) article(sec.entries[idx].title, sec.title, sec.entries[idx].body); } }
    window.__openCity=function(n){ pop.classList.add("show"); var i=INFO[n]; if(i) article(n,i.region,i.desc); else index(); };
    btn.onclick=function(){ if(pop.classList.contains("show")) pop.classList.remove("show"); else { index(); pop.classList.add("show"); } };
    document.getElementById("pX").onclick=function(){ pop.classList.remove("show"); };
  })();

  // ---- 모드(탐험 / 순행 그리기): 탐험은 깨끗한 지도(강조·페이드·패널 없음) ----
  var viewMode="explore";
  (function(){var ex=document.getElementById("mExplore"), dw=document.getElementById("mDraw"),
       svg=document.getElementById("map"), game=document.getElementById("game"), pop=document.getElementById("pedia");
    window.__setMode=function(m){ viewMode=m;
      ex.classList.toggle("on",m==="explore"); dw.classList.toggle("on",m==="draw");
      svg.classList.toggle("draw",m==="draw");
      game.classList.toggle("show", m==="draw" && SELECTED.length>=2);
      if(m==="draw") pop.classList.remove("show");
      try{ localStorage.setItem("mongolMode", m); }catch(e){} };   // 리런 넘어 모드 보존
    ex.onclick=function(){__setMode("explore");}; dw.onclick=function(){__setMode("draw");};
    var saved="explore"; try{ saved=localStorage.getItem("mongolMode")||"explore"; }catch(e){}
    if(FORCEMODE) saved=FORCEMODE;   // Python이 강제한 모드(무작위 뽑기 직후 등) 우선
    if(SCENARIO) saved="draw";       // 시나리오(순행 임무)는 항상 순행 그리기로 시작
    // 시나리오면 '칸의 명' 카드 표시 + 게임 패널 제목을 임무명으로
    if(SCENARIO){ var kc=SCENARIO.khan_command||""; if(kc){ document.getElementById("khanc").textContent=kc;
        document.getElementById("khan").classList.add("show"); }
      if(SCENARIO.title){ var tl=document.querySelector("#game .ttl"); if(tl) tl.textContent=SCENARIO.title; } }
    __setMode(saved); })();
  var LB="paint-order:stroke;stroke:var(--parchment);stroke-width:3px;stroke-linejoin:round;";
  var selSet={}; SELECTED.forEach(function(n){selSet[n]=true;});
  function legCost(n1,n2){ if(TERRAIN&&COSTS[n1]&&COSTS[n1][n2]!=null) return COSTS[n1][n2];
    var a=byName[n1],b=byName[n2]; return Math.hypot(a.x-b.x,a.y-b.y); }
  function tourLen(names){var L=0,m=names.length; for(var i=0;i<m;i++){L+=legCost(names[i],names[(i+1)%m]);} return L;}
  // 지형비용 켜짐: 간선을 비용/거리 비율로 색칠(청록=쉬움 → 주황=비쌈). 컴퓨터 답(붉은 점선)과 구분됨.
  function legColor(n1,n2){ if(!TERRAIN) return "var(--player)";
    // 거리 우회 비율(경로km/직선km, 지표 무관): 1=직선(청록) → 2배 우회(주황). 험지일수록 우회·주황.
    var a=byName[n1],b=byName[n2]; var dist=Math.hypot(a.x-b.x,a.y-b.y)||1; var ratio=1.6;
    if(ORBIS&&METRICS){ var m=METRICS[[n1,n2].sort().join("|")]; if(m){ ratio=m[0]/((dist*ORBIS.pxkm)||1); } }
    var t=Math.max(0,Math.min(1,(ratio-1)/1.0));
    var c0=[47,111,122], c1=[224,138,30];
    return "rgb("+Math.round(c0[0]+(c1[0]-c0[0])*t)+","+Math.round(c0[1]+(c1[1]-c0[1])*t)+","+Math.round(c0[2]+(c1[2]-c0[2])*t)+")"; }
  // 두 도시 사이 곡선 최소비용 경로(a→b 방향 정렬). 카토그램 중엔 null(직선 폴백).
  function legPath(a,b){ if(cartT>0||!PATHS) return null; var p=PATHS[[a,b].sort().join("|")]; if(!p||p.length<2) return null;
    var pa=byName[a], e0=Math.abs(p[0][0]-pa.x)+Math.abs(p[0][1]-pa.y), e1=Math.abs(p[p.length-1][0]-pa.x)+Math.abs(p[p.length-1][1]-pa.y);
    return e0<=e1 ? p : p.slice().reverse(); }

  // ---- 비용 카토그램 상태: 중심(대도)에서의 이동 비용을 반경으로(각도 보존, ORBIS식) ----
  // cartT∈[0,1] 보간 진행도. drawPlayer가 초기에 호출되므로 여기서 먼저 초기화.
  var origPos={}, warp={}, cartT=0, cartOn=false, answerShown=false;
  CITIES.forEach(function(c){origPos[c.n]={x:c.x,y:c.y};});
  GHOSTS.forEach(function(c){origPos[c.n]={x:c.x,y:c.y};});
  function pos(n){ var o=origPos[n]||byName[n]; if(cartT<=0||!warp[n]) return o; var w=warp[n];
    return {x:o.x+(w.x-o.x)*cartT, y:o.y+(w.y-o.y)*cartT}; }
  (function(){ if(!TERRAIN||!CARTCENTER) return; var ctr=byName[CARTCENTER]; if(!ctr) return;
    // 반경 = 비용/평균비용배율 → 평균보다 험한(산 너머) 도시는 밖으로, 쉬운 도시는 안으로.
    var num=0,den=0; CITIES.forEach(function(c){ var r0=Math.hypot(c.x-ctr.x,c.y-ctr.y), cr=CR[c.n];
      if(r0>1 && cr!=null){ num+=cr/r0; den++; } });
    var scale=(den?num/den:1)/0.85;  // 0.85: 살짝 축소해 화면(클립) 안에 들어오게
    function cl(v,a,b){return Math.max(a,Math.min(b,v));}
    CITIES.concat(GHOSTS).forEach(function(c){ var cr=CR[c.n];
      if(cr==null){ warp[c.n]={x:c.x,y:c.y}; return; }
      var dx=c.x-ctr.x, dy=c.y-ctr.y, r0=Math.hypot(dx,dy);
      if(r0<1e-6){ warp[c.n]={x:ctr.x,y:ctr.y}; return; }
      var r1=cr/scale;
      warp[c.n]={x:cl(ctr.x+dx/r0*r1,44,1236), y:cl(ctr.y+dy/r0*r1,112,702)}; }); })();

  // 도시
  var cg=document.getElementById("cities"), groups={};
  CITIES.forEach(function(c){
    var g=el("g",{class:"city"+(selSet[c.n]?" sel":(SELECTED.length?" dim":""))}); groups[c.n]=g;
    g.appendChild(el("circle",{cx:c.x,cy:c.y,r:"13",fill:"transparent"}));
    if(selSet[c.n]) g.appendChild(el("circle",{cx:c.x,cy:c.y,r:"9",fill:"none",stroke:"var(--gold)","stroke-width":"2",class:"selring"}));
    if(c.C){
      g.appendChild(el("polygon",{points:c.x+","+(c.y-9)+" "+(c.x+9)+","+c.y+" "+c.x+","+(c.y+9)+" "+(c.x-9)+","+c.y,fill:"var(--gold)",stroke:"#7a531a","stroke-width":"1",class:"dot"}));
      var lc=el("text",{x:c.x,y:c.y+24,"text-anchor":"middle",style:"font-size:15px;font-weight:700;fill:var(--ink);"+LB});lc.textContent=c.n;g.appendChild(lc);
    }else{
      g.appendChild(el("circle",{cx:c.x,cy:c.y,r:"4",fill:"var(--ink)",class:"dot"}));
      var l=el("text",{x:c.x+8,y:c.y+4,class:(c.M?"lblOn":"lbl"),style:"font-size:12.5px;fill:var(--ink);"+LB});l.textContent=c.n;g.appendChild(l);
    }
    g.addEventListener("click",function(){ if(window.__moved) return;
      if(viewMode==="draw" && selSet[c.n]) pick(c.n); else __openCity(c.n); });
    cg.appendChild(g);
  });

  // 출발지 표식 (카토그램에서 함께 이동하도록 그룹으로)
  var startG=null;
  if(START&&byName[START]){var sc=byName[START];
    startG=el("g",{class:"startmark"});
    startG.appendChild(el("circle",{cx:sc.x,cy:sc.y,r:"4.5",fill:"var(--gold)"}));
    var stg=el("text",{x:sc.x,y:sc.y-15,"text-anchor":"middle",style:"font-size:11px;font-weight:700;fill:var(--gold);"+LB});stg.textContent="출발";startG.appendChild(stg);
    cg.appendChild(startG);}

  // 보이지 않는 도시 (카토그램용 per-ghost 그룹)
  var gh=document.getElementById("ghosts"), ghostGroups={};
  GHOSTS.forEach(function(c){
    var g=el("g",{}); ghostGroups[c.n]=g;
    g.appendChild(el("circle",{cx:c.x,cy:c.y,r:"6.5",fill:"none",stroke:"var(--ghost)","stroke-width":"0.8",opacity:"0.45"}));
    g.appendChild(el("circle",{cx:c.x,cy:c.y,r:"3.6",fill:"var(--ghost)"}));
    var t=el("text",{x:c.x,y:c.y-11,"text-anchor":"middle",style:"font-size:11.5px;font-style:italic;fill:var(--ghost);"+LB});t.textContent=c.n;g.appendChild(t);
    gh.appendChild(g);
  });

  // ---- 플레이 모드 ----
  var playerG=document.getElementById("player"), answerG=document.getElementById("answer");
  var picked=[];
  var gamePanel=document.getElementById("game"), prog=document.getElementById("prog"), scoreEl=document.getElementById("score");
  if(START&&selSet[START]) picked.push(START);
  drawPlayer();
  prog.textContent = picked.length ? ("출발지("+START+")에서 시작 — 다음 도시 클릭") : "강조된 도시를 순서대로 클릭";

  function pick(name){
    if(picked.indexOf(name)>=0) return;
    picked.push(name); drawPlayer();
    prog.textContent="내 순행 "+picked.length+" / "+SELECTED.length+(picked.length===SELECTED.length?" — 채점하세요":"");
  }
  function drawPlayer(){
    playerG.innerHTML="";
    var seq=picked.slice();
    if(picked.length===SELECTED.length && picked.length>=2) seq.push(picked[0]); // 닫힌 순회
    if(seq.length>=2){
      if(TERRAIN){ // 간선별 비용 색 + 지형 따라 굽는 곡선
        for(var s=0;s<seq.length-1;s++){ var col=legColor(seq[s],seq[s+1]), cp=legPath(seq[s],seq[s+1]);
          if(cp){ playerG.appendChild(el("polyline",{points:cp.map(function(q){return q[0]+","+q[1];}).join(" "),fill:"none",stroke:col,"stroke-width":"2.8","stroke-linejoin":"round","stroke-linecap":"round",opacity:"0.92"})); }
          else { var a=pos(seq[s]),b=pos(seq[s+1]); playerG.appendChild(el("line",{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:col,"stroke-width":"2.8","stroke-linecap":"round",opacity:"0.92"})); } }
      }else{
        var pts=seq.map(function(n){var p=pos(n);return p.x+","+p.y;});
        playerG.appendChild(el("polyline",{points:pts.join(" "),fill:"none",stroke:"var(--player)","stroke-width":"2.4","stroke-linejoin":"round",opacity:"0.9"}));
      }
    }
    picked.forEach(function(n,i){var c=pos(n);
      playerG.appendChild(el("circle",{cx:c.x,cy:c.y,r:"9",fill:"var(--player)",opacity:"0.92"}));
      var t=el("text",{x:c.x,y:c.y+3.5,"text-anchor":"middle",style:"font-size:11px;font-weight:700;fill:#f3ece0"});t.textContent=(i+1);playerG.appendChild(t);
    });
  }
  function reveal(){
    answerG.innerHTML="";
    var r=ANSWER.route;
    if(!r||r.length<2){ answerShown=false; return; }
    answerShown=true;
    var loop=r.concat([r[0]]), pts=[];
    for(var i=0;i<loop.length-1;i++){ var a=loop[i],b=loop[i+1], cp=legPath(a,b);
      var seg = cp ? cp.slice() : [[pos(a).x,pos(a).y],[pos(b).x,pos(b).y]];
      if(i>0) seg=seg.slice(1);   // 이전 구간 끝점과 중복 제거
      seg.forEach(function(q){ pts.push(q[0]+","+q[1]); }); }
    answerG.appendChild(el("polyline",{points:pts.join(" "),fill:"none",stroke:"var(--route)","stroke-width":"2.4","stroke-dasharray":"7 5",opacity:"0.85","marker-end":"url(#arrow)"}));
  }
  function mkey(a,b){ return [a,b].sort().join("|"); }
  // 시나리오 별점: gap%(내 결과 vs 최적)를 임계 [a,b,c]에 매핑. 작을수록 좋음. gap<0(추월)=3★.
  function starsFor(gap, th){ return gap<=th[0]?3:(gap<=th[1]?2:(gap<=th[2]?1:0)); }
  var RANKS=["재순행하라","칸의 명을 받들었다","무난한 순행","칸의 칭송"]; // index=별 개수
  document.getElementById("grade").onclick=function(){
    if(picked.length<SELECTED.length){ prog.textContent="모든 도시를 방문하세요 ("+picked.length+"/"+SELECTED.length+")"; return; }
    reveal();
    var loop=picked.concat([picked[0]]), mine=0, html="", gap=null;
    var orb = TERRAIN && ORBIS && Object.keys(METRICS).length;
    if(orb){
      // ORBIS 3지표 결과표: 거리·시간·비용. 최적화 지표(우선순위) 열 강조.
      var hi = (ORBIS.priority==="최단")?0:(ORBIS.priority==="최속")?1:2;  // [km,일,관]
      html += "<div class='ohead'>"+ORBIS.mode+" · "+ORBIS.priority+" · "+ORBIS.season+"</div>";
      var tk=0,td=0,tc=0,rows="";
      function hc(k){ return "c"+(hi===k?" hl":""); }
      for(var i=0;i<loop.length-1;i++){ var a=loop[i],b=loop[i+1], m=METRICS[mkey(a,b)]||[0,0,0];
        tk+=m[0]; td+=m[1]; tc+=m[2];
        rows+="<tr><td>"+(i+1)+"</td><td>"+a+"→"+b+"</td><td class='"+hc(0)+"'>"+Math.round(m[0]).toLocaleString()+"</td><td class='"+hc(1)+"'>"+(+m[1]).toFixed(1)+"</td><td class='"+hc(2)+"'>"+Math.round(m[2]).toLocaleString()+"</td></tr>"; }
      html += "<table class='legs'><tr><th>#</th><th>구간</th><th class='"+hc(0)+"'>거리</th><th class='"+hc(1)+"'>일</th><th class='"+hc(2)+"'>관</th></tr>"+rows+
        "<tr class='tot'><td></td><td>합계</td><td class='c'>"+Math.round(tk).toLocaleString()+"</td><td class='c'>"+td.toFixed(1)+"</td><td class='c'>"+Math.round(tc).toLocaleString()+"</td></tr></table>";
      mine = (hi===0?tk:hi===1?td:tc);   // 최적화 지표로 비교
    } else {
      var rs="";
      for(var i=0;i<loop.length-1;i++){ var a=loop[i],b=loop[i+1], c=legCost(a,b); mine+=c;
        rs+="<tr><td>"+(i+1)+"</td><td>"+a+"→"+b+"</td><td class='c'>"+Math.round(c).toLocaleString()+"</td></tr>"; }
      html += "<table class='legs'><tr><th>#</th><th>구간</th><th class='c'>거리</th></tr>"+rs+
        "<tr class='tot'><td></td><td>합계</td><td class='c'>"+Math.round(mine).toLocaleString()+"</td></tr></table>";
    }
    if(ANSWER.route&&ANSWER.route.length){
      var opt=ANSWER.len||tourLen(ANSWER.route), u=orb?(" "+ORBIS.unit):"";
      gap=(mine-opt)/(opt||1)*100;
      html+="<div class='cmp'>컴퓨터("+(ANSWER.label||"해법")+"): <span class='opt'>"+Math.round(opt).toLocaleString()+u+"</span> — ";
      if(Math.abs(gap)<1.0) html+="최적과 동일! 👏";
      else if(gap>0) html+="최적보다 <b>+"+gap.toFixed(1)+"%</b> 더 듦";
      else html+="컴퓨터보다 <b>"+(-gap).toFixed(1)+"%</b> 더 적음! 🏆";
      html+="</div>";
    } else {
      html+="<div style='color:var(--ink-soft)'>도시를 2개 이상 고르면 컴퓨터 해답과 자동 비교됩니다.</div>";
    }
    // 시나리오(순행 임무): gap%로 별점 + 등급 + lore + 최고기록(localStorage). 시나리오 없으면 건너뜀(회귀).
    if(SCENARIO && gap!=null){
      var th=SCENARIO.stars||[5,15,30], s=starsFor(gap, th);
      var glyph=""; for(var k=0;k<3;k++) glyph += (k<s?"<span>★</span>":"<span class='off'>★</span>");
      var key="mongolScen:"+(SCENARIO.id||SCENARIO.title), best=s, bestHtml="";
      try{ var pv=parseInt(localStorage.getItem(key)); if(!isNaN(pv)) best=Math.max(best,pv);
           localStorage.setItem(key, String(best)); }catch(e){}
      if(best>s) bestHtml="<span class='best'> (최고 "+best+"★)</span>";
      var top="<div class='stars'>"+glyph+"</div><div class='rank'>"+RANKS[s]+bestHtml+"</div>";
      if(s>0 && SCENARIO.lore) top+="<div class='lore'>"+SCENARIO.lore+"</div>";
      html = top + html;
    }
    scoreEl.innerHTML=html; scoreEl.classList.add("show");
  };
  document.getElementById("reset").onclick=function(){
    picked = (START&&selSet[START])?[START]:[]; answerShown=false; drawPlayer(); answerG.innerHTML=""; scoreEl.classList.remove("show");
    prog.textContent = picked.length ? ("출발지("+START+")에서 시작 — 다음 도시 클릭") : "강조된 도시를 순서대로 클릭";
  };
  document.getElementById("collapse").onclick=function(){var g=document.getElementById("game");
    g.classList.toggle("collapsed"); this.textContent=g.classList.contains("collapsed")?"▸":"▾";};

  // ---- 비용 카토그램: 중심(대도)에서의 비용을 반경으로 지도를 변형(각도 보존) ----
  if(TERRAIN) document.getElementById("viz").classList.add("show");
  function applyCart(){
    var n,o,p;
    for(n in groups){ o=origPos[n]; p=pos(n); groups[n].setAttribute("transform","translate("+(p.x-o.x)+","+(p.y-o.y)+")"); }
    for(n in ghostGroups){ o=origPos[n]; p=pos(n); ghostGroups[n].setAttribute("transform","translate("+(p.x-o.x)+","+(p.y-o.y)+")"); }
    if(startG&&origPos[START]){ o=origPos[START]; p=pos(START); startG.setAttribute("transform","translate("+(p.x-o.x)+","+(p.y-o.y)+")"); }
    drawPlayer(); if(answerShown) reveal();
  }
  function animateCart(on){ cartOn=on; var from=cartT, to=on?1:0, t0=null, dur=600;
    function step(ts){ if(t0==null)t0=ts; var k=Math.min(1,(ts-t0)/dur), e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;
      cartT=from+(to-from)*e; applyCart(); if(k<1) requestAnimationFrame(step); }
    requestAnimationFrame(step);
  }
  (function(){var b=document.getElementById("vCart"); if(!b) return;
    b.onclick=function(){ var on=!cartOn; animateCart(on); b.classList.toggle("on",on); };})();

  // ---- 난이도 음영(명명된 장애) + 소프트 영향권(대도서 비용대) — 둘 다 기본 숨김, 토글 ----
  (function(){
    var terr=document.getElementById("terrain"), zones=document.getElementById("zones");
    terr.style.display="none"; zones.style.display="none";
    if(GEO.heat){  // 실제 DEM 난이도(경사+고도+사막)를 옅은 갈색 heat 이미지로
      var h=GEO.heat, bin=atob(h.b64), cv=document.createElement("canvas"); cv.width=h.w; cv.height=h.h;
      var ctx=cv.getContext("2d"), im2=ctx.createImageData(h.w,h.h);
      for(var p=0;p<h.w*h.h;p++){ var v=bin.charCodeAt(p)/255;
        im2.data[p*4]=120; im2.data[p*4+1]=80; im2.data[p*4+2]=45; im2.data[p*4+3]=Math.pow(v,1.4)*125; }
      ctx.putImageData(im2,0,0);
      var hi=el("image",{x:h.x0,y:h.y0,width:h.x1-h.x0,height:h.y1-h.y0,preserveAspectRatio:"none",opacity:"0.8"});
      hi.setAttribute("href",cv.toDataURL()); terr.appendChild(hi);
    }
    var vals=[]; for(var key in CR) vals.push(CR[key]);
    if(vals.length){ var lo=Math.min.apply(null,vals), span=(Math.max.apply(null,vals)-lo)||1;
      var gid=["url(#zoneA)","url(#zoneB)","url(#zoneC)","url(#zoneD)"];
      CITIES.forEach(function(c){ var cr=CR[c.n]; if(cr==null) return;
        var band=Math.min(3,Math.floor((cr-lo)/span*4));
        zones.appendChild(el("circle",{cx:c.x,cy:c.y,r:"54",fill:gid[band]})); }); }
    function tog(btn,g){ if(!btn) return; btn.onclick=function(){
      var on=g.style.display!=="block"; g.style.display=on?"block":"none"; btn.classList.toggle("on",on); }; }
    tog(document.getElementById("vHeat"),terr);
    tog(document.getElementById("vZone"),zones);
  })();

  // ---- 줌 / 팬 (클릭과 분리: 이동 임계값) ----
  (function(){var svg=document.getElementById("map"),vp=document.getElementById("viewport");
    var scale=1,tx=0,ty=0,MINS=1,MAXS=8;
    function clamp(v,a,b){return Math.max(a,Math.min(b,v));}
    function apply(){var W0=38,W1=1242,H0=106,H1=708;
      tx=clamp(tx,W1*(1-scale),W0*(1-scale));ty=clamp(ty,H1*(1-scale),H0*(1-scale));
      vp.setAttribute("transform","translate("+tx+","+ty+") scale("+scale+")");}
    function pt(e){var p=svg.createSVGPoint();p.x=e.clientX;p.y=e.clientY;return p.matrixTransform(svg.getScreenCTM().inverse());}
    function zoomAt(sx,sy,f){var ns=Math.min(MAXS,Math.max(MINS,scale*f)),af=ns/scale;tx=sx-(sx-tx)*af;ty=sy-(sy-ty)*af;scale=ns;apply();}
    svg.addEventListener("wheel",function(e){e.preventDefault();var p=pt(e);zoomAt(p.x,p.y,e.deltaY<0?1.12:1/1.12);},{passive:false});
    var drag=false,last=null,sxy=null; window.__moved=false;
    svg.addEventListener("pointerdown",function(e){drag=true;window.__moved=false;last=pt(e);sxy=[e.clientX,e.clientY];svg.classList.add("drag");});
    window.addEventListener("pointermove",function(e){if(!drag)return;
      if(Math.abs(e.clientX-sxy[0])+Math.abs(e.clientY-sxy[1])>4) window.__moved=true;
      var p=pt(e);tx+=p.x-last.x;ty+=p.y-last.y;last=p;apply();});
    window.addEventListener("pointerup",function(){drag=false;svg.classList.remove("drag");});
    document.getElementById("zin").onclick=function(){zoomAt(640,407,1.25);};
    document.getElementById("zout").onclick=function(){zoomAt(640,407,1/1.25);};
    document.getElementById("zrst").onclick=function(){scale=1;tx=0;ty=0;apply();};})();
</script></body></html>"""
