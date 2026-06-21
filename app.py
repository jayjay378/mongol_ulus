# -*- coding: utf-8 -*-
"""칸이 명한 순행로 — Streamlit 앱.
사이드바에서 순행 도시를 고르고(무작위 선택 지원), Python이 경로를 최적화
(고전/Brute/양자)해 SVG 고지도에 주입해 그린다. 단방향 흐름."""
import json, os, random
import streamlit as st
import streamlit.components.v1 as components

from solver import solve_classical, solve_bruteforce, solve_qaoa
from map_view import build_map
import terrain

HERE = os.path.dirname(__file__)
DATA = json.load(open(os.path.join(HERE, "map_data.json"), encoding="utf-8"))
CITIES = DATA["cities"]; GHOSTS = DATA["ghosts"]
_geo_path = os.path.join(HERE, "geo.json")
GEO = json.load(open(_geo_path, encoding="utf-8")) if os.path.exists(_geo_path) else {}
# iframe엔 그릴 것만(해안선·강·호수). 바다 마스크 비트(수십 KB)는 Python(terrain)만 쓰므로 제외.
GEO_VIEW = {k: GEO[k] for k in ("land", "lakes", "rivers", "heat", "yampaths") if k in GEO}
_info_path = os.path.join(HERE, "cities_info.json")
CITY_INFO = json.load(open(_info_path, encoding="utf-8")) if os.path.exists(_info_path) else {}
_pedia_path = os.path.join(HERE, "pedia.json")
PEDIA = json.load(open(_pedia_path, encoding="utf-8")) if os.path.exists(_pedia_path) else {}
# 도착 연출(스토리 모드): 역참 미니게임으로 도시에 도착하면 그 도시의 풍경 장면을 보여준다.
_scenes_path = os.path.join(HERE, "city_scenes.json")
try:
    CITY_SCENES = json.load(open(_scenes_path, encoding="utf-8")).get("scenes", {}) if os.path.exists(_scenes_path) else {}
except Exception:
    CITY_SCENES = {}
# 오프닝 전용 실제 지도(제노바~대도 해안선·노드). openbuild.py 산출물. 메인 지도와 무관.
_openmap_path = os.path.join(HERE, "opening_map.json")
OPENING_MAP = json.load(open(_openmap_path, encoding="utf-8")) if os.path.exists(_openmap_path) else {}
# 순행 임무(시나리오): 있으면 사이드바에서 골라 config를 고정하고 별점으로 채점. 없으면 자유 순행만.
_scen_path = os.path.join(HERE, "scenarios.json")
try:
    SCENARIOS = json.load(open(_scen_path, encoding="utf-8")).get("scenarios", []) if os.path.exists(_scen_path) else []
except Exception:
    SCENARIOS = []
SCEN_BY_TITLE = {s.get("title", ""): s for s in SCENARIOS}
NAMES = [c["n"] for c in CITIES]
BY = {c["n"]: c for c in CITIES}

def rotate_to(route, start):
    """순회를 시작 도시가 맨 앞에 오도록 회전(왕복이라 길이는 불변)."""
    if start in route:
        i = route.index(start); return route[i:] + route[:i]
    return route

st.set_page_config(page_title="칸이 명한 순행로", layout="wide")

# 리런(특히 수십 초 걸리는 양자 계산) 중에도 지도·백과사전을 흐려지지 않고 그대로 보고 만질 수 있게.
# 지도 iframe을 담은 컨테이너만 페이드/잠금 해제 — 경고 등 다른 요소는 Streamlit 기본대로(중복 방지).
st.markdown(
    "<style>[data-testid=\"stElementContainer\"]:has(iframe){opacity:1 !important;pointer-events:auto !important;}"
    "iframe{opacity:1 !important;pointer-events:auto !important;}</style>",
    unsafe_allow_html=True)

ss = st.session_state
if "route" not in ss:
    ss["route"] = []; ss["msg"] = None
