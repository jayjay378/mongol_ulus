# -*- coding: utf-8 -*-
"""지형 이동 비용 + ORBIS식 다지표(거리·시간·비용 × 이동수단 × 계절).

geobuild.py가 실제 DEM에서 난이도를 두 성분으로 분리해 geo.json에 굽는다:
  mtn(경사+고도=산악 험준함), des(건조=사막). 통행 마스크(sea=바다+제국밖)도 함께.
여기서는 그 성분을 이동수단·계절·우선순위에 따라 다르게 가중해 격자 최소비용 경로를 낸다.
ORBIS 명제 "거리 ≠ 시간 ≠ 비용": 시간은 산악에 민감, 비용은 사막(보급·물)에 민감하므로
최속/최저비용/최단이 서로 다른 경로가 되고, 이동수단의 지형 적성이 경로를 또 바꾼다."""
import math, os, json, heapq, base64
import numpy as np

def _load_geo():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo.json")
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}

_GEO = _load_geo()
BARRIERS = _GEO.get("barriers", []) or []
_SEA = _GEO.get("sea") or None
_META = _GEO.get("meta") or {}
SEA_BLOCK = 1.0e6   # 통행불가 셀 진입 페널티(사실상 차단)

# ---- 격자 차원·영역 = 통행 마스크와 일치 ----
if _SEA:
    _GW, _GH = _SEA["w"], _SEA["h"]
    _GX0, _GX1, _GY0, _GY1 = _SEA["x0"], _SEA["x1"], _SEA["y0"], _SEA["y1"]
    _SEABITS = _SEA["bits"]
else:
    _GW, _GH = 232, 140
    _GX0, _GX1, _GY0, _GY1 = 38, 1242, 106, 708
    _SEABITS = None
_CW = (_GX1 - _GX0) / _GW; _CH = (_GY1 - _GY0) / _GH
_YAMBITS = (_GEO.get("yam") or {}).get("bits")   # 역참 도로 비트(yam 격자=sea 격자와 동일 차원). 엘치 시간 할인용.

# ---- 난이도 두 성분 디코드 (base64) ----
def _decode(d):
    return (base64.b64decode(d["b64"]), float(d["scale"])) if d else (None, 1.0)
_MTNB, _MTNS = _decode(_GEO.get("mtn"))
_DESB, _DESS = _decode(_GEO.get("des"))
def _mtn(i, j): return _MTNB[i * _GH + j] / _MTNS if _MTNB else 0.0
def _des(i, j): return _DESB[i * _GH + j] / _DESS if _DESB else 0.0

# ---- 투영 메타: 거리 환산(km/px = 111/S)·행별 위도(겨울 북방 한파용) ----
_PROJ = _META.get("proj", [0.0, 0.0, 12.9, 1.0, 0.0, 60.0])
_OY, _S, _LAT1 = _PROJ[1], (_PROJ[2] or 12.9), _PROJ[5]
PXKM = 111.0 / _S
def _rowlat(j):
    return _LAT1 - ((_GY0 + (j + 0.5) * _CH) - _OY) / _S

