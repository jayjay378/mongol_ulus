# -*- coding: utf-8 -*-
"""오프라인 빌드 (런타임 아님 — 도시/지형을 바꾼 뒤 1회 실행: `py geobuild.py`).
① 1275년 팍스 몽골리카 주요 75개 도시(CITIES)에 실제 좌표를 부여하고 고정 bbox 등장방형 투영으로
   viewBox x/y 계산 → map_data.json 재생성(cities 75 + ghosts 유지, 클라리체·클로에 육지 보정).
② Natural Earth 50m 벡터(land/lakes/rivers, public domain) → 같은 투영으로 SVG path 'd' → geo.json.
③ 명명된 지형 장애(BARRIERS_LL, 실제 산맥/사막)를 투영해 geo.json["barriers"]에 기록(terrain.py가 로드).

투영 bbox는 **고정**(도시를 추가해도 기존 좌표·장애가 흔들리지 않음). 새 도시/설명 추가법은 README 참고.
출처: 도시 좌표 = 역사 위치(WHG/일반 지리지식 교차확인, 유적은 근사), 지오 = Natural Earth(PD)."""
import json, os, math, urllib.request, urllib.parse, time, base64

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_geocache"); os.makedirs(CACHE, exist_ok=True)

# 권역 라벨
R1, R2, R3, R4 = "동방 대영지", "중앙아시아·실크로드", "서아시아·중동", "북서방·동유럽"

# ---- 75개 도시: 이름 → (lat, lon, region). 1275 팍스 몽골리카 절정기. ----
CITIES = {
 # ① 대칸 직할령·동아시아 (20)
 "대도":(39.90,116.40,R1), "상도":(42.36,116.18,R1), "카라코룸":(47.20,102.83,R1),
 "개경":(37.97,126.55,R1), "합포":(35.19,128.58,R1), "양양":(32.01,112.12,R1),
 "임안":(30.27,120.16,R1), "천주":(24.87,118.59,R1), "광주":(23.13,113.26,R1),
 "성도":(30.57,104.07,R1), "대리":(25.69,100.16,R1), "경조":(34.27,108.95,R1),
 "개봉":(34.80,114.31,R1), "평양":(36.08,111.52,R1), "서경":(40.09,113.30,R1),
 "요양":(41.27,123.17,R1), "영하":(38.49,106.23,R1), "라싸":(29.65,91.14,R1),
 "동평":(35.94,116.47,R1), "제남":(36.65,117.00,R1),
 # ② 중앙아시아·실크로드 (15)
 "알말리크":(43.95,81.33,R2), "에밀":(46.75,82.98,R2), "고창":(42.95,89.18,R2),
 "베슈발리크":(44.06,89.20,R2), "카슈가르":(39.47,75.99,R2), "호탄":(37.11,79.93,R2),
 "사마르칸트":(39.65,66.96,R2), "부하라":(39.77,64.42,R2), "우르겐치":(42.33,59.15,R2),
 "오트라르":(42.85,68.30,R2), "후잔트":(40.28,69.62,R2), "타라즈":(42.90,71.39,R2),
 "야르칸드":(38.42,77.27,R2), "발라사군":(42.75,75.30,R2), "우루무치":(43.83,87.62,R2),
 # ③ 서아시아·중동 (일 한국) (20)
 "타브리즈":(38.08,46.29,R3), "마라게":(37.39,46.24,R3), "바그다드":(33.31,44.36,R3),
 "쉬라즈":(29.59,52.58,R3), "이스파한":(32.65,51.67,R3), "니샤푸르":(36.21,58.80,R3),
 "헤라트":(34.35,62.20,R3), "바스라":(30.51,47.81,R3), "모술":(36.34,43.13,R3),
 "알레포":(36.20,37.16,R3), "다마스쿠스":(33.51,36.29,R3), "디야르바키르":(37.91,40.24,R3),
 "코냐":(37.87,32.49,R3), "시바스":(39.75,37.02,R3), "에르주룸":(39.91,41.27,R3),
 "트빌리시":(41.72,44.79,R3), "아니":(40.51,43.57,R3), "하마단":(34.80,48.52,R3),
 "메르브":(37.66,62.19,R3), "카즈빈":(36.27,50.00,R3),
 # ④ 북서방·동유럽 (킵차크 한국) (20)
 "사라이":(47.20,47.80,R4), "신사라이":(48.60,44.90,R4), "불가르":(54.98,49.04,R4),
 "아스트라한":(46.35,48.04,R4), "아조프":(47.11,39.42,R4), "수다크":(44.85,34.97,R4),
 "카파":(45.03,35.38,R4), "키예프":(50.45,30.52,R4), "블라디미르":(56.13,40.41,R4),
 "노브고로드":(58.52,31.27,R4), "모스크바":(55.75,37.62,R4), "트베리":(56.86,35.92,R4),
 "랴잔":(54.50,40.05,R4), "갈리치":(49.12,24.72,R4), "스몰렌스크":(54.78,32.05,R4),
 "데르벤트":(42.06,48.29,R4), "바쿠":(40.41,49.87,R4), "우케크":(51.50,46.00,R4),
 "수즈달":(56.42,40.45,R4), "야로슬라블":(57.62,39.89,R4),
}
# 항상 라벨 표시(주요 거점) / 수도
MAJOR = {"대도","상도","카라코룸","개경","임안","천주","사마르칸트","부하라","타브리즈","바그다드",
         "사라이","카슈가르","라싸","키예프","노브고로드","헤라트","타라즈","다마스쿠스"}