if "sel" not in ss:
    # 기본 8도시(서향 실크로드). 측정상 4도시는 탐욕법=최적이라 너무 쉽고,
    # 인간 vs 컴퓨터 격차는 8~12도시에서 의미가 생긴다(난이도 곡선).
    ss["sel"] = ["대도", "상도", "카라코룸", "알말리크", "사마르칸트", "부하라", "헤라트", "바그다드"]

with st.sidebar:
    st.header("칸의 명")
    st.caption("🎲 스토리 / 샌드박스 **모드는 첫 화면(별자리)에서 선택**합니다. 아래는 샌드박스 설정입니다.")
    scen = None   # 모드 선택은 인게임 타이틀로 이전 — 사이드바는 샌드박스 조정용.
    # ── 샌드박스(자유 순행) 컨트롤 (스토리 설정은 scenarios.json에서 고정·아래 STORY로 주입) ──
    count = st.slider("순행 도시 수", 2, 30, 8)
    st.caption("8~12개에서 인간의 직관과 컴퓨터 해법의 격차가 가장 큽니다.")
    if st.button("🎲 무작위로 도시 뽑기", use_container_width=True):
        ss["sel"] = random.sample(NAMES, count)
        ss["force_mode"] = "draw"   # 무작위로 뽑으면 즉시 순행 그리기 모드로
    sel = st.multiselect("순행할 도시", NAMES, key="sel")

    method = st.radio("해법", ["고전 (NN + 2-opt)", "Brute Force (정답)", "양자 (QAOA)"])
    if method.startswith("양자"):
        st.caption("도시 4개까지만 (큐비트 = 도시² — 배포 메모리 안전). '순행 그리기'에서 채점 시 자동 실행.")
        reps = st.slider("QAOA 레이어 (reps)", 1, 4, 2)
        maxiter = st.slider("옵티마이저 반복", 20, 300, 100, 20)
    else:
        reps, maxiter = 2, 100
    st.caption("해답은 채점할 때 자동 계산되어 공개됩니다.")
    st.divider()
    terrain_on = st.checkbox("지형 비용 (산·사막·고원)")
    if terrain_on:
        omode = st.selectbox("순행 주체", terrain.MODE_LIST,
                             index=terrain.MODE_LIST.index(terrain.DEFAULT_MODE))
        st.caption(terrain.MODE_DESC.get(omode, ""))
        opriority = st.radio("우선순위", terrain.PRIORITY_LIST, horizontal=True)
        oseason = st.selectbox("계절", terrain.SEASON_LIST, index=0)
        st.caption("거리≠시간≠비용 — 누가·어떤 우선순위·어느 계절에 가느냐로 최적 경로가 달라집니다.")
    else:
        omode, opriority, oseason = terrain.DEFAULT_MODE, terrain.DEFAULT_PRIORITY, terrain.DEFAULT_SEASON
    show_ghosts = st.checkbox("보이지 않는 도시들")
    start = "대도" if "대도" in sel else (sel[0] if sel else None)

@st.cache_data(show_spinner=False)
def _lcp(coords_t, terrain_on, mode, priority, season):
    """지형 ON: 격자 최소비용(선택지표 C, 곡선 경로, 3지표). OFF: (None,{},{}). 선택/수단/우선순위/계절 바뀔 때만."""
    if not terrain_on:
        return None, {}, {}
    return terrain.least_cost(list(coords_t), mode=mode, priority=priority, season=season)

@st.cache_data(show_spinner=False)
def _qaoa(coords_t, reps, maxiter, terrain_on, mode, priority, season):
    C, _, _ = _lcp(coords_t, terrain_on, mode, priority, season)
    return solve_qaoa(list(coords_t), reps=reps, maxiter=maxiter, C=C)

