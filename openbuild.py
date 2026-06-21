# -*- coding: utf-8 -*-
"""오프닝 전용 지도 빌더 (오프라인 — 네트워크 불필요, 캐시된 Natural Earth만 사용).
마르코 폴로 오프닝 시네마틱용으로 제노바(서)~대도(동) 일대의 실제 해안선을 오프닝 스테이지
좌표(opSvg viewBox 1000×520)로 투영해 opening_map.json을 만든다.
메인 지도(geo.json·map_data.json)는 전혀 건드리지 않는다(별도 산출물).
실행: py openbuild.py  (도시·범위를 바꾼 뒤 1회). 출처=Natural Earth 50m(PD)."""
import json, os, math

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_geocache")

# 오프닝 지리 bbox: 제노바(8.9E)~대도(116.4E) 포함, 약간 여백.
LON0, LON1, LAT0, LAT1 = 4.0, 124.0, 16.0, 56.0
# 오프닝 스테이지 픽셀 박스(opSvg viewBox 1000×520 내부, 여백 확보).
W, H = 1000, 520
PX0, PX1, PY0, PY1 = 40, 960, 58, 470
LATM = (LAT0 + LAT1) / 2.0
COSL = math.cos(math.radians(LATM))
_dataW = (LON1 - LON0) * COSL
_dataH = (LAT1 - LAT0)
S = min((PX1 - PX0) / _dataW, (PY1 - PY0) / _dataH)
OX = PX0 + ((PX1 - PX0) - _dataW * S) / 2.0
OY = PY0 + ((PY1 - PY0) - _dataH * S) / 2.0


def project(lat, lon):
    return (round(OX + (lon - LON0) * COSL * S, 1), round(OY + (LAT1 - lat) * S, 1))


# 오프닝 주요 노드(실제 좌표). 제노바·베네치아=출발, 경유 도식점, 대도=동단.
NODES = {
    "제노바": (44.41, 8.93), "베네치아": (45.44, 12.34),
    "콘스탄티노플": (41.01, 28.98), "바그다드": (33.31, 44.36),
    "사마르칸트": (39.65, 66.96), "카슈가르": (39.47, 75.99),
    "카라코룸": (47.20, 102.83), "대도": (39.90, 116.40),
}
ROUTE = ["베네치아", "콘스탄티노플", "바그다드", "사마르칸트", "카슈가르", "카라코룸", "대도"]
BIG = {"제노바", "베네치아", "대도"}


def fetch(name):
    return json.load(open(os.path.join(CACHE, name), encoding="utf-8"))


def rings(geom):
    t = geom["type"]; c = geom["coordinates"]
    if t == "Polygon":
        yield c[0]
    elif t == "MultiPolygon":
        for p in c:
            yield p[0]


def bbox_hit(coords):
    xs = [c[0] for c in coords]; ys = [c[1] for c in coords]
    return not (max(xs) < LON0 or min(xs) > LON1 or max(ys) < LAT0 or min(ys) > LAT1)


def dp_open(pts, eps):
    n = len(pts)
    if n < 3:
        return pts[:]
    keep = [False] * n; keep[0] = keep[n - 1] = True; stack = [(0, n - 1)]
    while stack:
        s, e = stack.pop(); x1, y1 = pts[s]; x2, y2 = pts[e]
        dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1.0; dmax = 0.0; idx = -1
        for i in range(s + 1, e):
            x0, y0 = pts[i]; d = abs((x0 - x1) * dy - (y0 - y1) * dx) / L
            if d > dmax:
                dmax = d; idx = i
        if idx != -1 and dmax > eps:
            keep[idx] = True; stack.append((s, idx)); stack.append((idx, e))
    return [pts[i] for i in range(n) if keep[i]]


def dp_closed(pts, eps):
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    n = len(pts)
    if n < 4:
        return pts
    p0 = pts[0]
    far = max(range(n), key=lambda i: (pts[i][0] - p0[0]) ** 2 + (pts[i][1] - p0[1]) ** 2)
    return dp_open(pts[0:far + 1], eps)[:-1] + dp_open(pts[far:] + [pts[0]], eps)[:-1]


def to_d(lonlat, eps=1.1):
    proj = [project(p[1], p[0]) for p in lonlat]
    proj = dp_closed(proj, eps)
    if len(proj) < 3:
        return None
    return "M" + " L".join("%g,%g" % (x, y) for x, y in proj) + " Z"


def collect(fname, eps=1.1):
    out = []
    for f in fetch(fname)["features"]:
        for ring in rings(f["geometry"]):
            if bbox_hit(ring):
                d = to_d(ring, eps)
                if d:
                    out.append(d)
    return out


def main():
    land = collect("ne_50m_land.geojson", 1.1)
    lakes = collect("ne_50m_lakes.geojson", 0.9)
    nodes = {}
    for n, (la, lo) in NODES.items():
        x, y = project(la, lo)
        nodes[n] = {"x": x, "y": y, "big": (n in BIG)}
    # 메인 지도 75개 도시를 오프닝 좌표로 투영(오프닝 '수많은 도시' 연출용 배경 노드).
    cities = []
    try:
        md = json.load(open(os.path.join(HERE, "map_data.json"), encoding="utf-8"))
        for c in md.get("cities", []):
            if "lat" in c and "lon" in c:
                x, y = project(c["lat"], c["lon"])
                cities.append({"x": x, "y": y, "n": c["n"]})
    except Exception as e:
        print("map_data 도시 투영 실패:", e)
    out = {"w": W, "h": H, "land": land, "lakes": lakes, "nodes": nodes,
           "route": ROUTE, "cities": cities, "bbox": [LON0, LAT0, LON1, LAT1]}
    json.dump(out, open(os.path.join(HERE, "opening_map.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    print("opening_map: land=%d lakes=%d nodes=%d cities=%d | S=%.2f px/°" % (
        len(land), len(lakes), len(nodes), len(cities), S))
    for n, p in nodes.items():
        print("  %-8s (%.0f, %.0f)%s" % (n, p["x"], p["y"], "  ★" if p["big"] else ""))


if __name__ == "__main__":
    main()