CAPITAL = {"대도"}

# ---- 명명된 지형 장애: (이름, lat, lon, radius°, k세기). 실제 산맥/사막. ----
# 역참(Yam) 지형 제약을 반영 → 최소비용 경로가 실제 회랑을 따라 굽는다:
#  · 하서주랑(Hexi): 치롄산맥(남) ↔ 고비(북) 사이 좁은 회랑으로 둔황↔중국이 뱀처럼 휨.
#  · 헝두안산맥: 성도↔대리가 진사강 협곡을 따라 강하게 우회.
BARRIERS_LL = [
 ("자그로스 산맥", 33.0, 48.0, 3.0, 4.0), ("캅카스 산맥", 42.8, 44.0, 2.2, 3.5),
 ("엘부르즈",      36.3, 52.0, 1.8, 3.0), ("카라쿰 사막", 39.5, 58.5, 2.6, 3.0),
 ("파미르·천산",   39.0, 73.0, 2.4, 5.0), ("톈산 동부",   43.0, 84.0, 2.4, 3.0),
 ("타클라마칸",    38.8, 83.0, 3.0, 3.5), ("고비 사막",   42.5,105.0, 3.6, 3.2),
 ("티베트 고원",   32.0, 88.0, 5.0, 3.5), ("히말라야",    29.0, 86.0, 2.6, 4.0),
 ("치롄산맥",      37.8, 99.0, 2.2, 3.6), ("헝두안산맥",  28.2,101.0, 2.2, 4.2),
]

# 사막(건조)은 실제 표고(DEM)로 안 잡히므로 실제 위치의 존(zone)으로 가산. (이름, lat, lon, 반경°, 세기)
DESERTS_LL = [
    ("타클라마칸", 38.6, 83.0, 3.2, 3.0), ("고비", 42.5, 104.0, 4.6, 2.6),
    ("카라쿰", 39.2, 59.0, 2.7, 2.6), ("키질쿰", 43.0, 63.5, 2.3, 2.0),
    ("다쉬테카비르", 34.0, 54.5, 2.7, 2.6), ("다쉬테루트", 31.0, 58.5, 2.0, 2.6),
    ("시리아 사막", 33.0, 40.0, 3.2, 2.6), ("아라비아 북부", 29.5, 43.0, 3.0, 2.4),
]

# 칼비노 '보이지 않는 도시' 중 바다에 놓였던 2개를 육지로 보정 (이름 → lat,lon)
GHOST_FIX = {"클로에": (33.0, 55.0), "클라리체": (39.0, 34.0)}