@st.cache_data(show_spinner=False)
def _story_bundle(scen_json):
    """스토리(폴로) 모드 전체 설정을 미리 계산해 iframe에 통째로 주입(인게임 타이틀에서 전환).
    공정 채점=Brute(≤9)·아니면 고전. scen_json(고정 문자열)로 캐시 → 1회만 계산."""
    scen = json.loads(scen_json)
    sel = [c for c in scen.get("cities", []) if c in BY]
    _st = scen.get("start"); start = _st if _st in sel else (sel[0] if sel else None)
    terrain_on = bool(scen.get("terrain"))
    omode = scen.get("persona", terrain.DEFAULT_MODE)
    opriority = scen.get("priority", terrain.DEFAULT_PRIORITY)
    oseason = scen.get("season", terrain.DEFAULT_SEASON)
    answer = {"route": [], "len": 0, "label": ""}; costs, paths, metrics3, cr = {}, {}, {}, {}
    cart_center = None
    if len(sel) >= 2:
        coords = [(BY[n]["x"], BY[n]["y"]) for n in sel]; ct = tuple(coords)
        C, lcp_paths, lcp_metrics = _lcp(ct, terrain_on, omode, opriority, oseason)
        if len(sel) <= 9:
            order, L, _ = solve_bruteforce(coords, C); label = "정답"
        else:
            order, L, _ = solve_classical(coords, C); label = "고전"
        answer = {"route": rotate_to([sel[i] for i in order], start), "len": L, "label": label}
        if terrain_on and C is not None:
            costs = {sel[i]: {sel[j]: float(C[i][j]) for j in range(len(sel))} for i in range(len(sel))}
            for (i, j), pts in lcp_paths.items():
                paths["|".join(sorted([sel[i], sel[j]]))] = pts
            for (i, j), (km, days, coin) in lcp_metrics.items():
                metrics3["|".join(sorted([sel[i], sel[j]]))] = [round(km), round(days, 1), round(coin)]
    if terrain_on:
        cart_center = "대도" if "대도" in BY else start
        if cart_center and cart_center in BY:
            cc = BY[cart_center]
            cr = terrain.cost_from_center((cc["x"], cc["y"]), CITIES, mode=omode, priority=opriority, season=oseason)
    orbis = {"mode": omode, "priority": opriority, "season": oseason,
             "unit": terrain.METRIC_UNIT.get(opriority, ""), "pxkm": terrain.PXKM} if terrain_on else None
    scenario_meta = {"id": scen.get("id"), "title": scen.get("title"),
                     "khan_command": scen.get("khan_command", ""), "stars": scen.get("stars", [5, 15, 30]),
                     "lore": scen.get("lore", ""), "scenes": scen.get("scenes", {}),
                     "opening": scen.get("opening"), "closing": scen.get("closing")}
    return {"sel": sel, "start": start, "terrain": terrain_on, "answer": answer, "costs": costs,
            "paths": paths, "metrics": metrics3, "cr": cr, "cart_center": cart_center,
            "orbis": orbis, "scenario": scenario_meta}

STORY = _story_bundle(json.dumps(SCENARIOS[0], ensure_ascii=False)) if SCENARIOS else None