# ---- ORBIS 파라미터 ----
# 지표 가중: 시간은 산악에 민감(MT>DT), 비용은 사막에 민감(DC>MC).
MT, DT = 1.0, 0.55       # 산악→시간, 사막→시간
MC, DC = 0.55, 1.0       # 산악→비용, 사막→비용
# 순행 주체(persona): 이동수단이 아니라 '누가 가는가'. ORBIS식으로 각 집단이 지형·계절에
# 다르게 반응 → 최적 경로(순서까지)가 갈린다. 핵심 설계: 오르톡(사막강세·산약점)과
# 포로단(산 상대강세·사막약점)의 적성을 반대로 벌려 순열 자체가 달라지게, 관료단은 둘 다 회피.
#   speed(km/일), rate(비용/km), 지형 적성(1=중립·<1 강세·>1 약점): mtnT,desT,mtnC,desC,
#   seasonSens(계절 민감도: 1=표준, >1 악천후에 더 취약 — 계절 스윙을 증폭)
# yamSpeed: 역참 도로 위 셀의 시간비용 배율(<1=빨라짐). 엘치는 환마로 도로 위에서만 압도적,
#   벗어나면 일반 기수 속도. 다른 주체는 도로 혜택이 작다(자기 보속·지형 논리가 지배).
MODES = {
    # 황제의 역참(yam) 특사: 역참 환마 → *도로 위에서만* 압도적 속도(off-road는 일반 기수 ~80km/일). 비용 막대.
    "엘치":   dict(speed=80.0,  rate=13.0, mtnT=1.7, desT=1.1, mtnC=1.5, desC=1.2, seasonSens=1.1, yamSpeed=0.32),
    # 제국 공인 대상 길드(ortogh): 낙타 상단. 사막 관통 강세·산악 약점. 연중 운행이라 계절에 둔감.
    "오르톡": dict(speed=30.0,  rate=2.5,  mtnT=1.6, desT=0.4, mtnC=1.4, desC=0.4, seasonSens=0.8, yamSpeed=0.9),
    # 칸의 호구 조사 관료단: 장부·서기·호위·문서함 대동. 산·사막 모두 최악, 악천후에 가장 취약.
    "관료단": dict(speed=40.0,  rate=5.0,  mtnT=2.1, desT=1.7, mtnC=1.8, desC=1.6, seasonSens=1.7, yamSpeed=0.85),
    # 강제 이주 기술자·포로 집단: 도보. 산은 상대적으로 통과(고개)·사막은 가혹. 최저 비용, 겨울 노출에 취약.
    "포로단": dict(speed=15.0,  rate=1.0,  mtnT=1.25, desT=1.5, mtnC=1.15, desC=1.4, seasonSens=1.5, yamSpeed=0.95),
}
# 순행 주체 한 줄 설명(사이드바 캡션·교육용)
MODE_DESC = {
    "엘치":   "역참 환마로 달리는 황제의 특사 — 압도적 속도, 막대한 비용. 산악엔 느려짐.",
    "오르톡": "제국 공인 대상 길드의 낙타 상단 — 사막을 관통, 산악은 약점. 연중 운행.",
    "관료단": "호구를 조사하는 관료단 — 장부·서기·호위를 거느려 느리고, 험지·악천후에 가장 취약.",
    "포로단": "강제 이주당하는 기술자·포로 — 도보라 산은 넘되 사막은 가혹. 가장 싸지만 겨울에 취약.",
}
# 계절: 성분 스케일 + 겨울 북방 한파(cold). 각 주체의 seasonSens가 이 스윙을 증폭/완화.
SEASONS = {
    "봄":   dict(mtn=1.0,  des=1.0,  cold=0.0),
    "여름": dict(mtn=0.95, des=1.6,  cold=0.0),
    "가을": dict(mtn=1.0,  des=1.05, cold=0.0),
    "겨울": dict(mtn=1.6,  des=0.85, cold=1.4),
}
MODE_LIST = ["엘치", "오르톡", "관료단", "포로단"]
PRIORITY_LIST = ["최속", "최저비용", "최단"]
SEASON_LIST = ["봄", "여름", "가을", "겨울"]
# 기본 주체=관료단: 플레이어 페르소나(칸의 순회 감찰관)에 가장 가깝고, 지형·계절에 가장 민감해
# 지형비용 모드의 효과를 가장 잘 드러낸다.
DEFAULT_MODE, DEFAULT_PRIORITY, DEFAULT_SEASON = "관료단", "최속", "봄"
METRIC_UNIT = {"최속": "일", "최저비용": "관", "최단": "km"}   # 결과표 단위

# ---- 격자 헬퍼 ----
def _cellxy(i, j): return (_GX0 + (i + 0.5) * _CW, _GY0 + (j + 0.5) * _CH)
def _to_cell(x, y):
    return (min(_GW - 1, max(0, int((x - _GX0) / (_GX1 - _GX0) * _GW))),
            min(_GH - 1, max(0, int((y - _GY0) / (_GY1 - _GY0) * _GH))))