# 몽골 제국 최대 영토(~1294) 경계 (lat, lon), 시계방향. 이 밖은 바다처럼 통행불가로 둔다.
# 75개 도시는 모두 안에 들고, 인도·아라비아·서유럽·일본·동남아는 밖(검증됨).
EMPIRE_LL = [
    (60, 19), (63, 58), (60, 92), (54, 118), (52, 136),
    (33, 133), (29, 123), (23, 120), (20, 113), (22, 107), (20, 100), (27, 92), (30, 80), (29, 72),
    (25, 57), (26, 45), (30, 33), (36, 28), (45, 21), (52, 18),
]
# 제외존: 발칸·트라키아(콘스탄티노플=비잔틴)·흑해 서안. 제국 폴리곤 안이지만 비(非)몽골 영토라 통행불가.
# → 아나톨리아↔크림/루스는 흑해 서쪽(콘스탄티노플)이 아니라 동쪽(캅카스)으로만 연결됨.
EXCLUDE_LL = [(49, 17), (49, 31), (43, 31), (40, 30), (36, 26), (36, 17)]

# ---- 투영(aspect 보존 등장방형, 고정 bbox) ----
PX0, PX1, PY0, PY1 = 92, 1188, 162, 678         # 도시 fit 박스
LON0, LON1, LAT0, LAT1 = 23.0, 130.0, 20.0, 60.0  # 고정 bbox(75 도시 + 여백)
LATM = (LAT0 + LAT1) / 2.0; COSL = math.cos(math.radians(LATM))
_dataW = (LON1 - LON0) * COSL; _dataH = (LAT1 - LAT0)
S = min((PX1 - PX0) / _dataW, (PY1 - PY0) / _dataH)
OX = PX0 + ((PX1 - PX0) - _dataW * S) / 2.0
OY = PY0 + ((PY1 - PY0) - _dataH * S) / 2.0

def project(lat, lon):
    return (round(OX + (lon - LON0) * COSL * S, 1), round(OY + (LAT1 - lat) * S, 1))

# ---- Natural Earth ----
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"

def fetch(name):
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        req = urllib.request.Request(NE + name, headers={"User-Agent": "Mozilla/5.0"})
        open(path, "wb").write(urllib.request.urlopen(req, timeout=90).read())
    return json.load(open(path, encoding="utf-8"))

def bbox_hit(coords):
    xs = [c[0] for c in coords]; ys = [c[1] for c in coords]
    return not (max(xs) < LON0 or min(xs) > LON1 or max(ys) < LAT0 or min(ys) > LAT1)

def dp_open(pts, eps):
    n = len(pts)
    if n < 3: return pts[:]
    keep = [False] * n; keep[0] = keep[n - 1] = True; stack = [(0, n - 1)]
    while stack:
        s, e = stack.pop(); x1, y1 = pts[s]; x2, y2 = pts[e]
        dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1.0; dmax = 0.0; idx = -1
        for i in range(s + 1, e):
            x0, y0 = pts[i]; d = abs((x0 - x1) * dy - (y0 - y1) * dx) / L
            if d > dmax: dmax = d; idx = i
        if idx != -1 and dmax > eps:
            keep[idx] = True; stack.append((s, idx)); stack.append((idx, e))
    return [pts[i] for i in range(n) if keep[i]]

def dp_closed(pts, eps):
    if len(pts) > 1 and pts[0] == pts[-1]: pts = pts[:-1]
    n = len(pts)
    if n < 4: return pts
    p0 = pts[0]
    far = max(range(n), key=lambda i: (pts[i][0] - p0[0]) ** 2 + (pts[i][1] - p0[1]) ** 2)
    return dp_open(pts[0:far + 1], eps)[:-1] + dp_open(pts[far:] + [pts[0]], eps)[:-1]

def to_d(lonlat, close, eps=1.2):
    proj = [project(p[1], p[0]) for p in lonlat]
    proj = dp_closed(proj, eps) if close else dp_open(proj, eps)
    if len(proj) < (3 if close else 2): return None
    return "M" + " L".join("%g,%g" % (x, y) for x, y in proj) + (" Z" if close else "")

def rings(geom):
    t = geom["type"]; c = geom["coordinates"]
    if t == "Polygon": yield c[0]
    elif t == "MultiPolygon":
        for p in c: yield p[0]

def lstrings(geom):
    t = geom["type"]; c = geom["coordinates"]
    if t == "LineString": yield c
    elif t == "MultiLineString":
        for l in c: yield l

def collect_polys(fname, eps=1.2):
    out = []
    for f in fetch(fname)["features"]:
        for ring in rings(f["geometry"]):
            if bbox_hit(ring):
                d = to_d(ring, True, eps)
                if d: out.append(d)
    return out