# 답안은 매 렌더 자동 계산되어 (숨겨진 채) 주입된다. 채점(iframe) 시 공개 → 별도 버튼 불필요.
# 지형 ON이면 비용·경로 모두 '격자 최소비용'(지형 따라 굽는 경로)으로 일관. 고전/Brute 즉시, QAOA ≤5.
answer = {"route": [], "len": 0, "label": ""}
note = None
costs, cr, cart_center, paths, metrics3 = {}, {}, None, {}, {}
if len(sel) >= 2:
    coords = [(BY[n]["x"], BY[n]["y"]) for n in sel]; ct = tuple(coords)
    C, lcp_paths, lcp_metrics = _lcp(ct, terrain_on, omode, opriority, oseason)
    order = None; L = 0; label = ""
    if scen:
        # 임무는 공정한 '정답'으로 채점: Brute(≤9)·아니면 고전.
        if len(sel) <= 9:
            order, L, _ = solve_bruteforce(coords, C); label = "정답"
        else:
            order, L, _ = solve_classical(coords, C); label = "고전"
    elif method.startswith("고전"):
        order, L, _ = solve_classical(coords, C); label = "고전"
    elif method.startswith("Brute"):
        if len(sel) <= 9:
            order, L, _ = solve_bruteforce(coords, C); label = "Brute Force"
        else:
            order, L, _ = solve_classical(coords, C); label = "고전(대체)"
            note = ("info", "Brute Force는 9개 이하만 가능 — 고전 해로 대체합니다.")
    else:  # 양자 (QAOA)
        label = "QAOA"
        if len(sel) > 4:
            note = ("warning", "양자(QAOA)는 4개 이하만 — 도시 수를 줄이세요 (큐비트 = 도시², 배포 메모리 한계).")
        else:
            with st.spinner("QAOA 시뮬레이션 중... (도시 수에 따라 수십 초)"):
                order, info = _qaoa(ct, reps, maxiter, terrain_on, omode, opriority, oseason)
            if order is None:
                note = ("warning", info.get("note") or info.get("error", "양자 해 실패 — reps/maxiter를 올려보세요."))
            else:
                L = info.get("length", 0)
    if order is not None:
        answer = {"route": rotate_to([sel[i] for i in order], start), "len": L, "label": label}
    # 플레이어 채점(선택지표)용 비용 dict + 곡선 경로 + 구간별 3지표(거리·시간·비용) 주입
    if terrain_on and C is not None:
        costs = {sel[i]: {sel[j]: float(C[i][j]) for j in range(len(sel))} for i in range(len(sel))}
        for (i, j), pts in lcp_paths.items():
            paths["|".join(sorted([sel[i], sel[j]]))] = pts
        for (i, j), (km, days, coin) in lcp_metrics.items():
            metrics3["|".join(sorted([sel[i], sel[j]]))] = [round(km), round(days, 1), round(coin)]

if note:
    getattr(st, note[0])(note[1])

if terrain_on:
    cart_center = "대도" if "대도" in BY else start
    if cart_center and cart_center in BY:
        cc = BY[cart_center]
        cr = terrain.cost_from_center((cc["x"], cc["y"]), CITIES + (GHOSTS if show_ghosts else []),
                                      mode=omode, priority=opriority, season=oseason)

orbis = {"mode": omode, "priority": opriority, "season": oseason,
         "unit": terrain.METRIC_UNIT.get(opriority, ""), "pxkm": terrain.PXKM} if terrain_on else None
scenario_meta = {"id": scen.get("id"), "title": scen.get("title"),
                 "khan_command": scen.get("khan_command", ""),
                 "stars": scen.get("stars", [5, 15, 30]),
                 "lore": scen.get("lore", ""),
                 "scenes": scen.get("scenes", {}),       # 도시별 도착 연출 덮어쓰기(선택)
                 "opening": scen.get("opening"),          # 여정 시작 오프닝 연출
                 "closing": scen.get("closing")} if scen else None   # 귀환 후 '칸께 고하다' 연출
force_mode = ss.pop("force_mode", None)   # 무작위 뽑기·임무 시작 직후 1회만 모드 강제
html = build_map(CITIES, GHOSTS, sel, answer, start=start, show_ghosts=show_ghosts,
                 terrain=terrain_on, costs=costs,
                 barriers=(terrain.BARRIERS if terrain_on else []), cr=cr, cart_center=cart_center,
                 geo=GEO_VIEW, info=CITY_INFO, pedia=PEDIA, paths=paths, force_mode=force_mode,
                 metrics=metrics3, orbis=orbis, scenario=scenario_meta, city_scenes=CITY_SCENES,
                 opening_map=OPENING_MAP, story=STORY)
components.html(html, height=760, scrolling=False)

cap = "지도 상단 토글 — ‘탐험’은 도시를 눌러 역사 설명을, ‘순행 그리기’는 강조 도시를 순서대로 눌러 순행로를 작성한 뒤 ‘채점’합니다. "
cap += ("거리가 아니라 지형 이동 비용 기준 — 산·사막을 넘는 길이 비쌉니다." if terrain_on
        else "거리는 실제 지리 좌표 기준.")
st.caption(cap)