def _is_water(i, j): return _SEABITS is not None and _SEABITS[i * _GH + j] == "1"
def _is_road(i, j): return _YAMBITS is not None and _YAMBITS[i * _GH + j] == "1"
def _land_cell(i, j):
    if not _is_water(i, j): return (i, j)
    for r in range(1, 12):
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                ni, nj = i + di, j + dj
                if 0 <= ni < _GW and 0 <= nj < _GH and not _is_water(ni, nj):
                    return (ni, nj)
    return (i, j)

# 수단×계절별 시간·비용 배율(셀당), 캐시
_MULT_CACHE = {}
def _mults(mode, season):
    key = (mode, season)
    if key not in _MULT_CACHE:
        M = MODES.get(mode, MODES[DEFAULT_MODE]); S = SEASONS.get(season, SEASONS[DEFAULT_SEASON])
        # seasonSens: 계절 스윙(봄=1 기준의 편차)과 한파를 주체별로 증폭/완화.
        sens = M.get("seasonSens", 1.0)
        smtn = 1.0 + (S["mtn"] - 1.0) * sens; sdes = 1.0 + (S["des"] - 1.0) * sens
        cold = [S["cold"] * sens * max(0.0, (_rowlat(j) - 45.0) / 12.0) for j in range(_GH)]
        tm = [[0.0] * _GH for _ in range(_GW)]; cm = [[0.0] * _GH for _ in range(_GW)]
        for i in range(_GW):
            for j in range(_GH):
                m = _mtn(i, j) * smtn + cold[j]; d = _des(i, j) * sdes
                tm[i][j] = 1.0 + m * MT * M["mtnT"] + d * DT * M["desT"]
                cm[i][j] = 1.0 + m * MC * M["mtnC"] + d * DC * M["desC"]
        _MULT_CACHE[key] = (tm, cm)
    return _MULT_CACHE[key]

# Dijkstra용 셀 비용밀도(지표별, km당). 통행불가 = SEA_BLOCK. 캐시
_GRID_CACHE = {}
def _grid_for(mode, priority, season):
    key = (mode, priority, season)
    if key not in _GRID_CACHE:
        tm, cm = _mults(mode, season); M = MODES.get(mode, MODES[DEFAULT_MODE])
        g = [[0.0] * _GH for _ in range(_GW)]
        for i in range(_GW):
            for j in range(_GH):
                if _is_water(i, j): g[i][j] = SEA_BLOCK
                elif priority == "최단":     g[i][j] = PXKM
                elif priority == "최저비용": g[i][j] = PXKM * M["rate"] * cm[i][j]
                else:                                                  # 최속
                    g[i][j] = PXKM * tm[i][j] / M["speed"]
                    if _is_road(i, j): g[i][j] *= M.get("yamSpeed", 1.0)  # 역참로 위 시간 단축(엘치 큼)
        _GRID_CACHE[key] = g
    return _GRID_CACHE[key]

_NB = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
def _dijkstra(si, sj, g):
    INF = float("inf")
    dist = [[INF] * _GH for _ in range(_GW)]; prev = [[None] * _GH for _ in range(_GW)]
    dist[si][sj] = 0.0; pq = [(0.0, si, sj)]
    while pq:
        d, i, j = heapq.heappop(pq)
        if d > dist[i][j]: continue
        gi = g[i][j]
        for dx, dy in _NB:
            ni, nj = i + dx, j + dy
            if 0 <= ni < _GW and 0 <= nj < _GH:
                nd = d + math.hypot(dx * _CW, dy * _CH) * (gi + g[ni][nj]) * 0.5
                if nd < dist[ni][nj]:
                    dist[ni][nj] = nd; prev[ni][nj] = (i, j); heapq.heappush(pq, (nd, ni, nj))
    return dist, prev