def collect_lines(fname, eps=1.0):
    out = []
    for f in fetch(fname)["features"]:
        for ln in lstrings(f["geometry"]):
            if bbox_hit(ln):
                d = to_d(ln, False, eps)
                if d: out.append(d)
    return out

def holes(geom):
    """폴리곤 내부 구멍 ring들(내해·호수가 land 폴리곤의 hole로 표현됨: 카스피·아랄 등)."""
    t = geom["type"]; c = geom["coordinates"]
    if t == "Polygon":
        for h in c[1:]: yield h
    elif t == "MultiPolygon":
        for p in c:
            for h in p[1:]: yield h

def proj_rings(fname, eps=2.0, want_holes=False):
    """폴리곤 ring들을 투영 px 좌표로(마스크 래스터화용, 닫는 중복점 없음).
    want_holes=True면 외곽 대신 내부 구멍 ring들을 반환."""
    out = []; src = holes if want_holes else rings
    for f in fetch(fname)["features"]:
        for ring in src(f["geometry"]):
            if bbox_hit(ring):
                pr = dp_closed([project(p[1], p[0]) for p in ring], eps)
                if len(pr) >= 3:
                    out.append(pr)
    return out

# 육지/바다 마스크: terrain.py 격자와 동일한 영역(viewBox 클립)·해상도. 스캔라인 폴리곤 채우기.
SEA_W, SEA_H = 232, 140
SEA_X0, SEA_X1, SEA_Y0, SEA_Y1 = 38, 1242, 106, 708

def _scanfill(rings, val, grid):
    cw = (SEA_X1 - SEA_X0) / SEA_W; ch = (SEA_Y1 - SEA_Y0) / SEA_H
    for j in range(SEA_H):
        cy = SEA_Y0 + (j + 0.5) * ch; xs = []
        for ring in rings:
            m = len(ring)
            for k in range(m):
                x1, y1 = ring[k]; x2, y2 = ring[(k + 1) % m]
                if (y1 <= cy < y2) or (y2 <= cy < y1):
                    xs.append(x1 + (cy - y1) / (y2 - y1) * (x2 - x1))
        xs.sort()
        for a in range(0, len(xs) - 1, 2):
            ia = max(0, int((xs[a] - SEA_X0) / cw)); ib = min(SEA_W - 1, int((xs[a + 1] - SEA_X0) / cw))
            for i in range(ia, ib + 1): grid[i][j] = val

def build_seamask(land_rings, land_holes, lake_rings, empire_ring, exclude_ring):
    grid = [[1] * SEA_H for _ in range(SEA_W)]   # 1=통행불가(기본), 0=통행가능
    _scanfill(land_rings, 0, grid)   # 육지 = 통행가능
    _scanfill(land_holes, 1, grid)   # 내해(카스피·아랄 등 land 구멍) = 불가
    _scanfill(lake_rings, 1, grid)   # 호수 = 불가
    # 제국 밖 = 통행불가(바다와 동일). 제국 안만 육지가 통행 가능하게 남긴다.
    emp = [[0] * SEA_H for _ in range(SEA_W)]
    _scanfill([empire_ring], 1, emp)
    for i in range(SEA_W):
        for j in range(SEA_H):
            if emp[i][j] == 0:
                grid[i][j] = 1
    _scanfill([exclude_ring], 1, grid)   # 발칸·콘스탄티노플 제외존 = 통행불가
    bits = "".join(str(grid[i][j]) for i in range(SEA_W) for j in range(SEA_H))
    blocked = bits.count("1")
    return {"w": SEA_W, "h": SEA_H, "x0": SEA_X0, "x1": SEA_X1, "y0": SEA_Y0, "y1": SEA_Y1, "bits": bits}, blocked

# ---- 실제 표고(DEM) → 난이도 그리드 ----
ELEV_W, ELEV_H = 120, 72   # 표고 샘플 격자(opentopodata ETOPO1, 캐시)
ELEV_CACHE = os.path.join(CACHE, "elev_%dx%d.json" % (ELEV_W, ELEV_H))
SLOPE_K, ALT_K, ALT0 = 0.12, 1.4, 2500.0   # 난이도 = 1 + 경사*K + 고도초과*K + 사막

