# -*- coding: utf-8 -*-
"""SVG 고지도 HTML 생성 + 플레이 모드(직접 경로 그리고 채점).
경로 비교 답안(answer)은 Python(solver)이 계산해 주입한다. 단방향 흐름."""
import json


def build_map(cities, ghosts, selected, answer, start=None, show_ghosts=False,
              terrain=False, costs=None, barriers=None, cr=None, cart_center=None, geo=None, info=None, pedia=None, paths=None,
              force_mode=None, metrics=None, orbis=None, scenario=None, city_scenes=None, opening_map=None, story=None, sounds=None,
              relay_terr=None):
    return (TEMPLATE
            .replace("%%RELAYTERR%%", json.dumps(relay_terr or None, ensure_ascii=False))
            .replace("%%SOUNDS%%", json.dumps(sounds or {}, ensure_ascii=False))
            .replace("%%STORY%%", json.dumps(story or None, ensure_ascii=False))
            .replace("%%OPENMAP%%", json.dumps(opening_map or {}, ensure_ascii=False))
            .replace("%%CITYSCENES%%", json.dumps(city_scenes or {}, ensure_ascii=False))
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
  .zoom button{ width:34px; height:34px; border:1px solid var(--ink-soft); background:rgba(255,255,255,.3);
    color:var(--ink); font-family:"Noto Serif KR",serif; font-size:18px; border-radius:4px; cursor:pointer; line-height:1; }
  .zoom button:hover{ background:rgba(255,255,255,.6); } .zoom button.rst{ font-size:12px; }
  .viz{ right:16px; top:58px; display:none; flex-direction:column; padding:5px; gap:5px; z-index:5; }
  .viz.show{ display:flex; }
  .viz button{ width:112px; height:31px; border:1px solid var(--ink-soft); background:rgba(255,255,255,.3);
    color:var(--ink); font-family:"Noto Serif KR",serif; font-size:12.5px; border-radius:4px; cursor:pointer; line-height:1; }
  .viz button.on{ background:var(--player); color:#f3ece0; border-color:var(--player); }
  .mode{ left:50%; transform:translateX(-50%); top:14px; display:flex; padding:3px; gap:0; z-index:6; }
  .mode button{ border:1px solid var(--ink-soft); background:rgba(255,255,255,.35); color:var(--ink);
    font-family:"Noto Serif KR",serif; font-size:13px; padding:7px 16px; cursor:pointer; line-height:1; }
  .mode button:first-child{ border-radius:3px 0 0 3px; }
  .mode button:last-child{ border-radius:0 3px 3px 0; border-left:none; }
  .mode button.on{ background:var(--gold); color:#fff; border-color:var(--gold); }
  .pediaBtn{ position:absolute; right:16px; top:16px; width:40px; height:34px; z-index:7;
    border:1px solid var(--ink-soft); background:rgba(233,221,191,.94); border-radius:4px; cursor:pointer; font-size:17px; }
  .pediaBtn:hover{ background:rgba(233,221,191,1); }
  .sndBtn{ right:62px; width:36px; font-size:15px; }
  .pedia{ right:16px; top:16px; width:368px; max-height:calc(100% - 32px); z-index:7; display:none;
    flex-direction:column; padding:0; overflow:hidden; }
  .pedia.show{ display:flex; }
  .pedia .pHd{ display:flex; align-items:center; justify-content:space-between; padding:10px 13px;
    border-bottom:1px solid var(--ink-soft); background:rgba(216,200,160,.55); }
  .pedia .pHd b{ font-size:15px; } .pedia .pX{ border:none; background:none; cursor:pointer; font-size:15px; color:var(--ink-soft); }
  .pedia .pBody{ padding:10px 14px 15px; overflow:auto; }
  .pedia .sec{ font-weight:700; font-size:12.5px; color:var(--route); letter-spacing:2px; margin:12px 0 4px; }
  .pedia .subsec{ font-weight:700; font-size:11px; color:var(--ink-soft); margin:8px 0 2px; letter-spacing:1px; }
  .pedia .ent{ cursor:pointer; font-size:13.5px; padding:3px 0 3px 6px; color:var(--ink); }
  .pedia .ent:hover{ color:var(--player); }
  .pedia .back{ cursor:pointer; color:var(--ink-soft); font-size:12px; margin-bottom:8px; display:inline-block; }
  .pedia .anm{ font-weight:700; font-size:18px; } .pedia .arg{ color:var(--route); font-size:11.5px; margin:3px 0 10px; letter-spacing:1px; }
  .pedia .abd{ font-size:14px; line-height:1.75; white-space:pre-wrap; }
  .game{ left:50%; transform:translateX(-50%); bottom:14px; padding:10px 14px 12px; width:278px; z-index:5; font-size:13px; display:none; }
  .game.show{ display:block; }
  .game.collapsed .body{ display:none; }
  .game .hd{ display:flex; align-items:center; justify-content:space-between; }
  .game .col{ border:none; background:none; cursor:pointer; font-size:15px; color:var(--ink-soft); padding:0 2px; line-height:1; }
  .game .ttl{ font-weight:700; font-size:15px; }
  .game .prog{ color:var(--ink); margin-bottom:9px; font-size:12.5px; }
  .game .btns{ display:flex; gap:7px; }
  .game button{ flex:1; padding:7px 0; border:1px solid var(--ink-soft); background:rgba(255,255,255,.35);
    color:var(--ink); font-family:"Noto Serif KR",serif; font-size:13.5px; border-radius:4px; cursor:pointer; }
  .game button:hover{ background:rgba(255,255,255,.6); }
  .game button.primary{ background:var(--player); color:#f3ece0; border-color:var(--player); }
  .game button.primary:hover{ filter:brightness(1.08); }
  .game .score{ margin-top:9px; line-height:1.6; display:none; max-height:248px; overflow:auto; }
  .game .score.show{ display:block; }
  .game .score b{ color:var(--player); } .game .score .opt{ color:var(--route); font-weight:700; }
  .game .score table.legs{ width:100%; border-collapse:collapse; font-size:12px; }
  .game .score table.legs th{ text-align:left; color:var(--ink-soft); font-weight:700; border-bottom:1px solid var(--ink-soft); padding:2px 4px; }
  .game .score table.legs td{ padding:2px 3px; } .game .score table.legs td.c, .game .score table.legs th.c{ text-align:right; white-space:nowrap; }
  .game .score table.legs .hl{ color:var(--route); font-weight:700; }
  .game .score table.legs tr.tot td{ border-top:1px solid var(--ink-soft); }
  .game .score .ohead{ font-size:12px; color:var(--gold); font-weight:700; margin-bottom:4px; letter-spacing:1px; }
  .game .score .cmp{ margin-top:6px; }
  .game .khan{ display:none; margin-bottom:9px; padding:8px 10px; border:1px solid var(--gold);
    border-radius:4px; background:rgba(193,154,73,.12); }
  .game .khan.show{ display:block; }
  .game .khan .kh{ font-size:10.5px; color:var(--gold); font-weight:700; letter-spacing:2px; margin-bottom:3px; }
  .game .khan .kc{ font-size:12.5px; line-height:1.6; color:var(--ink); white-space:pre-wrap; }
  .game .score .stars{ font-size:22px; color:var(--gold); letter-spacing:2px; margin:3px 0 2px; }
  .game .score .stars .off{ color:var(--ink-soft); opacity:.45; }
  .game .score .rank{ font-weight:700; font-size:13.5px; } .game .score .best{ color:var(--ink-soft); font-size:11.5px; }
  .game .score .lore{ font-size:12px; line-height:1.6; color:var(--ink-soft); margin-top:5px; white-space:pre-wrap; }
  /* 2단계 역참로 미니게임: 전용 오버레이 스테이지(다수 후보 중 보급 4개 선택) */
  .game button.go{ width:100%; margin-top:8px; background:var(--gold); color:#fff; border-color:var(--gold); }
  .game button.go:disabled{ cursor:default; }
  .game.relaymode{ display:none; }
  #relaystage{ position:absolute; inset:0; z-index:9; display:none; flex-direction:column;
    background:radial-gradient(125% 95% at 50% 28%, #efe6ce, #e0d1a8); color:var(--ink); }
  #relaystage.show{ display:flex; }
  #relaystage .rsHd{ padding:12px 16px 5px; text-align:center; flex:0 0 auto; }
  #relaystage .rsTag{ font-size:11px; letter-spacing:5px; color:var(--gold); font-weight:700; }
  #relaystage .rsTtl{ font-size:21px; font-weight:700; margin-top:2px; }
  #relaystage .rsHint{ font-size:13px; color:var(--ink); margin-top:3px; }
  #relaystage .rsStage{ flex:1 1 auto; min-height:0; }
  #relaystage svg{ width:100%; height:100%; display:block; }
  #relaystage .st{ cursor:pointer; }
  #relaystage .rsFoot{ flex:0 0 auto; padding:9px 16px 13px; display:flex; gap:10px; align-items:center; justify-content:center; flex-wrap:wrap; }
  #relaystage .rsFoot button{ padding:8px 22px; border:1px solid var(--ink-soft); background:rgba(255,255,255,.45);
    color:var(--ink); font-family:"Noto Serif KR",serif; font-size:14px; border-radius:4px; cursor:pointer; }
  #relaystage .rsFoot button:hover{ background:rgba(255,255,255,.7); }
  #relaystage .rsFoot button.primary{ background:var(--gold); color:#fff; border-color:var(--gold); }
  #relaystage .rsFoot button:disabled{ opacity:.45; cursor:default; }
  #relaystage .rsRes{ font-size:13.5px; text-align:center; }
  #relaystage .rsRes .stars{ font-size:22px; color:var(--gold); letter-spacing:2px; line-height:1.2; }
  #relaystage .rsRes .stars .off{ color:var(--ink-soft); opacity:.4; }
  #relaystage .rsRes .warn{ color:var(--route); font-weight:700; }
  /* 역참로 튜토리얼(첫 구간 1회 + ? 버튼) — 비차단 하단 길잡이 카드 */
  #rsHelp{ position:absolute; right:14px; top:12px; z-index:13; width:26px; height:26px; border-radius:50%;
    border:1px solid var(--ink-soft); background:rgba(255,255,255,.55); color:var(--ink-soft); cursor:pointer;
    font-family:"Noto Serif KR",serif; font-size:14px; font-weight:700; line-height:1; }
  #rsHelp:hover{ background:rgba(255,255,255,.85); color:var(--ink); }
  #rsTut{ position:absolute; left:50%; bottom:62px; transform:translateX(-50%); width:min(560px,92%); z-index:12; display:none; }
  #rsTut.show{ display:block; animation:rsTutIn .25s ease; }
  @keyframes rsTutIn{ from{ opacity:0; transform:translate(-50%,8px);} to{ opacity:1; transform:translate(-50%,0);} }
  #rsTut .rsTutCard{ background:#f4ecd4; border:1px solid var(--gold); border-radius:9px; padding:12px 16px 11px; box-shadow:0 8px 24px rgba(40,28,12,.28); }
  #rsTut .rsTutTag{ font-size:10px; letter-spacing:4px; color:var(--gold); font-weight:700; margin-bottom:5px; }
  #rsTut .rsTutBody{ font-size:13.5px; line-height:1.72; color:var(--ink); }
  #rsTut .rsTutBody b{ color:var(--route); }
  #rsTut .rsTutFoot{ display:flex; align-items:center; gap:8px; margin-top:11px; }
  #rsTut .rsTutDots{ flex:1 1 auto; letter-spacing:3px; color:var(--ink-soft); font-size:12px; }
  #rsTut .rsTutFoot button{ padding:6px 16px; border:1px solid var(--ink-soft); background:rgba(255,255,255,.55);
    border-radius:5px; cursor:pointer; font-family:"Noto Serif KR",serif; font-size:12.5px; color:var(--ink); }
  #rsTut .rsTutFoot button:hover{ background:rgba(255,255,255,.85); }
  #rsTut .rsTutFoot button.primary{ background:var(--gold); color:#fff; border-color:var(--gold); }
  /* 도착 연출(스토리 모드): 역참 구간 사이에 도착 도시 풍경 장면 */
  #cityscene{ position:absolute; inset:0; z-index:10; display:none; align-items:center; justify-content:center;
    background:radial-gradient(130% 100% at 50% 35%, #efe6cd, #d9c79c); }
  #cityscene.show{ display:flex; }
  #cityscene .csInner{ width:min(88%,580px); max-height:94%; overflow:auto; text-align:center; padding:8px 4px; }
  #cityscene .csArt{ width:100%; height:150px; border:1px solid var(--ink-soft); border-radius:5px;
    background:repeating-linear-gradient(135deg,#cdbb92,#cdbb92 9px,#c6b389 9px,#c6b389 18px);
    background-size:cover; background-position:center; color:var(--ink-soft); font-size:12px; letter-spacing:4px;
    display:flex; align-items:center; justify-content:center; }
  #cityscene .csArt.hasimg{ color:transparent; border-color:var(--gold); }
  #cityscene .csTag{ margin-top:12px; font-size:11px; letter-spacing:5px; color:var(--gold); font-weight:700; }
  #cityscene .csTtl{ font-size:24px; font-weight:700; margin-top:3px; }
  #cityscene .csBody{ font-size:14.5px; line-height:1.8; color:var(--ink); margin:12px 4px 16px; white-space:pre-wrap; text-align:left; }
  #cityscene .csBody .csLine{ min-height:7px; }
  #cityscene .csGo{ padding:9px 26px; border:1px solid var(--gold); background:var(--gold); color:#fff;
    font-family:"Noto Serif KR",serif; font-size:14.5px; border-radius:4px; cursor:pointer; }
  #cityscene .csGo:hover{ filter:brightness(1.08); }
  /* 스토리 오프닝 시네마틱: 대도만 밝히고(스포트라이트), 리빌 시 나머지 노드는 자기 본래 불투명도로 복귀
     (도시 클래스별 opacity[sel=1·dim=.30]를 보존해야 하므로 일괄 페이드 대신 규칙 제거로 즉시 복귀) */
  svg.map.storyintro #cities .city:not(.startcity){ opacity:0; }
  svg.map.storyintro #ghosts, svg.map.storyintro #answer, svg.map.storyintro #player{ opacity:0; }
  /* 오프닝 시네마틱(스토리): 제노바→베네치아→대도 여정. 전용 SVG 카메라 + 하단 내레이션 카드. */
  /* 컴포넌트 iframe 전체(고정 높이)를 덮는다. map-wrap은 본 지도 비율따라 높이가 변해(짤림/여백) → viewport에 고정. */
  /* 타이틀(별자리)만 밤하늘(.night), 지도 전환 후엔 양피지/황토 배경(레터박스 하단이 검게 남던 문제 수정). */
  #opening{ position:fixed; inset:0; z-index:11; display:none; flex-direction:column; background:#d8c8a0; }
  #opening.show{ display:flex; }
  #opening .opMap{ flex:1 1 auto; min-height:0; }
  #opening .opMap svg{ width:100%; height:100%; display:block; }
  #opening .opCard{ flex:0 0 auto; padding:10px 18px 15px; text-align:center;
    background:#e9ddbf; border-top:1px solid rgba(70,56,39,.18); }   /* 단색(가독성) — 그라데이션 제거 */
  #opening .opTag{ font-size:11px; letter-spacing:4px; color:var(--gold); font-weight:700; }
  #opening .opTtl{ font-size:20px; font-weight:700; margin-top:2px; }
  #opening .opBody{ font-size:14px; line-height:1.72; color:var(--ink); margin:7px auto 12px; max-width:580px; text-align:left; white-space:pre-wrap; }
  #opening .opBody .opLine{ min-height:6px; }
  #opening .opGo{ padding:8px 26px; border:1px solid var(--gold); background:var(--gold); color:#fff;
    font-family:"Noto Serif KR",serif; font-size:14.5px; border-radius:4px; cursor:pointer; }
  #opening .opGo:hover{ filter:brightness(1.08); }
  /* 오프닝 내러티브 = 전면 낭독 뷰: 지도를 어둡게 깔고 중앙에 큰 본문+장 제목(긴 산문 몰입). 클릭 힌트는 하단 opCard. */
  #opRead{ position:absolute; inset:0; z-index:8; display:none; align-items:center; justify-content:center; padding:26px 20px;
    background:radial-gradient(125% 100% at 50% 42%, rgba(16,11,5,.5), rgba(8,6,3,.8)); }
  #opRead.show{ display:flex; animation:opReadIn .5s ease; }
  @keyframes opReadIn{ from{ opacity:0 } to{ opacity:1 } }
  #opRead .opReadInner{ width:min(690px,94%); max-height:90%; overflow:auto; text-align:center; }
  #opRead .opReadArt{ width:100%; height:148px; border:1px solid rgba(214,184,112,.45); border-radius:6px;
    background:#1a140c center/cover no-repeat; color:#9b8a66; display:flex; align-items:center; justify-content:center;
    font-size:12px; letter-spacing:6px; }
  #opRead .opReadArt.hasimg{ color:transparent; border-color:var(--gold); }
  #opRead .opReadTag{ margin-top:15px; font-size:11px; letter-spacing:6px; color:#d9b870; font-weight:700; }
  #opRead .opReadTtl{ font-size:27px; font-weight:700; color:#f1e6c8; margin-top:5px; letter-spacing:2px; text-shadow:0 1px 12px rgba(0,0,0,.55); }
  #opRead .opReadBody{ font-size:15.5px; line-height:1.95; color:#ece0c6; margin:16px 4px 20px; text-align:left; white-space:pre-wrap; }
  #opRead .opReadBody .opLine{ min-height:9px; }
  #opRead .opReadGo{ padding:9px 30px; border:1px solid var(--gold); background:var(--gold); color:#fff;
    font-family:"Noto Serif KR",serif; font-size:15px; border-radius:5px; cursor:pointer; }
  #opRead .opReadGo:hover{ filter:brightness(1.08); }
  /* 첫 화면 '별자리'(밤하늘): 노드만 빛나고 지도·라벨 숨김. opacity 전환은 JS가 inline으로 구동. */
  #opening.night{ cursor:default; background:#070b1c; }
  #opening.night .opCard{ background:#070b1c; padding-bottom:20px; }
  #opening.night .opTag{ font-size:12.5px; letter-spacing:6px; color:#d9b870; }
  #opening.night .opTtl{ font-size:34px; letter-spacing:4px; color:#f1e6c8; margin-top:4px;
    text-shadow:0 0 16px rgba(0,0,0,.5); }
  #opening.night #opCam text{ opacity:0; }
  #opening.night #opCam circle{ filter:drop-shadow(0 0 2.5px #ffe7a6); }
  /* 모드 선택 버튼(타이틀) — 2줄(라벨+설명), 큼직하게 */
  .titlechoice{ display:flex !important; flex-direction:column; align-items:center; gap:1px; min-width:160px;
    padding:11px 20px !important; font-size:16px !important; line-height:1.15; }
  .titlechoice span{ font-size:11px; font-weight:400; opacity:.82; letter-spacing:0; }
  .titleBtn{ position:absolute; left:16px; top:16px; z-index:7; padding:7px 13px; border:1px solid var(--ink-soft);
    background:rgba(233,221,191,.94); border-radius:4px; cursor:pointer; font-family:"Noto Serif KR",serif;
    font-size:13px; color:var(--ink); }
  .titleBtn:hover{ background:rgba(233,221,191,1); }
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
  <div id="relaystage">
    <button id="rsHelp" title="역참로 잇기 도움말">?</button>
    <div class="rsHd"><div class="rsTag">역 참 로</div><div class="rsTtl" id="rsTtl"></div><div class="rsHint" id="rsHint"></div></div>
    <div class="rsStage"><svg id="rsSvg" viewBox="0 0 1000 540" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet" aria-label="역참로 미니게임"></svg></div>
    <div class="rsFoot" id="rsFoot"></div>
    <div id="rsTut"><div class="rsTutCard"><div class="rsTutTag" id="rsTutTag">길잡이</div><div class="rsTutBody" id="rsTutBody"></div>
      <div class="rsTutFoot"><span class="rsTutDots" id="rsTutDots"></span><button id="rsTutSkip">건너뛰기</button><button class="primary" id="rsTutNext">다음 →</button></div></div></div>
  </div>
  <div id="cityscene"><div class="csInner">
    <div class="csArt" id="csArt">삽 화 자 리</div>
    <div class="csTag" id="csTag">도 착</div>
    <div class="csTtl" id="csTtl"></div>
    <div class="csBody" id="csBody"></div>
    <button class="csGo" id="csGo">계속 →</button>
  </div></div>
  <div id="opening">
    <div class="opMap"><svg id="opSvg" viewBox="0 0 1000 520" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" aria-label="오프닝 시네마틱"><rect id="opSky" x="0" y="0" width="1000" height="520" fill="#070b1c"/><g id="opStarfield"></g><g id="opCam"></g></svg></div>
    <div class="opCard">
      <div class="opTag" id="opTag"></div>
      <div class="opTtl" id="opTtl"></div>
      <div class="opBody" id="opBody"></div>
      <button class="opGo" id="opGo">계속 →</button>
    </div>
    <div id="opRead"><div class="opReadInner">
      <div class="opReadArt" id="opReadArt">삽 화 자 리</div>
      <div class="opReadTag" id="opReadTag"></div>
      <div class="opReadTtl" id="opReadTtl"></div>
      <div class="opReadBody" id="opReadBody"></div>
      <button class="opReadGo" id="opReadGo">계속 →</button>
    </div></div>
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
  <button class="pediaBtn sndBtn" id="sndBtn" title="소리 끄기">&#128266;</button>
  <button class="panel titleBtn" id="toTitle" title="타이틀(모드 선택)로">&#9776; 타이틀</button>
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
  var TERRAIN=%%TERRAIN%%, COSTS=%%COSTS%%, BARRIERS=%%BARRIERS%%, CR=%%CR%%, CARTCENTER=%%CARTCENTER%%, GEO=%%GEO%%, INFO=%%INFO%%, PEDIA=%%PEDIA%%, PATHS=%%PATHS%%, FORCEMODE=%%FORCEMODE%%, METRICS=%%METRICS%%, ORBIS=%%ORBIS%%, SCENARIO=%%SCENARIO%%, CITYSCENES=%%CITYSCENES%%, OPENMAP=%%OPENMAP%%, STORY=%%STORY%%, SOUNDS=%%SOUNDS%%, RELAYTERR=%%RELAYTERR%%;
  var NS="http://www.w3.org/2000/svg";
  function el(t,a){var e=document.createElementNS(NS,t);for(var k in a)e.setAttribute(k,a[k]);return e;}
  var byName={}; CITIES.forEach(function(c){byName[c.n]=c;});

  // ---- 사운드(효과음·BGM): 파일은 sounds/ 폴더(page/bgm/select/arrive/star). 브라우저 정책상 첫 클릭에 해제. ----
  var __muted=false, __bgm=null, __sndReady=false;
  try{ __muted = localStorage.getItem("mongolMute")==="1"; }catch(e){}
  function __sfx(name){ if(__muted||!SOUNDS||!SOUNDS[name]) return; try{ var a=new Audio(SOUNDS[name]); a.volume=0.7; a.play().catch(function(){}); }catch(e){} }
  function __startBgm(){ if(!SOUNDS||!SOUNDS.bgm||__muted) return; if(!__bgm){ __bgm=new Audio(SOUNDS.bgm); __bgm.loop=true; __bgm.volume=0.38; } __bgm.play().catch(function(){}); }
  function __unlock(){ if(__sndReady) return; __sndReady=true; __startBgm(); }
  window.addEventListener("pointerdown", __unlock);   // 첫 사용자 제스처에 오디오 해제 + BGM 시작
  window.__sfx=__sfx;
  // 타이틀(별자리) 동안 부모 페이지 배경(좌우 여백·상단 바까지) 밤하늘로(같은 출처라 접근 가능, 막히면 무해). 모드 진입 시 복귀.
  function __pageBg(dark){ try{ var pd=window.parent.document, c=dark?"#070b1c":"";
    var sels=['[data-testid="stApp"]','.stApp','[data-testid="stAppViewContainer"]','[data-testid="stMain"]',
      '[data-testid="stHeader"]','[data-testid="stToolbar"]','[data-testid="stMainBlockContainer"]','.block-container'];
    sels.forEach(function(s){ var el=pd.querySelector(s); if(el) el.style.background=c; });
    pd.body.style.background=c;
  }catch(e){} }
  (function(){ var b=document.getElementById("sndBtn"); if(!b) return;
    function upd(){ b.textContent=__muted?"🔇":"🔊"; b.title=__muted?"소리 켜기":"소리 끄기"; }
    upd();
    b.onclick=function(){ __muted=!__muted; try{ localStorage.setItem("mongolMute", __muted?"1":"0"); }catch(e){}
      if(__muted){ if(__bgm) __bgm.pause(); } else { __sndReady=true; __startBgm(); } upd(); };
  })();

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
    function article(title,sub,bd){ body.className="pBody"; if(window.__sfx) window.__sfx("page");   // 책장 넘기는 소리
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
    window.__setMode=function(m){ if(window.__relayActive) return;   // 역참로 진행 중엔 모드 잠금
      viewMode=m;
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
    var g=el("g",{class:"city"+(selSet[c.n]?" sel":(SELECTED.length?" dim":""))+(c.n===START?" startcity":"")}); groups[c.n]=g;
    g.appendChild(el("circle",{cx:c.x,cy:c.y,r:"13",fill:"transparent"}));
    if(selSet[c.n]) g.appendChild(el("circle",{cx:c.x,cy:c.y,r:"9",fill:"none",stroke:"var(--gold)","stroke-width":"2",class:"selring"}));
    if(c.C){
      g.appendChild(el("polygon",{points:c.x+","+(c.y-9)+" "+(c.x+9)+","+c.y+" "+c.x+","+(c.y+9)+" "+(c.x-9)+","+c.y,fill:"var(--gold)",stroke:"#7a531a","stroke-width":"1",class:"dot"}));
      var lc=el("text",{x:c.x,y:c.y+25,"text-anchor":"middle",style:"font-size:16px;font-weight:700;fill:var(--ink);"+LB});lc.textContent=c.n;g.appendChild(lc);
    }else{
      g.appendChild(el("circle",{cx:c.x,cy:c.y,r:"4",fill:"var(--ink)",class:"dot"}));
      var l=el("text",{x:c.x+8,y:c.y+4,class:(c.M?"lblOn":"lbl"),style:"font-size:13.5px;fill:var(--ink);"+LB});l.textContent=c.n;g.appendChild(l);
    }
    g.addEventListener("click",function(){ if(window.__moved||window.__relayActive) return;
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
    // 2단계 진입: 완전한 순회를 채점했으면 '역참로 잇기' 버튼(거시→미시).
    if(picked.length>=2 && picked.length===SELECTED.length) html += "<button class='go' id='toRelay'>역참로 잇기 →</button>";
    scoreEl.innerHTML=html; scoreEl.classList.add("show");
    var tr=document.getElementById("toRelay"); if(tr) tr.onclick=function(){ if(window.__startRelay) window.__startRelay(picked.slice()); };
  };
  document.getElementById("reset").onclick=function(){
    picked = (START&&selSet[START])?[START]:[]; answerShown=false; drawPlayer(); answerG.innerHTML=""; scoreEl.classList.remove("show");
    prog.textContent = picked.length ? ("출발지("+START+")에서 시작 — 다음 도시 클릭") : "강조된 도시를 순서대로 클릭";
  };
  document.getElementById("collapse").onclick=function(){var g=document.getElementById("game");
    g.classList.toggle("collapsed"); this.textContent=g.classList.contains("collapsed")?"▸":"▾";};

  // ── 인게임 타이틀에서 '스토리' 선택 시: 메인 지도 설정을 폴로 번들(STORY)로 교체 ──
  // 단방향 흐름 유지: app.py가 샌드박스+스토리 설정을 둘 다 주입, 여기서 JS로 전환.
  window.__applyStory=function(S){ if(!S) return;
    SELECTED=S.sel||[]; START=S.start||null; ANSWER=S.answer||{route:[],len:0,label:""}; TERRAIN=!!S.terrain;
    COSTS=S.costs||{}; PATHS=S.paths||{}; METRICS=S.metrics||{}; ORBIS=S.orbis||null;
    SCENARIO=S.scenario||null; CR=S.cr||{}; CARTCENTER=S.cart_center||null;
    selSet={}; SELECTED.forEach(function(n){ selSet[n]=true; });
    // 도시 강조 갱신(sel/dim/startcity + 금색 selring)
    CITIES.forEach(function(c){ var g=groups[c.n]; if(!g) return;
      g.setAttribute("class","city"+(selSet[c.n]?" sel":(SELECTED.length?" dim":""))+(c.n===START?" startcity":""));
      var ring=g.querySelector(".selring");
      if(selSet[c.n]&&!ring){ g.insertBefore(el("circle",{cx:c.x,cy:c.y,r:"9",fill:"none",stroke:"var(--gold)","stroke-width":"2","class":"selring"}), g.childNodes[1]||null); }
      else if(!selSet[c.n]&&ring){ ring.parentNode.removeChild(ring); } });
    // 출발 표식 재생성
    if(startG&&startG.parentNode) startG.parentNode.removeChild(startG); startG=null;
    if(START&&byName[START]){ var sc=byName[START]; startG=el("g",{class:"startmark"});
      startG.appendChild(el("circle",{cx:sc.x,cy:sc.y,r:"4.5",fill:"var(--gold)"}));
      var stg=el("text",{x:sc.x,y:sc.y-15,"text-anchor":"middle",style:"font-size:11px;font-weight:700;fill:var(--gold);"+LB}); stg.textContent="출발"; startG.appendChild(stg);
      cg.appendChild(startG); }
    // 게임 상태/패널 리셋 + 칸의 명 카드 + 지형 viz
    picked=(START&&selSet[START])?[START]:[]; answerShown=false; drawPlayer(); answerG.innerHTML="";
    scoreEl.classList.remove("show"); scoreEl.innerHTML="";
    prog.textContent = picked.length ? ("출발지("+START+")에서 시작 — 다음 도시 클릭") : "강조된 도시를 순서대로 클릭";
    if(SCENARIO){ var kc=SCENARIO.khan_command||""; if(kc){ document.getElementById("khanc").textContent=kc; document.getElementById("khan").classList.add("show"); }
      if(SCENARIO.title){ var tl=document.querySelector("#game .ttl"); if(tl) tl.textContent=SCENARIO.title; } }
    var vz=document.getElementById("viz"); if(vz) vz.classList.toggle("show", !!TERRAIN);
    if(window.__setMode) window.__setMode("draw");   // 스토리는 순행 그리기 모드(게임 패널 표시)
  };

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
    document.getElementById("zrst").onclick=function(){scale=1;tx=0;ty=0;apply();};
    // 장면 전환용: 박스(bx0,by0,bx1,by1)를 화면에 맞춰 애니메이션 줌(역참로 미니게임).
    function animTo(ns,nx,ny,dur){ if(dur==null)dur=650;
      if(dur<=0){ scale=ns; tx=nx; ty=ny; apply(); return; }   // 즉시 세팅(시네마틱 시작 프레임)
      var s0=scale,x0=tx,y0=ty,t0=null;
      function st(ts){ if(t0==null)t0=ts; var k=Math.min(1,(ts-t0)/dur), e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;
        scale=s0+(ns-s0)*e; tx=x0+(nx-x0)*e; ty=y0+(ny-y0)*e; apply(); if(k<1) requestAnimationFrame(st); }
      requestAnimationFrame(st); }
    window.__focus=function(bx0,by0,bx1,by1,dur){ var bw=Math.max(1,bx1-bx0), bh=Math.max(1,by1-by0);
      var ns=Math.min(MAXS,Math.max(MINS, Math.min(1204/bw,602/bh)*0.82)), cx=(bx0+bx1)/2, cy=(by0+by1)/2;
      animTo(ns, 640-ns*cx, 407-ns*cy, dur); };
    window.__resetView=function(dur){ animTo(1,0,0,dur); };})();

  // ====== 2단계: 역참로 미니게임 — 전용 스테이지, 다수 후보 중 보급 4개 선택 ======
  // 거시 채점 후 진입. 각 구간 A→B마다 '다른 화면'(오버레이)으로 전환, 두 도시 사이에 산재한
  // 다수 역참 후보 중 '보급 사거리(R) 안에서 가장 짧게' 잇는 4개를 골라 보급선을 만든다.
  // 채점=DP 최적(정확히 4 경유, 각 구간 ≤R)과 비교. 사거리 초과 구간=빨강·보급 끊김(감점).
  // 전부 iframe 자기완결(Python·데이터 변경 0). 향후 역참 '종류' 세분화 대비해 노드에 t(type) 보유.
  (function(){
    var stage=document.getElementById("relaystage"), svgEl=document.getElementById("rsSvg"),
        rsTtl=document.getElementById("rsTtl"), rsHint=document.getElementById("rsHint"), rsFoot=document.getElementById("rsFoot"),
        game=document.getElementById("game"), scoreEl2=document.getElementById("score"),
        sceneEl=document.getElementById("cityscene"), csTtl=document.getElementById("csTtl"), csTag=document.getElementById("csTag"),
        csBody=document.getElementById("csBody"), csArt=document.getElementById("csArt"), csGo=document.getElementById("csGo");
    var W=1000, H=540, MX=92, CY=270, AX=MX, BX=W-MX, DX=BX-AX;       // 스테이지 좌표계
    // A0·B0·RB·TF(맵→스테이지 변환)는 구간마다 buildCorridor에서 실제 지형 회랑에 맞춰 재설정된다.
    var RB=200, A0={x:AX,y:CY}, B0={x:BX,y:CY}, TF=null;   // RB=기본 사거리(구간마다 buildCorridor에서 회랑 길이×0.34)
    // 역참 종류 — 보급선 = '최소 비용 가변 경로'. 종류마다 사거리(reach)·이동비용(rate)·통행료(toll)가 다르다:
    //  모린=멀리 가나 비쌈(환마)·테르겐=가까우나 쌈(수레)·나린=중간(보안). 개수는 고정이 아니라 비용 최적화의 결과.
    var TYPES=[
      {name:"모린 얌", sub:"말·장거리", tip:"멀리·비쌈", reach:1.55, rate:1.15, toll:1.30, r:6,   fill:"var(--gold)"},
      {name:"테르겐 얌", sub:"수레·물자", tip:"가깝·저렴", reach:0.72, rate:0.85, toll:0.45, r:5,   fill:"#86813c"},
      {name:"나린 얌", sub:"밀행·보안", tip:"중간",     reach:1.05, rate:1.00, toll:0.85, r:5.5, fill:"#2f6f7a"}
    ];
    // 주체 적성(ORBIS.mode): 적성 종류는 사거리↑(×1.15) + 이동비용·통행료↓(×0.82) → 더 멀리·더 싸게 → 주체마다 최적 보급선이 갈린다.
    var PREF={"엘치":0,"오르톡":1,"관료단":2,"포로단":1};
    function persona(){ return (ORBIS&&ORBIS.mode)||"관료단"; }
    function prefType(){ var p=PREF[persona()]; return (p==null)?-1:p; }
    // ── 지형 난이도(맵 전역 격자) + 실제 거리(km) ── G2
    var TOLLKM=200;
    function _dec(b64){ var s=atob(b64), a=new Uint8Array(s.length); for(var i=0;i<s.length;i++) a[i]=s.charCodeAt(i); return a; }
    var TERR=(RELAYTERR&&RELAYTERR.b64)?_dec(RELAYTERR.b64):null, KIND=(RELAYTERR&&RELAYTERR.k)?_dec(RELAYTERR.k):null,
        DES=(RELAYTERR&&RELAYTERR.des)?_dec(RELAYTERR.des):null, VIA=(RELAYTERR&&RELAYTERR.via)?_dec(RELAYTERR.via):null;
    function _samp(arr,mx,my){ if(!arr) return 0; var R=RELAYTERR,
      i=Math.max(0,Math.min(R.w-1,Math.floor((mx-R.x0)/(R.x1-R.x0)*R.w))),
      j=Math.max(0,Math.min(R.h-1,Math.floor((my-R.y0)/(R.y1-R.y0)*R.h))); return arr[j*R.w+i]/255; }
    function desMap(mx,my){ return _samp(DES,mx,my); }      // 사막 강도 0..1
    function viaMap(mx,my){ return VIA?_samp(VIA,mx,my):0.6; } // 사이트 적합도 0..1(高=좋음)
    function desAlong(u,v){ if(!DES||!TF) return 0; var n=4,s=0;   // hop 위 사막도 평균
      for(var k=0;k<=n;k++){ var t=k/n, m=toMap({x:u.x+(v.x-u.x)*t,y:u.y+(v.y-u.y)*t}); s+=desMap(m.x,m.y); } return s/(n+1); }
    var REACHDES=0.55;
    function effReach(u,v){ return reachOf(u)/(1+REACHDES*desAlong(u,v)); }   // 사막 가로지르면 실효 사거리↓(P1, 완전사막≈÷1.55)
    function pxkm(){ return (ORBIS&&ORBIS.pxkm)||1; }
    function toMap(p){ return TF?{x:(p.x-TF.ox)/TF.s+TF.minx, y:(p.y-TF.oy)/TF.s+TF.miny}:p; }   // 스테이지→맵 역변환
    function hardMap(mx,my){ if(!TERR) return 1.0; var R=RELAYTERR,
      i=Math.max(0,Math.min(R.w-1,Math.floor((mx-R.x0)/(R.x1-R.x0)*R.w))),
      j=Math.max(0,Math.min(R.h-1,Math.floor((my-R.y0)/(R.y1-R.y0)*R.h))); return TERR[j*R.w+i]/255*R.scale; }
    function kindMap(mx,my){ if(!KIND) return 0; var R=RELAYTERR,
      i=Math.max(0,Math.min(R.w-1,Math.floor((mx-R.x0)/(R.x1-R.x0)*R.w))),
      j=Math.max(0,Math.min(R.h-1,Math.floor((my-R.y0)/(R.y1-R.y0)*R.h))); return KIND[j*R.w+i]; }
    function terrMult(u,v){ if(!TERR||!TF) return 1.0; var n=5,s=0;   // hop 위 6점 평균 난이도(평지1·산악·사막↑·바다=불가)
      for(var k=0;k<=n;k++){ var t=k/n, m=toMap({x:u.x+(v.x-u.x)*t,y:u.y+(v.y-u.y)*t}); s+=hardMap(m.x,m.y); } return s/(n+1); }
    function kmOf(u,v){ return TF? dist(u,v)/TF.s*pxkm() : dist(u,v); }   // 실제 거리(km)
    // 노드 사거리·이동비용 rate·통행료. A0/B0(인장)는 .t 없음 → 기본 사거리·rate 1·통행료 0.
    function reachOf(nd){ if(!nd||nd.t==null) return RB; var ty=TYPES[nd.t]; return RB*ty.reach*(nd.t===prefType()?1.15:1); }
    function rateOf(nd){ if(!nd||nd.t==null) return 1.0; var ty=TYPES[nd.t]; return ty.rate*(nd.t===prefType()?0.82:1); }
    function tollOf(nd){ if(!nd||nd.t==null) return 0; var ty=TYPES[nd.t]; return ty.toll*TOLLKM*(nd.t===prefType()?0.82:1); }
    // 이동 비용 = 실제 거리(km) × 출발 종류 rate × 구간 지형 난이도. 산·사막·바다 횡단은 비싸 → 최적이 쉬운 지형으로 우회.
    function hopCost(u,v){ return kmOf(u,v)*rateOf(u)*terrMult(u,v); }
    var legs=[], li=0, nodes=[], pick=[], starsArr=[], curA="", curB="", active=false;
    function hash(s){ var h=2166136261; for(var i=0;i<s.length;i++){ h^=s.charCodeAt(i); h=Math.imul(h,16777619);} return h>>>0; }
    function rng(seed){ var s=(seed>>>0)||1; return function(){ s=(Math.imul(s,1664525)+1013904223)>>>0; return s/4294967296; }; }
    function clampY(y){ return Math.max(56,Math.min(H-56,y)); }
    function clampX(x){ return Math.max(38,Math.min(W-38,x)); }
    function dist(p,q){ return Math.hypot(p.x-q.x, p.y-q.y); }
    // ====== 실제 지형 회랑(G1) — 전용 스테이지에 본 지도 슬라이스를 변환해 그린다 ======
    // 맵 좌표(1280×780) → 스테이지 좌표(1000×540): 구간 A→B 회랑 bbox를 스테이지에 맞춰 확대(실제 방향·위치).
    function toStage(p){ return {x: TF.ox+(p.x-TF.minx)*TF.s, y: TF.oy+(p.y-TF.miny)*TF.s}; }
    function plLen(pts){ var seg=[0],L=0; for(var i=0;i<pts.length-1;i++){ L+=Math.hypot(pts[i+1].x-pts[i].x,pts[i+1].y-pts[i].y); seg.push(L);} return {L:L||1,seg:seg}; }
    function plAt(pts,si,frac){ var t=frac*si.L,i;   // 폴리라인을 길이 비율로 샘플 + 법선(n) 반환
      for(i=0;i<pts.length-1;i++){ if(si.seg[i+1]>=t){ var d=si.seg[i+1]-si.seg[i]||1,u=(t-si.seg[i])/d,
        tx=pts[i+1].x-pts[i].x, ty=pts[i+1].y-pts[i].y, nl=Math.hypot(tx,ty)||1;
        return {x:pts[i].x+tx*u, y:pts[i].y+ty*u, nx:-ty/nl, ny:tx/nl}; } }
      var L=pts[pts.length-1]; return {x:L.x,y:L.y,nx:0,ny:1}; }
    // 역참 후보 사이트(실제 회랑 위·주변, 각자 종류 고정). 최소-비용 가변 경로의 그래프 노드.
    //  ① 테르겐 촘촘(저렴·근거리): 회랑 위 5 — 늘 실현가능한 다(多)역참 보급선 보장.
    //  ② 모린 성김(비싸나 장거리): 회랑 위 2~3 — 적은 역참(예: 2개)으로 잇는 선택지(특히 엘치 적성).
    //  ③ 나린 중간: 회랑서 약간 옆 2. ④ 미끼: 회랑서 멀리(혼합) — 우회 손해.
    // 사이트를 적합 지형(via 높은 곳)으로 스냅: 봉우리·사막내부에서 강 계곡·오아시스·스텝으로 끌림(P2). 작은 국소 탐색.
    function snapVia(x,y){ if(!VIA||!TF) return {x:clampX(x),y:clampY(y)};
      var bx=x,by=y,bv=viaMap(toMap({x:x,y:y}).x, toMap({x:x,y:y}).y);
      for(var a2=0;a2<8;a2++){ for(var rr=1;rr<=2;rr++){ var ang=a2/8*6.2832, sx=x+Math.cos(ang)*rr*13, sy=y+Math.sin(ang)*rr*13,
        m=toMap({x:sx,y:sy}), v=viaMap(m.x,m.y); if(v>bv+0.02){ bv=v; bx=sx; by=sy; } } }
      return {x:clampX(bx), y:clampY(by)}; }
    function genSites(a,b,corS){ var r=rng(hash([a,b].sort().join("|"))), out=[], si=plLen(corS);
      function on(f,jit,t){ var p=plAt(corS,si,f), s=snapVia(p.x+(r()-0.5)*8, p.y+(r()-0.5)*jit); return {x:s.x,y:s.y,t:t}; }
      function off(f,frac,side,t){ var p=plAt(corS,si,f), o=si.L*frac*side, s=snapVia(p.x+p.nx*o, p.y+p.ny*o); return {x:s.x,y:s.y,t:t}; }
      // ① 테르겐 레인(실현가능 백본): 회랑 따라 '국소 effReach'에 맞춰 그리디 배치(사막 구간 자동 밀집). 스냅 안 함(회랑=최소비용 viable).
      var prev={x:A0.x,y:A0.y}, step=Math.max(5, si.L/420);
      for(var t=step; t<si.L-2; t+=step){ var p=plAt(corS,si,t/si.L), m=toMap(p),
          lr=(RB*0.72)/(1+REACHDES*desMap(m.x,m.y));                   // 국소 테르겐 실효 사거리
        if(dist(prev,p)>=lr*0.80){ var nd={x:clampX(p.x+(r()-0.5)*4),y:clampY(p.y+(r()-0.5)*6),t:1}; out.push(nd); prev=nd; } }  // 간격 0.80(덜 촘촘)·지터 작게
      var pe={x:clampX(plAt(corS,si,0.94).x),y:clampY(plAt(corS,si,0.94).y+(r()-0.5)*10)};
      if(dist(prev,pe)>=14) out.push({x:pe.x,y:pe.y,t:1});             // 끝 보강은 가까우면 생략(겹침 방지)
      // ② 모린 성김·③ 나린·④ 미끼 — 거리에 비례, via로 스냅. 최소 간격(MINSEP) 미만이면 버려 겹침 방지(백본은 항상 유지).
      var MINSEP=14;
      function pushFar(s){ for(var i=0;i<out.length;i++){ if(dist(out[i],s)<MINSEP) return; } out.push(s); }
      var span=Math.max(1.4, si.L/RB), nM=Math.max(2,Math.round(span/1.55)+1), nN=Math.max(2,Math.round(span*0.45)), nD=Math.max(4,Math.round(span*0.7));
      for(var i2=0;i2<nM;i2++) pushFar(on((i2+0.5)/nM + (r()-0.5)*0.04, 18, 0));            // 모린 성김
      for(var i3=0;i3<nN;i3++) pushFar(off((i3+0.7)/(nN+0.4), 0.06+r()*0.03, (r()<0.5?1:-1), 2));  // 나린(회랑 옆)
      var dT=[1,2,0,1,2,0];
      for(var k=0;k<nD;k++){ var f=0.1+r()*0.8; pushFar(off(f, 0.16+r()*0.12, (r()<0.5?1:-1), dT[k%dT.length])); }  // 미끼
      return out; }
    // 지형 난이도 음영 — 본 지도(탐험 모드)와 '동일 방식': 작은 난이도 격자(GEO.heat)를 캔버스로 만들어 <image>로 확대
    // (브라우저 bilinear 스무딩) → 마스킹 없는 연속 그라데이션이라 매끄럽고 익숙. 양피지·강·역참로·사이트가 그 아래로 또렷.
    function heatImage(){ var h=GEO.heat; if(!h||!h.b64) return null;
      var bin=atob(h.b64), cv=document.createElement("canvas"); cv.width=h.w; cv.height=h.h;
      var ctx=cv.getContext("2d"), im=ctx.createImageData(h.w,h.h);
      for(var p=0;p<h.w*h.h;p++){ var v=bin.charCodeAt(p)/255;
        im.data[p*4]=120; im.data[p*4+1]=80; im.data[p*4+2]=45; im.data[p*4+3]=Math.pow(v,1.4)*120; }
      ctx.putImageData(im,0,0);
      var img=el("image",{x:h.x0,y:h.y0,width:h.x1-h.x0,height:h.y1-h.y0,preserveAspectRatio:"none",opacity:"0.78"});
      img.setAttribute("href",cv.toDataURL()); return img; }
    // 사막 기호: 점묘(흩뿌린 모래알) + 가끔 짧은 모래언덕 곡선.
    function duneGlyph(x,y,rg){ var g=el("g",{}), c="#a98a55";
      for(var i=0;i<5;i++) g.appendChild(el("circle",{cx:(x+(rg()-0.5)*15).toFixed(1),cy:(y+(rg()-0.5)*10).toFixed(1),r:(rg()*0.5+0.7).toFixed(2),fill:c,opacity:"0.85"}));
      if(rg()<0.5) g.appendChild(el("path",{d:"M"+(x-6)+","+(y+4)+" q6,-4 12,0",fill:"none",stroke:c,"stroke-width":"0.8",opacity:"0.7"}));
      return g; }
    // 본 지도 슬라이스(정적 레이어): 바다 베이스 + 변환된 해안선·(난이도 heat)·호수·강·역참로. 스트로크는 비-스케일.
    function geoSlice(){ var root=el("g",{});
      root.appendChild(el("rect",{x:"0",y:"0",width:String(W),height:String(H),fill:"var(--sea)","fill-opacity":"0.5"}));
      var g=el("g",{transform:"translate("+TF.ox+","+TF.oy+") scale("+TF.s+") translate("+(-TF.minx)+","+(-TF.miny)+")"});
      (GEO.land||[]).forEach(function(d){ g.appendChild(el("path",{d:d,fill:"var(--parchment)",stroke:"var(--ink-soft)","stroke-width":"0.9","vector-effect":"non-scaling-stroke","stroke-linejoin":"round","stroke-linecap":"round"})); });
      var hImg=heatImage(); if(hImg) g.appendChild(hImg);   // 지형 난이도 = 부드러운 heat 한 장(육지 위)
      (GEO.lakes||[]).forEach(function(d){ g.appendChild(el("path",{d:d,fill:"var(--sea)","fill-opacity":"0.85",stroke:"none"})); });
      (GEO.rivers||[]).forEach(function(d){ g.appendChild(el("path",{d:d,fill:"none",stroke:"#6f8c88","stroke-width":"0.9","vector-effect":"non-scaling-stroke",opacity:"0.6"})); });
      (GEO.yampaths||[]).forEach(function(d){ g.appendChild(el("path",{d:d,fill:"none",stroke:"var(--gold)","stroke-width":"1.1","stroke-dasharray":"4 4","vector-effect":"non-scaling-stroke",opacity:"0.5"})); });
      root.appendChild(g);
      // 사막 = 옛 지도식 점묘(매끄러운 heat 위, 사막 셀에만). 스테이지 좌표=일정 크기, 시드 PRNG로 leg마다 고정.
      if(KIND){ var rg=rng(hash(curA+"|"+curB+"|ico")), STc=34;
        for(var iy=58; iy<H-50; iy+=STc){ for(var ix=26; ix<W-26; ix+=STc){
          var jx=ix+(rg()-0.5)*26, jy=iy+(rg()-0.5)*22, m=toMap({x:jx,y:jy});
          if(kindMap(m.x,m.y)===2 && rg()<0.72) root.appendChild(duneGlyph(jx,jy,rg)); } } }
      return root; }
    // 구간 회랑 준비: 변환·A0/B0·RB·후보 사이트·정적 지도 레이어 구성.
    function buildCorridor(a,b){
      var pa=byName[a], pb=byName[b], corM;
      if(pa&&pb){ var P=(PATHS&&PATHS[[a,b].sort().join("|")]);
        if(P&&P.length>1){ corM=P.map(function(q){return {x:q[0],y:q[1]};});
          if(dist(corM[0],pa)>dist(corM[corM.length-1],pa)) corM.reverse(); }   // 정렬키라 방향이 뒤집힐 수 있음 → a에 가깝게
        else corM=[{x:pa.x,y:pa.y},{x:pb.x,y:pb.y}]; }
      else { corM=[{x:0,y:CY},{x:DX,y:CY}]; }                                    // 폴백(좌표 없음): 추상 직선
      var xs=corM.map(function(p){return p.x;}), ys=corM.map(function(p){return p.y;});
      var minx=Math.min.apply(null,xs),maxx=Math.max.apply(null,xs),miny=Math.min.apply(null,ys),maxy=Math.max.apply(null,ys);
      // 패딩은 회랑의 '큰 변' 기준(양축 동일) → 짧은/가는 회랑도 A0~B0가 스테이지를 충분히 채움(고정값 지배 방지).
      var span=Math.max(maxx-minx, maxy-miny, 1), pad=span*0.14+8; minx-=pad;maxx+=pad;miny-=pad;maxy+=pad;
      var bw=Math.max(1,maxx-minx), bh=Math.max(1,maxy-miny);
      var availW=W-80, availH=H-92, s=Math.min(availW/bw, availH/bh);            // 상단 46·하단 46 여백(범례)
      TF={s:s, ox:40+(availW-bw*s)/2, oy:46+(availH-bh*s)/2, minx:minx, miny:miny};
      var corS=corM.map(toStage); A0=corS[0]; B0=corS[corS.length-1];
      // 사거리 = '실제 km'(REACHKM) 기준 → 역참 수 ≈ 실제거리/REACHKM. 소프트 캡은 '테르겐-사막' 최악 개수 기준(사막=사거리↓라 더 많아짐).
      var si=plLen(corS), pk=pxkm();
      if(ORBIS&&ORBIS.pxkm){ var corrKm=si.L/TF.s*pk, REACHKM=700, capN=11;
        var corrDes=0; for(var q=0;q<=10;q++){ var mm=toMap(plAt(corS,si,q/10)); corrDes+=desMap(mm.x,mm.y); } corrDes/=11;
        var estN=corrKm/(REACHKM*0.72)*(1+REACHDES*corrDes)*1.12;       // 테르겐(사거리×0.72)·사막 축소·안전계수 → 최악 개수 추정
        var effKm=REACHKM*Math.max(1, estN/capN);                       // 추정이 capN 넘으면 사거리 넓혀 ~capN로 묶음
        RB=Math.min(Math.max(40, effKm*TF.s/pk), si.L*0.42);           // floor: 짧은 구간도 ≥~2역참(0=비-게임 방지)
        TOLLKM=(RB/TF.s*pk)*4.0; }                                      // 통행료=실제 hop 길이(RB_km)에 비례 → 종류 트레이드오프 거리무관
      else { RB=Math.max(48, si.L*0.34); TOLLKM=Math.max(40, si.L*0.20); }  // 지형 OFF(실제 km 없음): 정규화 폴백
      nodes=genSites(a,b,corS);
      svgEl.innerHTML=""; svgEl.appendChild(geoSlice()); svgEl.appendChild(el("g",{id:"rsDyn"}));   // 정적 지도 + 동적 레이어
    }
    // 최소 비용 가변 경로(Dijkstra): A0 → (역참 임의 개수·순서) → B0. 개수 고정 없음.
    //  간선 u→v: dist(u,v) ≤ reachOf(u)(보급 도달)일 때만. 비용 = 이동비용 hopCost(u,v) + 도착 노드 통행료 tollOf(v).
    //  → '적은 비싼 모린' vs '많은 싼 테르겐'의 트레이드오프가 최적 개수를 결정. 종류·적성이 경로 구조를 가른다.
    function solveOpt(){ var n=nodes.length, V=n+2, SRC=n, DST=n+1;   // SRC=A0, DST=B0
      function node(i){ return i===SRC?A0 : i===DST?B0 : nodes[i]; }
      var V2=V, d=new Array(V2).fill(Infinity), par=new Array(V2).fill(-1), done=new Array(V2).fill(false);
      d[SRC]=0;
      function relax(u){ var pu=node(u);
        for(var v=0;v<V2;v++){ if(v===u||v===SRC) continue; var pv=node(v), dd=dist(pu,pv);
          if(dd>effReach(pu,pv)) continue; var nc=d[u]+hopCost(pu,pv)+tollOf(pv); if(nc<d[v]){ d[v]=nc; par[v]=u; } } }
      for(var it=0;it<V2;it++){ var best=Infinity,bu=-1;
        for(var i=0;i<V2;i++){ if(!done[i]&&d[i]<best){best=d[i];bu=i;} }
        if(bu<0) break; done[bu]=true; if(bu===DST) break; relax(bu); }
      if(d[DST]===Infinity) return null;
      var idx=[], cur=par[DST]; while(cur>=0 && cur!==SRC){ idx.unshift(cur); cur=par[cur]; }   // 중간 역참들(B0 제외)
      return {cost:d[DST], idx:idx}; }
    // (디버그/튜닝) 현재 nodes·주체 기준 최적 보급선 요약: {cost, relays, types}. 측정용.
    window.__relayOpt=function(){ var o=solveOpt(); if(!o) return null;
      return {cost:Math.round(o.cost), relays:o.idx.length, types:o.idx.map(function(ix){return nodes[ix].t;})}; };
    // 체인(인덱스 배열) → 좌표열 [A0, …역참…, B0]. cost=이동비용 합 + 역참 통행료 합. feasible=각 hop ≤ reachOf(출발).
    function chainSeq(idxArr){ var s=[A0]; idxArr.forEach(function(ix){ s.push(nodes[ix]); }); s.push(B0); return s; }
    function chainCost(idxArr){ var seq=[A0]; idxArr.forEach(function(ix){ seq.push(nodes[ix]); }); seq.push(B0);
      var c=0, km=0, feasible=true;
      for(var i=0;i<seq.length-1;i++){ if(dist(seq[i],seq[i+1])>effReach(seq[i],seq[i+1])+0.5) feasible=false;
        c+=hopCost(seq[i],seq[i+1]); km+=kmOf(seq[i],seq[i+1]); }
      idxArr.forEach(function(ix){ c+=tollOf(nodes[ix]); });
      return {cost:c, km:km, feasible:feasible}; }
    function head(){ return pick.length? nodes[pick[pick.length-1]] : A0; }
    function reaches(u,v){ return dist(u,v) <= effReach(u,v)+0.5; }   // 지형(사막) 반영 실효 사거리
    function bReached(){ return reaches(head(), B0); }   // 머리에서 도착(B0)까지 보급이 닿으면 보급선 완성 가능
    function partialCost(){ var seq=[A0]; pick.forEach(function(ix){seq.push(nodes[ix]);}); var c=0;
      for(var i=0;i<seq.length-1;i++) c+=hopCost(seq[i],seq[i+1]); pick.forEach(function(ix){c+=tollOf(nodes[ix]);}); return c; }
    function draw(optIdx){
      var dyn=document.getElementById("rsDyn"); if(!dyn){ dyn=el("g",{id:"rsDyn"}); svgEl.appendChild(dyn); } dyn.innerHTML="";
      var pf=prefType(), hd=head();
      // 종류 범례(상단) — 이름 + 트레이드오프(사거리·비용). 지도 위 가독성 위해 옅은 배경 띠.
      dyn.appendChild(el("rect",{x:"0",y:"0",width:String(W),height:"44",fill:"#efe6ce","fill-opacity":"0.85"}));
      var lx=54; TYPES.forEach(function(ty,ti){ var on=ti===pf;
        dyn.appendChild(el("circle",{cx:lx,cy:20,r:"5.5",fill:ty.fill,stroke:on?"var(--route)":"#7a531a","stroke-width":on?"2":"1"}));
        var lt=el("text",{x:lx+11,y:18,style:"font-size:12px;font-weight:"+(on?"700":"600")+";fill:"+(on?"var(--route)":"var(--ink)")+";"+LB});
        lt.textContent=ty.name+(on?" ◆":""); dyn.appendChild(lt);
        var lp=el("text",{x:lx+11,y:32,style:"font-size:9.5px;fill:var(--ink-soft);"+LB}); lp.textContent=ty.tip; dyn.appendChild(lp);
        lx+=158; });
      dyn.appendChild(el("text",{x:W-16,y:18,"text-anchor":"end",style:"font-size:10px;fill:var(--ink-soft);"+LB})).textContent="◆ 주체 적성";
      dyn.appendChild(el("text",{x:W-16,y:31,"text-anchor":"end",style:"font-size:10px;fill:var(--ink-soft);"+LB})).textContent="더 멀리·더 싸게";
      // 보급 도달 범위(현재 머리) — effReach를 방향별로 샘플한 '정직한' 블롭(사막 방향은 짧게). 링 안=실제로 닿는 곳.
      if(active){ var bn=30, bp=[];
        for(var bi=0;bi<bn;bi++){ var ang=bi/bn*6.2832, cc=Math.cos(ang), ss=Math.sin(ang),
            er=effReach(hd,{x:hd.x+cc*reachOf(hd)*0.66, y:hd.y+ss*reachOf(hd)*0.66});
          bp.push((hd.x+cc*er).toFixed(1)+","+(hd.y+ss*er).toFixed(1)); }
        dyn.appendChild(el("polygon",{points:bp.join(" "),fill:"var(--gold)","fill-opacity":"0.05",stroke:"var(--gold)","stroke-width":"1.4","stroke-dasharray":"3 6",opacity:"0.5"})); }
      // 최적 보급선(채점 후 잔상)
      if(optIdx){ var oseq=chainSeq(optIdx);
        dyn.appendChild(el("polyline",{points:oseq.map(function(p){return p.x+","+p.y;}).join(" "),fill:"none",stroke:"var(--route)","stroke-width":"2","stroke-dasharray":"6 5",opacity:"0.6"})); }
      // 플레이어 보급선(순서대로) — 닿으면 녹, 초과면 적
      var seq=chainSeq(pick), drawTo=active?(bReached()?seq.length-1:seq.length-2):seq.length-1;
      for(var i=0;i<drawTo;i++){ var ok=reaches(seq[i],seq[i+1]);
        dyn.appendChild(el("line",{x1:seq[i].x,y1:seq[i].y,x2:seq[i+1].x,y2:seq[i+1].y,stroke:ok?"#2f7a4f":"#b3402b","stroke-width":"3","stroke-linecap":"round",opacity:"0.95"})); }
      // 후보 사이트 — 종류 색, 적성 외곽 링, 머리에서 닿으면 또렷·아니면 흐림, 체인에 든 것은 순번
      nodes.forEach(function(nd,idx){ var oi=pick.indexOf(idx), inChain=oi>=0, ty=TYPES[nd.t]||TYPES[0],
        canReach=active&&!inChain&&reaches(hd,nd), g=el("g",{class:"st"});
        g.appendChild(el("circle",{cx:nd.x,cy:nd.y,r:"15",fill:"transparent"}));
        if(active && !inChain && !canReach) g.setAttribute("opacity","0.4");   // 닿지 않는 후보는 흐리게
        if(!inChain && nd.t===pf) g.appendChild(el("circle",{cx:nd.x,cy:nd.y,r:String(ty.r+3.5),fill:"none",stroke:"var(--route)","stroke-width":"1.6",opacity:"0.75"}));
        if(canReach) g.appendChild(el("circle",{cx:nd.x,cy:nd.y,r:String(ty.r+2),fill:"none",stroke:"var(--gold)","stroke-width":"1.4",opacity:"0.9"}));
        g.appendChild(el("circle",{cx:nd.x,cy:nd.y,r:inChain?"8":String(ty.r),fill:inChain?"var(--player)":ty.fill,stroke:"#fff","stroke-width":"1.4"}));
        if(inChain){ var t=el("text",{x:nd.x,y:nd.y+3.4,"text-anchor":"middle",style:"font-size:10px;font-weight:700;fill:#f3ece0"}); t.textContent=(oi+1); g.appendChild(t); }
        g.addEventListener("click",function(){ if(active) chainClick(idx); });
        dyn.appendChild(g); });
      function seal(p,color,name,sub){ var g=el("g",{});
        g.appendChild(el("circle",{cx:p.x,cy:p.y,r:"15",fill:color,opacity:"0.96"}));
        g.appendChild(el("circle",{cx:p.x,cy:p.y,r:"15",fill:"none",stroke:"#fff","stroke-width":"1.4",opacity:"0.6"}));
        var t=el("text",{x:p.x,y:p.y-23,"text-anchor":"middle",style:"font-size:13px;font-weight:700;paint-order:stroke;stroke:#efe6ce;stroke-width:3px;fill:"+color+";"+LB}); t.textContent=name; g.appendChild(t);
        var s=el("text",{x:p.x,y:p.y+4,"text-anchor":"middle",style:"font-size:9px;font-weight:700;fill:#fff"}); s.textContent=sub; g.appendChild(s);
        dyn.appendChild(g); }
      seal(A0,"#2f7a4f",curA,"출발"); seal(B0,"var(--route)",curB,"도착");
      // 도착까지 보급이 닿으면 B에 펄스 — "이으면 완성" 명확히.
      if(active && bReached()){ var pr=el("circle",{cx:B0.x,cy:B0.y,r:"19",fill:"none",stroke:"var(--gold)","stroke-width":"2.5",opacity:"0.9"});
        pr.appendChild(el("animate",{attributeName:"r",values:"16;25;16",dur:"1.3s",repeatCount:"indefinite"}));
        pr.appendChild(el("animate",{attributeName:"opacity",values:"0.95;0.3;0.95",dur:"1.3s",repeatCount:"indefinite"})); dyn.appendChild(pr); }
    }
    // 체인 클릭: 머리에서 닿는 새 사이트=추가, 체인 안 사이트=거기까지로 되돌림(재경로). 못 닿으면 빨강 깜빡(왜 안 되는지 피드백).
    function chainClick(idx){ var at=pick.indexOf(idx);
      if(at>=0){ pick=pick.slice(0, at); }                                  // 이미 든 노드 클릭 → 그 앞까지 잘라 되돌림
      else if(reaches(head(), nodes[idx])) pick.push(idx);                  // 닿으면 추가
      else { flashUnreach(idx); return; }                                  // 사거리 밖 → 깜빡(추가 안 됨)
      draw(null); foot(); }
    function flashUnreach(idx){ var dyn=document.getElementById("rsDyn"); if(!dyn) return; var nd=nodes[idx];
      var fl=el("circle",{cx:nd.x,cy:nd.y,r:"11",fill:"none",stroke:"#b3402b","stroke-width":"2.5",opacity:"0.95"}); dyn.appendChild(fl);
      if(window.__sfx) window.__sfx("select");
      setTimeout(function(){ if(fl.parentNode) fl.parentNode.removeChild(fl); }, 460); }
    function foot(){ var pf=prefType(), can=bReached();
      rsHint.textContent="역참을 이어 보급선을 잇고 — 비용(=거리×지형+통행료)을 가장 낮게, 개수는 자유   ·   주체 "+persona()+(pf>=0?" 적성: "+TYPES[pf].name:"");
      var info="역참 "+pick.length+"개"+(can?"  ·  도착까지 보급 연결됨 ✓":"  ·  도착(B)까지 더 이으시오");
      rsFoot.innerHTML="<div class='rsRes' style='margin-right:8px'>"+info+"</div>"+
        "<button class='primary' id='rsDone'"+(can?"":" disabled")+">보급선 완성</button><button id='rsReset'>다시</button>";
      document.getElementById("rsDone").onclick=function(){ if(bReached()) grade(); };
      document.getElementById("rsReset").onclick=function(){ pick=[]; draw(null); foot(); };
    }
    function grade(){ active=false;
      var pc=chainCost(pick), feasible=pc.feasible, opt=solveOpt();
      draw(opt?opt.idx:null);
      var gap=opt?(pc.cost-opt.cost)/(opt.cost||1)*100:0, s=feasible?starsFor(gap,[12,26,48]):0;
      starsArr[li]=s;
      var glyph=""; for(var k=0;k<3;k++) glyph+=(k<s?"<span>★</span>":"<span class='off'>★</span>");
      var last=li===legs.length-1;
      var msg=feasible ? ("역참 "+pick.length+"개 · "+Math.round(pc.km)+"km · 최적 대비 "+(gap<1.5?"<b>최적!</b>":"+"+gap.toFixed(0)+"%"))
                       : "<span class='warn'>보급 끊김 — 사거리 초과 구간</span>";
      rsFoot.innerHTML="<div class='rsRes'><div class='stars'>"+glyph+"</div><div>"+msg+"</div></div>"+
        "<button id='rsRetry'>다시</button><button class='primary' id='rsNext'>"+(last?"순행 완주 →":"다음 역참로 →")+"</button>";
      document.getElementById("rsRetry").onclick=function(){ pick=[]; active=true; draw(null); foot(); };
      document.getElementById("rsNext").onclick=function(){ afterLeg(last); };
    }
    // 구간 완료 → 다음으로. 스토리 모드면 연출을 끼우고 진행.
    // 마지막 구간(귀환) 후엔 도시 도착 대신 '칸께 고하다'(closing) 연출.
    function afterLeg(last){
      function go(){ if(last) finish(); else { li++; loadLeg(); } }
      if(!SCENARIO){ go(); return; }
      if(last && SCENARIO.closing) playScene(SCENARIO.closing, "칸 께 고 하 다", "순행을 마치다 →", go);
      else showSceneCity(legs[li][1], last, go);   // 방금 도착한 도시(이 구간의 도착지)
    }
    // 도착 연출 해상도: 이야기별 덮어쓰기 > city_scenes.json > 자동 플레이스홀더.
    function sceneFor(city){
      var sc=(SCENARIO && SCENARIO.scenes && SCENARIO.scenes[city]) || (CITYSCENES && CITYSCENES[city]);
      if(!sc) sc={title:city, lines:["("+city+"에 도착했다. 풍경 묘사를 적으세요 — city_scenes.json)"], img:null};
      return sc;
    }
    function showSceneCity(city, isLast, cont){ playScene(sceneFor(city), "도 착", isLast?"여정의 끝 →":"다음 역참로 →", cont); }
    // 범용 연출 재생: 오프닝·도착·보고(closing) 모두 같은 오버레이로.
    function playScene(sc, tag, btnLabel, cont){
      if(!sc){ cont(); return; }
      if(window.__sfx) window.__sfx("page");   // 책 넘기는 소리(도착·보고 연출 카드)
      csTtl.textContent=sc.title||""; csTag.textContent=tag||"연 출";
      csBody.innerHTML=""; (sc.lines||[]).forEach(function(ln){ var p=document.createElement("div"); p.className="csLine"; p.textContent=ln||""; csBody.appendChild(p); });
      if(sc.img){ csArt.style.backgroundImage="url('"+sc.img+"')"; csArt.textContent=""; csArt.classList.add("hasimg"); }
      else { csArt.style.backgroundImage=""; csArt.textContent="삽 화 자 리"; csArt.classList.remove("hasimg"); }
      csGo.textContent=btnLabel||"계속 →";
      sceneEl.classList.add("show");
      csGo.onclick=function(){ sceneEl.classList.remove("show"); cont(); };
    }
    window.__playScene=playScene;   // 스토리 오프닝 시네마틱(로드 시)에서 재사용
    function loadLeg(){ active=true; curA=legs[li][0]; curB=legs[li][1]; buildCorridor(curA,curB); pick=[];
      rsTtl.textContent=curA+"  →  "+curB+"   ("+(li+1)+" / "+legs.length+")";
      draw(null); foot();
      if(li===0) relayTutorial(false);   // 첫 구간(대도→상도)에서 1회 길잡이
    }
    // 역참로 튜토리얼 — 비차단 하단 길잡이 카드(4단계). force=true면 ? 버튼서 재호출(localStorage 무시).
    var TUT=[
      "<b>역참로 잇기</b> — 출발 <b>"+("")+"</b>에서 도착까지 보급선을 역참으로 잇습니다. 방금 짠 거시 순행로의 한 구간을 직접 채우는 단계예요.",
      "<b>보급 범위</b> — 출발점의 <b>점선 원</b>이 보급이 닿는 거리입니다. 그 안의 역참만 이을 수 있고, <b>닿는 후보는 금색 테두리</b>로 빛나요. 금색 역참을 <b>클릭</b>해 잇고, 잘못 골랐으면 그 역참을 <b>다시 클릭</b>해 되돌립니다.",
      "<b>역참 종류</b> — 위 범례처럼 <b>모린</b>(멀리·비쌈)·<b>테르겐</b>(가깝·저렴)·<b>나린</b>(중간)이 있습니다. 주체 적성(◆) 종류는 더 멀리·더 싸게 가요. 사막·산은 보급이 짧게 닿고 비싸니, <b>강·오아시스를 따라</b> 잇는 게 유리합니다.",
      "<b>목표</b> — 도착까지 이으면 <b>‘보급선 완성’</b>. 적은 역참·짧은 길로 <b>총비용이 최적에 가까울수록 별 ★★★</b>. 자, 직접 이어보세요!"
    ];
    function relayTutorial(force){
      try{ if(!force && localStorage.getItem("mongolRelayTut")) return; }catch(e){}
      var tut=document.getElementById("rsTut"); if(!tut) return;
      var body=document.getElementById("rsTutBody"), dots=document.getElementById("rsTutDots"),
          nextB=document.getElementById("rsTutNext"), skipB=document.getElementById("rsTutSkip"); var i=0;
      function show(){ body.innerHTML=TUT[i].replace("출발 <b></b>","출발 <b>"+curA+"</b>");
        var dd=""; for(var k=0;k<TUT.length;k++) dd+=(k===i?"●":"○"); dots.textContent=dd;
        nextB.textContent=(i===TUT.length-1)?"시작하기":"다음 →"; skipB.style.display=(i===TUT.length-1)?"none":"";
        tut.classList.add("show"); }
      function done(){ tut.classList.remove("show"); try{ localStorage.setItem("mongolRelayTut","1"); }catch(e){} }
      nextB.onclick=function(){ if(window.__sfx) window.__sfx("page"); i++; if(i>=TUT.length) done(); else show(); };
      skipB.onclick=done; show();
    }
    (function(){ var hb=document.getElementById("rsHelp"); if(hb) hb.onclick=function(){ relayTutorial(true); }; })();
    function finish(){ active=false; window.__relayActive=false;
      var tot=0; starsArr.forEach(function(x){ tot+=(x||0); }); var mx=legs.length*3, best=tot;
      try{ var key="mongolRelay:"+(SCENARIO?(SCENARIO.id||SCENARIO.title):("free:"+SELECTED.slice().sort().join(",")));
        var pv=parseInt(localStorage.getItem(key)); if(!isNaN(pv)) best=Math.max(best,pv); localStorage.setItem(key,String(best)); }catch(e){}
      // 스테이지에 완주 요약 렌더
      svgEl.innerHTML="";
      svgEl.appendChild(el("text",{x:W/2,y:118,"text-anchor":"middle",style:"font-size:15px;font-weight:700;letter-spacing:4px;fill:var(--gold)"})).textContent="역 참 로  완 주";
      svgEl.appendChild(el("text",{x:W/2,y:172,"text-anchor":"middle",style:"font-size:34px;font-weight:700;fill:var(--ink)"})).textContent=tot+" / "+mx+" ★";
      if(best>tot) svgEl.appendChild(el("text",{x:W/2,y:200,"text-anchor":"middle",style:"font-size:13px;fill:var(--ink-soft)"})).textContent="최고 "+best+" / "+mx+" ★";
      legs.forEach(function(lg,i){ var y=246+i*30;
        var t=el("text",{x:W/2,y:y,"text-anchor":"middle",style:"font-size:13px;fill:var(--ink)"});
        t.textContent=(i+1)+".  "+lg[0]+" → "+lg[1]+"      "+("★★★".slice(0,starsArr[i]||0)+"☆☆☆".slice(0,3-(starsArr[i]||0)));
        svgEl.appendChild(t); });
      rsTtl.textContent="순행 완주"; rsHint.textContent="모든 구간의 보급선을 이었습니다";
      rsFoot.innerHTML="<button id='rsBack'>지도로 돌아가기</button><button class='primary' id='rsAgain'>다시 순행 →</button>";
      document.getElementById("rsAgain").onclick=function(){ location.reload(); };
      document.getElementById("rsBack").onclick=function(){ stage.classList.remove("show"); game.classList.remove("relaymode");
        var h="<div class='ohead'>역참로 완주</div><div class='stars'>"+tot+" / "+mx+" ★</div>";
        h+="<table class='legs'><tr><th>#</th><th>구간</th><th class='c'>별</th></tr>";
        legs.forEach(function(lg,i){ h+="<tr><td>"+(i+1)+"</td><td>"+lg[0]+"→"+lg[1]+"</td><td class='c'>"+(starsArr[i]||0)+"★</td></tr>"; });
        h+="</table>"; if(best>tot) h+="<div class='best'>최고 "+best+" / "+mx+" ★</div>";
        scoreEl2.innerHTML=h; scoreEl2.classList.add("show"); };
    }
    window.__startRelay=function(tour){ if(!tour||tour.length<2) return;
      legs=[]; for(var i=0;i<tour.length;i++) legs.push([tour[i], tour[(i+1)%tour.length]]);
      li=0; starsArr=[]; window.__relayActive=true;
      game.classList.add("relaymode"); stage.classList.add("show");
      loadLeg();   // 오프닝은 스토리 진입(로드) 시 시네마틱으로 재생 → 여기선 바로 첫 구간.
    };
  })();

  // ====== 오프닝 시네마틱 엔진: 전용 SVG에 '실제 지도'(제노바~대도 해안선)를 그리고 카메라로 연출 ======
  // 첫 화면: 제노바로 줌인 + 제노바만 활성(펄스) 노드 → 플레이어가 제노바를 클릭하면 독백(beat 0)부터 시작.
  // 이후 beats: 카메라가 focus 도시로 이동, "route"는 베네치아→대도 경로를 그려 보인다. 본 지도와 무관.
  // 지도 데이터 = openbuild.py 산출 OPENMAP(없으면 도식 폴백). 스테이지 좌표 = opSvg viewBox 1000×520.
  (function(){
    var opening=document.getElementById("opening"); if(!opening) return;
    var cam=document.getElementById("opCam"), opCard=opening.querySelector(".opCard"),
        opTag=document.getElementById("opTag"), opTtl=document.getElementById("opTtl"),
        opBody=document.getElementById("opBody"), opGo=document.getElementById("opGo");
    // 전면 낭독 뷰(긴 산문) 요소
    var opRead=document.getElementById("opRead"), opReadArt=document.getElementById("opReadArt"),
        opReadTag=document.getElementById("opReadTag"), opReadTtl=document.getElementById("opReadTtl"),
        opReadBody=document.getElementById("opReadBody"), opReadGo=document.getElementById("opReadGo");
    function showRead(b){   // beat 내러티브를 전면 낭독 뷰에 표시(지도 어둡게). 삽화칸=b.img 있으면 표시, 없으면 자리.
      opReadTag.textContent=b.tag||""; opReadTtl.textContent=b.title||"";
      opReadBody.innerHTML=""; (b.lines||[]).forEach(function(ln){ var pp=document.createElement("div"); pp.className="opLine"; pp.textContent=ln||""; opReadBody.appendChild(pp); });
      if(b.img){ opReadArt.style.backgroundImage="url('"+b.img+"')"; opReadArt.textContent=""; opReadArt.classList.add("hasimg"); }
      else { opReadArt.style.backgroundImage=""; opReadArt.textContent="삽 화 자 리"; opReadArt.classList.remove("hasimg"); }
      opReadGo.textContent=b.btn||"계속 →"; opReadInner_scrollTop();
      if(opCard) opCard.style.opacity="0"; opRead.classList.add("show"); }
    function hideRead(){ opRead.classList.remove("show"); if(opCard) opCard.style.opacity="1"; }
    function opReadInner_scrollTop(){ var inn=opRead&&opRead.querySelector(".opReadInner"); if(inn) inn.scrollTop=0; }
    var CXC=500, CYC=255, mk=el;
    var POS=(OPENMAP&&OPENMAP.nodes)||{ "제노바":{x:142,y:300,big:1}, "베네치아":{x:210,y:266,big:1},
      "콘스탄티노플":{x:340,y:300}, "바그다드":{x:440,y:334}, "사마르칸트":{x:560,y:250},
      "카슈가르":{x:660,y:262}, "카라코룸":{x:760,y:198}, "대도":{x:872,y:248,big:1} };
    var ROUTE=(OPENMAP&&OPENMAP.route)||["베네치아","콘스탄티노플","바그다드","사마르칸트","카슈가르","카라코룸","대도"];
    function smooth(pts){ if(pts.length<2) return ""; var d="M"+pts[0].x+","+pts[0].y;
      for(var i=0;i<pts.length-1;i++){ var p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;
        d+="C"+(p1.x+(p2.x-p0.x)/6)+","+(p1.y+(p2.y-p0.y)/6)+" "+(p2.x-(p3.x-p1.x)/6)+","+(p2.y-(p3.y-p1.y)/6)+" "+p2.x+","+p2.y; }
      return d; }
    var opSky=document.getElementById("opSky"), starfield=document.getElementById("opStarfield");
    var routeGold=null, caravan=null, built=false, routeOn=false, opLand=null, opCities=null, nodeG={}, OPENONLY={"제노바":1,"베네치아":1,"대도":1};
    function rngOpen(seed){ var s=(seed>>>0)||1; return function(){ s=(Math.imul(s,1664525)+1013904223)>>>0; return s/4294967296; }; }
    function setT(elm,op,dur){ if(!elm) return; elm.style.transition="opacity "+(dur||0.8)+"s ease"; elm.style.opacity=String(op); }
    // 별자리 → 지도: 하나의 일괄 크로스페이드. 하늘·별은 사라지고 지도는 떠오르며, 별 노드의 글로우도 같은 시간에 부드럽게 꺼진다.
    // night 클래스는 '끝'에서만 제거(즉시 제거 시 글로우·스타일이 따로 튀는 문제 해결). 모든 변화가 같은 dur로 동기화.
    function starToMap(dur, done){ dur=dur||3.4;
      // 글로우를 inline으로 고정 → night 제거해도 유지 → 같은 dur로 서서히 끔(팝 없음)
      var circs=cam.querySelectorAll("circle");
      [].forEach.call(circs, function(c){ c.style.filter="drop-shadow(0 0 2.5px #ffe7a6)"; });
      void cam.offsetWidth;                                  // reflow 후 transition 적용
      opening.classList.remove("night");
      [].forEach.call(circs, function(c){ c.style.transition="filter "+dur+"s ease"; c.style.filter="none"; });
      setT(opSky,0,dur); setT(starfield,0,dur); setT(opLand,1,dur);   // 하늘·별 ↓, 지도 ↑ — 동시
      if(done) setTimeout(done, dur*1000+120);
    }
    function build(){ if(built) return; built=true; cam.innerHTML="";
      // 배경 별무리(밤하늘 ambiance) — 한 번만 생성
      if(starfield && !starfield.childNodes.length){ var r=rngOpen(20260621);
        for(var s=0;s<64;s++) starfield.appendChild(mk("circle",{cx:(r()*1000).toFixed(1),cy:(r()*520).toFixed(1),r:(r()*1.2+0.3).toFixed(1),fill:"#fff",opacity:(r()*0.55+0.2).toFixed(2)})); }
      // 지도 레이어(클릭 시 페이드인): 바다 + 육지(해안선) + 호수
      opLand=mk("g",{}); opLand.setAttribute("id","opLand");
      // 파치먼트 시트를 깔아 바다가 '어둠'이 아니라 '양피지' 위에서 블렌드 → 기존 바다 색감 유지(배경은 어둠·레터박스 시네마틱).
      opLand.appendChild(mk("rect",{x:"-300",y:"-300",width:"1600",height:"1120",fill:"var(--parchment)"}));
      opLand.appendChild(mk("rect",{x:"-300",y:"-300",width:"1600",height:"1120",fill:"var(--sea)",opacity:"0.32"}));
      ((OPENMAP&&OPENMAP.land)||[]).forEach(function(d){ opLand.appendChild(mk("path",{d:d,fill:"var(--parchment)",stroke:"var(--ink-soft)","stroke-width":"0.6","stroke-linejoin":"round","stroke-linecap":"round"})); });
      ((OPENMAP&&OPENMAP.lakes)||[]).forEach(function(d){ opLand.appendChild(mk("path",{d:d,fill:"var(--sea)","fill-opacity":"0.75",stroke:"none"})); });
      cam.appendChild(opLand);
      // 75개 도시 노드('수많은 도시' 연출용) — 처음엔 숨김(opacity 0), 베네치아 이후 beat에서 페이드인
      opCities=mk("g",{}); opCities.setAttribute("id","opCities"); opCities.style.opacity="0";
      ((OPENMAP&&OPENMAP.cities)||[]).forEach(function(c){ opCities.appendChild(mk("circle",{cx:c.x,cy:c.y,r:"2.2",fill:"var(--ink-soft)",opacity:"0.7"})); });
      cam.appendChild(opCities);
      // 금색 애니 경로(대도 클릭 시 그려짐). 점선 가이드는 두지 않음 — 제노바·베네치아 장면에선 경로 미표시.
      var pts=ROUTE.map(function(n){return POS[n];}).filter(Boolean), dstr=smooth(pts);
      routeGold=mk("path",{d:dstr,fill:"none",stroke:"var(--gold)","stroke-width":"2.4",opacity:"0.95","stroke-linecap":"round","stroke-linejoin":"round"});
      cam.appendChild(routeGold);
      var L=routeGold.getTotalLength(); routeGold.setAttribute("stroke-dasharray",L); routeGold.setAttribute("stroke-dashoffset",L);
      caravan=mk("circle",{r:"4.5",fill:"var(--route)",opacity:"0"}); cam.appendChild(caravan);
      // 노드(별/도시) — 그룹별. 제노바·베네치아는 오프닝 전용(별자리·본 게임 지도엔 미표시).
      for(var n in POS){ var p=POS[n]; if(!p) continue;
        var g=mk("g",{}); nodeG[n]=g;
        var col=(n==="대도"?"var(--route)":(n==="제노바"?"#2f7a4f":"var(--gold)"));
        g.appendChild(mk("circle",{cx:p.x,cy:p.y,r:p.big?"4.5":"2.8",fill:col,stroke:"#fff","stroke-width":p.big?"1":"0.5"}));
        if(p.big){ var t=mk("text",{x:p.x,y:p.y-9,"text-anchor":"middle",style:"font-size:9px;font-weight:700;fill:var(--ink);"+LB}); t.textContent=n; g.appendChild(t); }
        cam.appendChild(g); }
    }
    var camS=1,camX=0,camY=0;
    function applyCam(){ cam.setAttribute("transform","translate("+camX+","+camY+") scale("+camS+")"); }
    function camTo(cx,cy,z,dur){ var s0=camS,x0=camX,y0=camY,nx=CXC-z*cx,ny=CYC-z*cy,t0=null; dur=(dur==null?900:dur);
      if(dur<=0){ camS=z;camX=nx;camY=ny;applyCam(); return; }
      function st(ts){ if(t0==null)t0=ts; var k=Math.min(1,(ts-t0)/dur), e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;
        camS=s0+(z-s0)*e; camX=x0+(nx-x0)*e; camY=y0+(ny-y0)*e; applyCam(); if(k<1) requestAnimationFrame(st); }
      requestAnimationFrame(st); }
    function animateRoute(onDone){ if(!routeGold||!routeOn){ if(onDone)onDone(); return; } var L=routeGold.getTotalLength(),t0=null,dur=1900,done=false;
      function fin(){ if(done) return; done=true; if(onDone) onDone(); }
      caravan.setAttribute("opacity","1");
      function st(ts){ if(!routeOn){ caravan.setAttribute("opacity","0"); fin(); return; }   // beat 넘어가면 중단
        if(t0==null)t0=ts; var k=Math.min(1,(ts-t0)/dur), e=1-Math.pow(1-k,2);
        routeGold.setAttribute("stroke-dashoffset", L*(1-e));
        var pt=routeGold.getPointAtLength(L*e); caravan.setAttribute("cx",pt.x); caravan.setAttribute("cy",pt.y);
        if(k<1) requestAnimationFrame(st); else { caravan.setAttribute("opacity","0"); fin(); } }
      requestAnimationFrame(st); }
    function zoomFor(n){ var p=POS[n]; if(!p) return [CXC,CYC,1.0]; return [p.x, p.y, p.big?3.2:2.6]; }
    function runBeats(beats, onDone){ var i=0;
      function advance(){ i++; if(i<beats.length) beat(); else { hideRead(); opening.classList.remove("show"); if(onDone) onDone(); } }
      function beat(){ var b=beats[i]||{}; routeOn=false;   // 매 beat 전환 시 경로 애니 중단
        if(window.__sfx) window.__sfx("page");   // 책 넘기는 소리(서사 카드 전환)
        showRead(b);   // 내러티브 = 전면 낭독 뷰(지도 어둡게, 중앙 큰 본문). 클릭 힌트만 하단 opCard.
        if(b.focus==="cities"){ camTo(500,235,1.0,1100); if(opCities) setT(opCities,1);
          if(routeGold) routeGold.setAttribute("stroke-dashoffset", routeGold.getTotalLength()); }   // 베네치아서 줌아웃 → 75개 도시 등장(경로는 대도 클릭 시)
        else if(b.focus==="route"){ camTo(CXC,235,1.0,900); if(routeGold){ routeGold.setAttribute("stroke-dashoffset", routeGold.getTotalLength()); routeOn=true; setTimeout(animateRoute,450); } }
        else { var z=zoomFor(b.focus); camTo(z[0],z[1],z[2],900); }
        opReadGo.onclick=function(){
          if(b.tutorial){ hideRead(); runTutorial(b.tutorial, b.tutorial_title||"첫 번째 여정", advance); return; }   // 노드 연결 튜토리얼
          if(b.next_node && nodeG[b.next_node]){   // 낭독 닫고(지도 밝게) 다음 노드 활성화(페이드+펄스) → 하단 힌트로 클릭 유도
            hideRead();
            opTag.textContent=""; opTtl.textContent="";
            opBody.innerHTML="<div class='opLine' style='text-align:center;color:var(--ink-soft)'>"+(b.next_hint||(b.next_node+"를 클릭하세요"))+"</div>";
            opGo.style.display="none"; if(opCard) opCard.style.opacity="1";
            if(b.focus && nodeG[b.focus]){   // 노드 포커스 beat: 떠나는 노드 페이드아웃 + 다음 노드로 카메라 센터링
              if(b.focus!==b.next_node) setT(nodeG[b.focus], 0);
              var zn=zoomFor(b.next_node); camTo(zn[0], zn[1], zn[2], 1100);
            }
            activateNode(b.next_node, function(){
              if(b.route_on_click && routeGold){   // 대도 클릭 후 노드를 잇는 경로 애니메이션 → 완료(또는 폴백)되면 진행
                var adv=false; function go(){ if(adv) return; adv=true; if(routeGold) routeGold.setAttribute("stroke-dashoffset", 0); advance(); }
                routeGold.setAttribute("stroke-dashoffset", routeGold.getTotalLength()); routeOn=true; animateRoute(go);
                setTimeout(go, 2600);
              } else advance();
            });
          } else advance();   // 순수 내러티브 → 다음 beat가 낭독 뷰 갱신(닫지 않음, 깜빡임 방지)
        };
      }
      beat();
    }
    // 노드 활성화: 페이드 인 + 펄스 링 + 클릭 히트영역. 클릭 시 cb().
    function activateNode(name, cb){ var g=nodeG[name], p=POS[name]; if(!g||!p){ cb(); return; }
      setT(g,1,1.0);   // 노드가 천천히 '떠오르며' 등장(시선 유도)
      var pulse=mk("circle",{cx:p.x,cy:p.y,r:"6",fill:"none",stroke:"var(--gold)","stroke-width":"1.5"});
      pulse.appendChild(mk("animate",{attributeName:"r",values:"5;12;5",dur:"1.4s",repeatCount:"indefinite"}));
      pulse.appendChild(mk("animate",{attributeName:"opacity",values:"1;0;1",dur:"1.4s",repeatCount:"indefinite"}));
      g.appendChild(pulse);
      var hit=mk("circle",{cx:p.x,cy:p.y,r:"16",fill:"transparent"}); hit.style.cursor="pointer";
      hit.addEventListener("click",function(){ if(pulse.parentNode)pulse.parentNode.removeChild(pulse); if(hit.parentNode)hit.parentNode.removeChild(hit); cb(); });
      g.appendChild(hit);
    }
    // 노드 연결 튜토리얼: route의 도시를 하나씩 '떠오르게' + 클릭 유도 → 직전 지점에서 이동 애니메이션으로 잇는다.
    // (베네치아→대도 첫 여행 = 역참로 잇기 메커닉 튜토리얼). 도시 좌표는 OPENMAP.cities(75개)에서 이름으로 조회.
    function runTutorial(names, title, onDone){
      var tutorG=mk("g",{}); cam.appendChild(tutorG);
      var prev=POS["베네치아"]||{x:CXC,y:CYC}, i=0;
      function cityPos(nm){ var cs=(OPENMAP&&OPENMAP.cities)||[]; for(var j=0;j<cs.length;j++) if(cs[j].n===nm) return cs[j]; return null; }
      function travel(a,b,cb){   // a→b 이동 애니메이션(부드러운 곡선이 자라며 카라반 이동), 완료 후 cb. 곡선은 남아 경로 누적.
        var dx=b.x-a.x, dy=b.y-a.y, len=Math.hypot(dx,dy)||1;
        var cx=(a.x+b.x)/2 - dy/len*len*0.14, cy=(a.y+b.y)/2 + dx/len*len*0.14;   // 수직으로 살짝 휜 제어점
        var pth=mk("path",{d:"M"+a.x+","+a.y+" Q"+cx.toFixed(1)+","+cy.toFixed(1)+" "+b.x+","+b.y,
          fill:"none",stroke:"var(--gold)","stroke-width":"2.4","stroke-linecap":"round","stroke-linejoin":"round"});
        tutorG.insertBefore(pth, tutorG.firstChild);   // 경로는 노드 아래
        var L=pth.getTotalLength(); pth.setAttribute("stroke-dasharray",L); pth.setAttribute("stroke-dashoffset",L);
        caravan.setAttribute("opacity","1"); var t0=null,dur=1100,done=false;
        function fin(){ if(done)return; done=true; pth.setAttribute("stroke-dashoffset",0); caravan.setAttribute("opacity","0"); cb(); }
        function st(ts){ if(t0==null)t0=ts; var k=Math.min(1,(ts-t0)/dur), e=1-Math.pow(1-k,2);
          pth.setAttribute("stroke-dashoffset", L*(1-e));
          var pt=pth.getPointAtLength(L*e); caravan.setAttribute("cx",pt.x); caravan.setAttribute("cy",pt.y);
          if(k<1) requestAnimationFrame(st); else fin(); }
        requestAnimationFrame(st); setTimeout(fin, dur+600);   // rAF 일시정지 폴백
      }
      function step(){
        if(i>=names.length){ if(onDone) onDone(); return; }
        var nm=names[i], p=cityPos(nm);
        if(!p){ i++; step(); return; }
        opTag.textContent=title||"첫 번째 여정"; opTtl.textContent="";
        opBody.innerHTML="<div class='opLine' style='text-align:center;color:var(--ink-soft)'><b>"+nm+"</b> — 클릭해 길을 이으시오 ("+(i+1)+" / "+names.length+")</div>";
        opGo.style.display="none";
        var g=mk("g",{}); g.style.opacity="0"; var big=(nm==="대도");
        g.appendChild(mk("circle",{cx:p.x,cy:p.y,r:big?"5.5":"4.5",fill:big?"var(--route)":"var(--gold)",stroke:"#fff","stroke-width":"1"}));
        var t=mk("text",{x:p.x,y:p.y-9,"text-anchor":"middle",style:"font-size:11px;font-weight:700;fill:var(--ink);"+LB}); t.textContent=nm; g.appendChild(t);
        var pulse=mk("circle",{cx:p.x,cy:p.y,r:"6",fill:"none",stroke:"var(--gold)","stroke-width":"1.5"});
        pulse.appendChild(mk("animate",{attributeName:"r",values:"5;13;5",dur:"1.4s",repeatCount:"indefinite"}));
        pulse.appendChild(mk("animate",{attributeName:"opacity",values:"1;0;1",dur:"1.4s",repeatCount:"indefinite"}));
        g.appendChild(pulse);
        var hit=mk("circle",{cx:p.x,cy:p.y,r:"17",fill:"transparent"}); hit.style.cursor="pointer";
        hit.addEventListener("click",function(){ if(pulse.parentNode)pulse.parentNode.removeChild(pulse); if(hit.parentNode)hit.parentNode.removeChild(hit);
          if(window.__sfx) window.__sfx("select");
          travel(prev, p, function(){ prev=p; i++; step(); }); });
        g.appendChild(hit); tutorG.appendChild(g);
        setT(g,1,0.8);   // 도시가 떠오름(페이드인)
      }
      step();
    }
    // 샌드박스 진입: 별→지도 전환 후 오버레이 닫아 본 게임(몽골 제국) 지도 표시.
    function startSandbox(){ try{ localStorage.setItem("mongolEntered","sandbox"); }catch(e){}
      __pageBg(false);   // 페이지 배경 밤하늘 해제
      if(opCard){ opCard.style.transition="opacity .5s"; opCard.style.opacity="0"; }   // 모드 선택 카드 사라짐
      starToMap(3.4, function(){ opening.classList.remove("show"); });   // 별→지도 일괄 전환 후 오버레이 닫기
    }
    // 스토리 진입: 메인 지도를 폴로로 교체 + 별→지도 → 1초 후 제노바 줌인 → 독백 beats → 대도서 줌아웃 리빌.
    function startStory(S){ if(window.__applyStory) window.__applyStory(S);
      var mapSvg=document.getElementById("map"), st=byName[(S&&S.start)||"대도"]||byName["대도"];
      mapSvg.classList.add("storyintro"); if(st && window.__focus) window.__focus(st.x-66,st.y-46,st.x+66,st.y+46,0);
      function reveal(){ if(window.__resetView) window.__resetView(1000); setTimeout(function(){ mapSvg.classList.remove("storyintro"); },100); }
      // 별→지도 전환을 하나의 일괄 크로스페이드로(3.4s) — 별이 도시로 바뀌는 메타포. 끝나면 제노바로 시선 유도.
      __pageBg(false);   // 페이지 배경 밤하늘 해제(복귀)
      if(opCard){ opCard.style.transition="opacity .5s"; opCard.style.opacity="0"; }   // 모드 선택 카드 사라짐
      var beats=(S&&S.scenario&&S.scenario.opening&&S.scenario.opening.beats)||[];
      starToMap(3.4, function(){   // 전환 완료 후: 제노바가 '떠오르고' 카메라가 그쪽으로 유도 → 클릭
        if(opCard){ opCard.style.transition="opacity .6s"; opCard.style.opacity="1"; }   // 카드 복귀(독백 안내)
        var gp=POS["제노바"]; if(gp) camTo(gp.x, gp.y, 2.2, 1400);   // 제노바로 부드럽게 시선 유도(activateNode가 천천히 떠올림)
        opTag.textContent=""; opTtl.textContent="";
        opBody.innerHTML="<div class='opLine' style='text-align:center;color:var(--ink-soft)'>제노바를 클릭해 이야기를 시작하세요</div>";
        opGo.style.display="none";
        if(typeof activateNode==="function") activateNode("제노바", function(){ runBeats(beats, reveal); });
        else runBeats(beats, reveal);
      });
    }
    // 인게임 타이틀(별자리): 스토리 / 샌드박스 선택.
    window.__runTitle=function(S){
      opening.classList.add("show"); opening.classList.add("night"); build();
      __pageBg(true);   // 타이틀: 페이지 배경까지 밤하늘로
      camTo(CXC, CYC, 1.0, 0);
      setT(opSky,1); setT(starfield,1); setT(opLand,0);
      for(var k in OPENONLY) if(nodeG[k]) setT(nodeG[k],0);   // 제노바·베네치아 숨김(별자리엔 없음)
      opTag.textContent="1275 · 팍스 몽골리카"; opTtl.textContent="칸이 명한 순행로";
      opBody.innerHTML="<div class='opLine' style='text-align:center;color:#c7d0ec;margin:2px 0 11px;font-size:13px'>유라시아를 잇는 순행에 오르라 — 모드를 선택하세요</div>"+
        "<div style='display:flex;gap:14px;justify-content:center;flex-wrap:wrap'>"+
        "<button class='opGo titlechoice' id='tStory'>📖 스토리<span>마르코 폴로의 순행</span></button>"+
        "<button class='opGo titlechoice' id='tSand' style='background:rgba(255,255,255,.14);color:#eee4cf;border-color:#9aa4c0'>🎲 샌드박스<span>자유롭게 도시를 잇다</span></button></div>";
      opGo.style.display="none";
      document.getElementById("tStory").onclick=function(){ if(window.__sfx) window.__sfx("select"); __unlock(); startStory(S); };
      document.getElementById("tSand").onclick=function(){ if(window.__sfx) window.__sfx("select"); __unlock(); startSandbox(); };
    };
  })();

  // ====== 인게임 타이틀 진입: 별자리 → [스토리 / 샌드박스] ======
  (function(){
    var tb=document.getElementById("toTitle");
    if(tb) tb.onclick=function(){ try{ localStorage.removeItem("mongolEntered"); }catch(e){} location.reload(); };
    var entered=null; try{ entered=localStorage.getItem("mongolEntered"); }catch(e){}
    if(entered==="sandbox") return;   // 샌드박스 진입 후 리런 → 타이틀 건너뜀(사이드바 조정 끊김 방지)
    if(STORY && OPENMAP && OPENMAP.nodes && window.__runTitle) window.__runTitle(STORY);
  })();
</script></body></html>"""