def _trace(prev, si, sj, ti, tj):
    pts = [(ti, tj)]; cur = (ti, tj)
    while cur != (si, sj) and prev[cur[0]][cur[1]] is not None:
        cur = prev[cur[0]][cur[1]]; pts.append(cur)
    pts.reverse(); return pts

def _simplify(pts, eps=4.0):
    n = len(pts)
    if n < 3: return pts
    keep = [False] * n; keep[0] = keep[n - 1] = True; st = [(0, n - 1)]
    while st:
        s, e = st.pop(); x1, y1 = pts[s]; x2, y2 = pts[e]
        dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1.0; dmax = 0.0; idx = -1
        for k in range(s + 1, e):
            x0, y0 = pts[k]; dd = abs((x0 - x1) * dy - (y0 - y1) * dx) / L
            if dd > dmax: dmax = dd; idx = k
        if idx != -1 and dmax > eps:
            keep[idx] = True; st.append((s, idx)); st.append((idx, e))
    return [pts[k] for k in range(n) if keep[k]]

def _path_metrics(cellpath, mode, season):
    """경로(셀 시퀀스)의 3지표: (거리 km, 시간 일, 비용 관)."""
    tm, cm = _mults(mode, season); M = MODES.get(mode, MODES[DEFAULT_MODE])
    ys = M.get("yamSpeed", 1.0)
    def _tr(i, j): return tm[i][j] * (ys if _is_road(i, j) else 1.0)   # 역참로 위 시간 단축 반영
    km = days = coin = 0.0
    for a in range(len(cellpath) - 1):
        i, j = cellpath[a]; ni, nj = cellpath[a + 1]
        stepkm = math.hypot((ni - i) * _CW, (nj - j) * _CH) * PXKM
        km += stepkm
        days += stepkm * (_tr(i, j) + _tr(ni, nj)) * 0.5 / M["speed"]
        coin += stepkm * M["rate"] * (cm[i][j] + cm[ni][nj]) * 0.5
    return km, days, coin

def least_cost(coords, mode=DEFAULT_MODE, priority=DEFAULT_PRIORITY, season=DEFAULT_SEASON):
    """좌표 → (선택지표 대칭 비용행렬 C, 쌍별 곡선 경로 paths[(i,j)], 쌍별 3지표 metrics[(i,j)]=(km,days,coin)).
    C는 priority가 정한 지표(최속=일, 최저비용=관, 최단=km)로 TSP가 그 총합을 최소화."""
    n = len(coords)
    g = _grid_for(mode, priority, season)
    cells = [_land_cell(*_to_cell(x, y)) for (x, y) in coords]
    C = np.zeros((n, n)); paths = {}; metrics = {}
    for i in range(n):
        dist, prev = _dijkstra(cells[i][0], cells[i][1], g)
        for j in range(n):
            if j == i: continue
            C[i, j] = dist[cells[j][0]][cells[j][1]]
            if j > i:
                cp = _trace(prev, cells[i][0], cells[i][1], cells[j][0], cells[j][1])
                metrics[(i, j)] = _path_metrics(cp, mode, season)
                px = [_cellxy(ci, cj) for (ci, cj) in cp]
                if px: px[0] = coords[i]; px[-1] = coords[j]
                paths[(i, j)] = [[round(x, 1), round(y, 1)] for (x, y) in _simplify(px, 4.0)]
    for i in range(n):
        for j in range(i + 1, n):
            v = min(C[i, j], C[j, i]); C[i, j] = C[j, i] = v
    return C, paths, metrics

def cost_from_center(center, cities, mode=DEFAULT_MODE, priority=DEFAULT_PRIORITY, season=DEFAULT_SEASON):
    """중심에서 각 도시로의 격자 최소비용(현 지표) {이름: 비용}. 카토그램·영향권용."""
    g = _grid_for(mode, priority, season)
    ci, cj = _land_cell(*_to_cell(center[0], center[1]))
    dist, _ = _dijkstra(ci, cj, g)
    out = {}
    for c in cities:
        i, j = _land_cell(*_to_cell(c["x"], c["y"]))
        out[c["n"]] = float(dist[i][j])
    return out