def fetch_elev():
    if os.path.exists(ELEV_CACHE):
        return json.load(open(ELEV_CACHE))
    pts = []
    for j in range(ELEV_H):
        for i in range(ELEV_W):
            pts.append((LAT1 - (j + 0.5) / ELEV_H * (LAT1 - LAT0),
                        LON0 + (i + 0.5) / ELEV_W * (LON1 - LON0)))
    E = []
    for s in range(0, len(pts), 100):
        loc = "|".join("%.3f,%.3f" % (a, b) for a, b in pts[s:s + 100])
        for attempt in range(4):
            try:
                r = urllib.request.urlopen(urllib.request.Request(
                    "https://api.opentopodata.org/v1/etopo1?locations=" + urllib.parse.quote(loc),
                    headers={"User-Agent": "Mozilla/5.0"}), timeout=40)
                E += [d["elevation"] for d in json.load(r)["results"]]; break
            except Exception:
                if attempt == 3: raise
                time.sleep(2.0)
        time.sleep(1.05)   # opentopodata 무료: 1 req/sec
    json.dump(E, open(ELEV_CACHE, "w"))
    return E

def build_difficulty():
    E = fetch_elev(); EW, EH = ELEV_W, ELEV_H
    elev = [[(E[j * EW + i] or 0) for j in range(EH)] for i in range(EW)]
    dxkm = (LON1 - LON0) / EW * 111.0 * COSL; dykm = (LAT1 - LAT0) / EH * 111.0
    def ev(i, j): return elev[max(0, min(EW - 1, i))][max(0, min(EH - 1, j))]
    slope = [[math.hypot((ev(i + 1, j) - ev(i - 1, j)) / (2 * dxkm),
                         (ev(i, j + 1) - ev(i, j - 1)) / (2 * dykm)) for j in range(EH)] for i in range(EW)]
    def samp(g, lon, lat):
        fi = (lon - LON0) / (LON1 - LON0) * EW - 0.5; fj = (LAT1 - lat) / (LAT1 - LAT0) * EH - 0.5
        i0 = int(math.floor(fi)); j0 = int(math.floor(fj)); ti = fi - i0; tj = fj - j0
        def gg(i, j): return g[max(0, min(EW - 1, i))][max(0, min(EH - 1, j))]
        return (gg(i0, j0) * (1 - ti) * (1 - tj) + gg(i0 + 1, j0) * ti * (1 - tj)
                + gg(i0, j0 + 1) * (1 - ti) * tj + gg(i0 + 1, j0 + 1) * ti * tj)
    def desert(lon, lat):
        s = 0.0
        for _, la, lo, r, k in DESERTS_LL:
            dla = lat - la; dlo = (lon - lo) * math.cos(math.radians(la))
            s += k * math.exp(-(dla * dla + dlo * dlo) / (2 * r * r))
        return s
    W, H = SEA_W, SEA_H; cw = (SEA_X1 - SEA_X0) / W; ch = (SEA_Y1 - SEA_Y0) / H
    # 난이도를 두 성분으로 분리: mtn(경사+고도=산악), des(사막). 합산 안 함 — terrain.py가 지표별로 가중.
    mtn = [[0.0] * H for _ in range(W)]; des = [[0.0] * H for _ in range(W)]
    for i in range(W):
        for j in range(H):
            x = SEA_X0 + (i + 0.5) * cw; y = SEA_Y0 + (j + 0.5) * ch
            lon = LON0 + (x - OX) / (COSL * S); lat = LAT1 - (y - OY) / S
            e = samp(elev, lon, lat); sl = samp(slope, lon, lat)
            mtn[i][j] = SLOPE_K * sl + ALT_K * max(0.0, e - ALT0) / 1000.0
            des[i][j] = desert(lon, lat)
    return mtn, des

def encode_diff(diff, scale=20.0):
    W = len(diff); H = len(diff[0])
    bs = bytes(min(255, int(round(diff[i][j] * scale))) for i in range(W) for j in range(H))
    return {"w": W, "h": H, "scale": scale, "b64": base64.b64encode(bs).decode()}

def downsample_heat(diff, HW=96, HH=58):
    W = len(diff); H = len(diff[0]); mx = max(max(c) for c in diff) or 1.0
    out = []
    for j in range(HH):
        for i in range(HW):
            si = int((i + 0.5) / HW * W); sj = int((j + 0.5) / HH * H)
            out.append(min(255, int(diff[si][sj] / mx * 255)))
    return {"w": HW, "h": HH, "x0": SEA_X0, "x1": SEA_X1, "y0": SEA_Y0, "y1": SEA_Y1,
            "b64": base64.b64encode(bytes(out)).decode()}

def main():
    data = json.load(open(os.path.join(HERE, "map_data.json"), encoding="utf-8"))

    # 도시 75개 재생성(투영)
    cities = []
    for n, (lat, lon, region) in CITIES.items():
        x, y = project(lat, lon)
        cities.append({"n": n, "x": x, "y": y, "lat": lat, "lon": lon, "region": region,
                       "M": n in MAJOR, "C": n in CAPITAL})
    data["cities"] = cities

    # 보이지 않는 도시: 유지 + 2개 육지 보정
    for gh in data.get("ghosts", []):
        if gh["n"] in GHOST_FIX:
            gh["x"], gh["y"] = project(*GHOST_FIX[gh["n"]])

    json.dump(data, open(os.path.join(HERE, "map_data.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

    # 장애 투영
    barriers = []
    for n, lat, lon, rad, k in BARRIERS_LL:
        x, y = project(lat, lon)
        barriers.append({"n": n, "x": x, "y": y, "s": round(rad * S, 1), "k": k})

    empire_ring = [project(la, lo) for (la, lo) in EMPIRE_LL]
    exclude_ring = [project(la, lo) for (la, lo) in EXCLUDE_LL]
    sea, water_cells = build_seamask(proj_rings("ne_50m_land.geojson", 2.0),
                                     proj_rings("ne_50m_land.geojson", 2.0, want_holes=True),
                                     proj_rings("ne_50m_lakes.geojson", 1.5),
                                     empire_ring, exclude_ring)
    mtn, des = build_difficulty()
    heatgrid = [[1.0 + mtn[i][j] + des[i][j] for j in range(SEA_H)] for i in range(SEA_W)]  # 평시 합성(음영용)
    geo = {
        "meta": {"bbox": [LON0, LAT0, LON1, LAT1], "proj": [OX, OY, S, COSL, LON0, LAT1]},
        "land":   collect_polys("ne_50m_land.geojson", 1.2),
        "lakes":  collect_polys("ne_50m_lakes.geojson", 1.0),
        "rivers": collect_lines("ne_50m_rivers_lake_centerlines.geojson", 1.0),
        "barriers": barriers,            # 폴백/참고용
        "sea": sea,                      # 통행 마스크(바다+제국밖)
        "mtn": encode_diff(mtn),         # 산악 성분(경사+고도) — terrain이 지표별로 가중
        "des": encode_diff(des),         # 사막 성분(건조)
        "heat": downsample_heat(heatgrid),  # 난이도 음영 시각용(iframe)
    }
    json.dump(geo, open(os.path.join(HERE, "geo.json"), "w", encoding="utf-8"), ensure_ascii=False)

    def at(g, la, lo):
        x, y = project(la, lo)
        i = max(0, min(SEA_W-1, int((x-SEA_X0)/(SEA_X1-SEA_X0)*SEA_W)))
        j = max(0, min(SEA_H-1, int((y-SEA_Y0)/(SEA_Y1-SEA_Y0)*SEA_H)))
        return g[i][j]
    print("cities:", len(cities), "| ghosts:", len(data.get("ghosts", [])))
    print("land:", len(geo["land"]), "lakes:", len(geo["lakes"]), "rivers:", len(geo["rivers"]),
          "barriers:", len(barriers), "| S=%.2f px/°" % S)
    print("통행 마스크 %dx%d, 불가 셀 %d/%d (%.0f%%)" % (sea["w"], sea["h"], water_cells,
          sea["w"]*sea["h"], 100.0*water_cells/(sea["w"]*sea["h"])))
    print("mtn 성분: 히말라야 %.1f 티베트 %.1f 파미르 %.1f 평지 %.1f | des 성분: 타클라마칸 %.1f 시리아 %.1f 카라쿰 %.1f" % (
        at(mtn,29,86), at(mtn,33,88), at(mtn,38,73), at(mtn,50,32), at(des,38.6,83), at(des,33,40), at(des,39,59)))
    # 경계 밖 도시 점검
    out = [c["n"] for c in cities if not (38 <= c["x"] <= 1242 and 106 <= c["y"] <= 708)]
    print("viewBox 밖 도시:", out or "없음")

if __name__ == "__main__":
    main()
