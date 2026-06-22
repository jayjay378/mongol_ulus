# 인계 문서 — 칸이 명한 순행로 (Claude Code 이어가기용)

몽골 제국 시대를 배경으로, 순회 감찰관(廉訪使)이 되어 **도시 순회 최적화(TSP)**를 풀고
인간의 직관과 컴퓨터/양자 해법을 비교하는 교육·오락용 웹앱. 수업 과제 규모.

---

## 1. 한눈 요약 / 실행
```
cd mongol_app
py -m venv .venv           # Windows: 'python'이 Store 더미면 'py' 사용
.\.venv\Scripts\Activate.ps1   # mac/linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
PowerShell에서 activate 안 되면: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` 후 재시도,
또는 활성화 없이 `.\.venv\Scripts\streamlit.exe run app.py`.

## 2. 아키텍처 (가벼운 단방향 구조)
- **Streamlit 한 앱** 안에서 Python이 최적화(고전·Brute·양자)를 담당.
- SVG 고지도는 `components.html()`로 iframe에 끼워넣어 **줌/팬/호버/플레이**를 매끄럽게 유지.
- 데이터 흐름은 **Python → HTML 단방향**: 사이드바 위젯으로 선택·실행 → 계산 결과를 HTML에 주입.
  iframe→Python 역방향(클릭 콜백)이 없어 양방향 커스텀 컴포넌트가 불필요(가벼움).
- 플레이어의 직접 경로 그리기·채점은 **iframe 내부 JS에서 자기완결**로 처리(역방향 불필요).
- 왜 이 구조? 양자(qiskit)는 브라우저 불가 → Python 필요. 슬리피맵(Leaflet 등)은 미감·왜곡과
  충돌 → 직접 그린 SVG. 서버 분리(FastAPI)는 과제 규모엔 과함 → Streamlit 단일.

## 3. 파일
- `app.py` — Streamlit UI/흐름. 도시 선택(수동/무작위), 해법 선택, 최적화, 시작도시 회전, 지도 주입,
  지형 비용 토글 + 비용행렬/카토그램 데이터 주입.
- `solver.py` — `distance_matrix`, `nearest_neighbor`, `two_opt`, `solve_classical`, `solve_bruteforce`,
  `solve_qaoa`(qiskit-optimization 0.7 API; 거리 정규화 + result.x 직접 디코딩 + 유효성 검사).
  세 solve_*에 **선택적 비용행렬 인자 `C=None`**(있으면 거리 대신 그 행렬 사용; 지형 비용용).
- `terrain.py` — 지형 이동 비용(합성). `BARRIERS`는 **`geo.json`에서 로드**(geobuild가 투영), `difficulty(x,y)`,
  `seg_cost`, `cost_matrix`(대칭 N×N), `cost_from_center`(카토그램·영향권용 중심거리비용).
- `map_view.py` — `build_map(..., terrain, costs, barriers, cr, cart_center, geo, info)`
  → SVG 고지도 HTML. 지오 베이스맵·**모드토글(탐험|순행 그리기)**·**백과사전 카드**·플레이·줌/팬·이스터에그·지형 시각.
- `map_data.json` — 도시 75 + 보이지 않는 도시 21 (**실제 좌표 투영**; `geobuild.py` 생성).
- `cities_info.json` — 도시별 `{region, desc}` 백과사전 콘텐츠(사용자 편집 지점, 상단 `_README`).
- `scenarios.json` — 순행 임무(시나리오) 정의: 도시·주체·우선순위·계절 고정 + gap% 별점 임계(§15, 사용자 편집, `_README`).
- `geo.json` — 실제 지리(해안선·강·호수 SVG path) + 투영된 지형 장애(barriers). `geobuild.py` 산출물.
- `geobuild.py` — 오프라인 빌드(1회 실행): `CITIES`(75 lat/lon/권역) 투영→map_data.json, Natural Earth→geo.json.
- `map_data.distorted.bak.json` — L3 이전 왜곡좌표 백업.

## 4. 데이터/좌표 규약
- **L3에서 변경됨(§11): 이제 실제 위경도를 고정 bbox 등장방형 투영한 좌표**(geobuild.py). 대도=동단.
  아래 옛 규약은 L3 이전 기록(백업 `map_data.distorted.bak.json`).
- (구) 실제 위경도 대신 **상대 위치만 맞춘 왜곡 좌표**(viewBox 1280×780). 대도(칸발리크)는 우중앙(955,395).
- 도시 58개는 밀집 해소를 위해 **완화(relaxation) 알고리즘**으로 분산(최소 간격 ~48px). 대도는 고정.
  (좌표 생성·완화 스크립트는 이전 대화의 `gen_map.py`. 현재는 그 결과 `map_data.json`만 사용.)
- 중국 도시는 **한국식 한자음**(항주·천주·서안·개봉·제남·양주·광주·성도·대동·돈황).
- 거리는 이 2D 좌표의 유클리드. solver·플레이어 점수 모두 같은 단위 → 비교 공정.

## 5. 핵심 설계 결정(합의된 것 — 되돌리지 말 것)
- **양자는 "시연/개념 증명"**: 실용 최적화는 고전이 담당. QAOA는 도시 4~5개에서만(큐비트=도시²).
  K=5(25큐비트)면 무효해·지연이 늘어나는데, 그게 NISQ 한계를 보여주는 의도된 교육 효과.
- **보이지 않는 도시(이스터에그)**: 칼비노 21개를 고정 무작위 위치에 **점**으로. 토글은 사이드바
  맨 아래, 라벨은 "보이지 않는 도시들" 단 하나(설명 일절 없음). 실재 도시에 종속/연결선 없음.
- **지형 아트(산맥·강·바다)는 기본 비가시**(사용자 요청). 단 **지형 *비용*은 옵트인 토글로 도입됨**(§10):
  기본 OFF면 종전과 동일, ON일 때만 비용·음영이 드러난다. 옛 `_terrain()`은 여전히 미사용.
- **호버 이름표**: OS 툴팁이 아니라 앱 세리프(Noto Serif KR) 각인 라벨. 도시마다 투명 히트원(r13).
  (과거 버그: 보이지 않는 라벨이 이벤트 가로채기 → pointer-events:none로 해결. 호버 시 DOM 이동
  코드가 일부 호버를 끊던 것 → 제거함.)
- **저작권**: 칼비노 산문 텍스트는 어떤 형태로도 재현 금지. 도시 이름·테마 분류(목차 수준)만 사용.

## 6. 현재 상태 / 직전 작업
- 플레이 모드 구현됨: 선택 도시 금색 강조, 클릭으로 청록 경로 작성, 채점 시 컴퓨터 해답(붉은 점선)
  공개 + "최적 대비 %" 점수.
- **시작 도시 고정 + 왕복** 반영: `start`=대도(없으면 첫 선택). 컴퓨터 경로는 시작도시로 회전,
  플레이어는 출발지에서 자동 시작(picked 시드), 닫힌 순회로 채점.
- 드래그 시 파란 텍스트 선택 → 전역 `user-select:none`로 해결.

## 7. 다음 지시(이번에 다룰 항목)

### 지시 1 — 패널이 좌상단 도시를 가림 (처리됨, 검증 필요)
- 증상: "직접 순행해 보세요" 패널이 지도 좌상단 도시를 덮음.
- 조치: 패널을 **하단 중앙**(`left:50%; transform:translateX(-50%); bottom:14px`)으로 이동하고
  **접기 토글(▾/▸)** 추가. 좌하단 줌 버튼과 겹치지 않음.
- TODO(검증): 도시가 많은 시나리오에서 펼친 패널+점수판이 하단 중앙 도시를 가리는지 확인.
  더 나으면 **드래그로 이동 가능한 패널** 또는 더 슬림한 가로 바로 개선.

### 지시 2 — 시작 도시 고정 + 왕복 (개념 결론 + 처리됨)
- 질문: 시작 도시를 정하고 왕복하게 하면 알고리즘 목표를 해치나?
- 결론: **아니다. 표준이며 이롭다.** TSP는 정의상 닫힌 순회(왕복)라, 시작 도시는 회전·방향 중복을
  없애는 라벨링일 뿐 최적해·길이 불변.
  - 고전: 시작 고정 = 탐색공간 n배 축소(이미 Brute Force는 0번 고정).
  - 양자: 시작 고정 시 QUBO 변수 n²→(n-1)², 퇴화 최적해 제거로 오히려 유리. 단 현재 qiskit `Tsp`는
    전체 n² 정식화라 **지금 코드의 큐비트 수는 n² 유지**(순회는 동일, 시작 고정은 표시/UX 규약).
  - 인간: "좌소에서 출발→전부 순회→복귀"가 직관적이고 페르소나(감찰관 순행)에 부합. 난이도는
    중간 도시 순서로 유지되어 trivial해지지 않음.
- 조치: `app.py`의 `rotate_to()`로 컴퓨터 경로를 시작도시 기준 회전, `map_view`는 시작도시에 "출발"
  표식 + picked 시드. 
- TODO(선택): 진짜 큐비트 절감을 원하면 qiskit `Tsp` 대신 (n-1)² 변수의 start-fixed QUBO 자체 구현.

## 8. 향후 후보 (합의된 방향성)
- ~~비기하 비용~~ → **구현됨(§10, 대칭 지형 비용 + 카토그램, L2).** 남은 길: 비대칭(ATSP)·L3 실제 지리.
- 도시 수 8~12에서 인간 vs 컴퓨터 격차가 커짐(점수 %로 피드백).
- 줌/팬은 추후 d3-zoom 같은 라이브러리로 교체하면 버그군 감소.

## 9. Claude Code 부트스트랩 프롬프트 (새 세션 첫 메시지로 붙여넣기)
```
이 폴더(mongol_app)는 Streamlit 기반 '칸이 명한 순행로' 앱이야. 몽골 제국 시대 배경의
도시 순회 최적화(TSP) 게임으로, app.py(Streamlit 흐름) + solver.py(고전 NN+2-opt / Brute /
QAOA) + map_view.py(components.html로 끼우는 SVG 고지도) + map_data.json(도시58+가상도시21,
고정 좌표) 구조야. 데이터는 Python→HTML 단방향. HANDOFF_CLAUDE_CODE.md에 설계 결정과 맥락이
정리돼 있으니 먼저 읽어줘. 양자는 '시연'용(고전이 실용 담당), 보이지 않는 도시는 이스터에그,
좌표는 상대 위치만 맞춘 왜곡 좌표(대도=우중앙)야. 먼저 `streamlit run app.py`로 띄워 동작을
확인하고, 다음으로 [원하는 작업]을 하고 싶어.
```
`[원하는 작업]` 예: "패널을 드래그 이동 가능하게", "비기하 비용(이동시간) 도입", "고전·양자 경로 동시 비교".

## 10. 지형 비용 — 비기하 비용 (구현됨, L2)
"연결성은 거리가 아니라 비용"(ORBIS 명제)을 합성으로 구현. 사이드바 **"지형 비용" 토글**(기본 OFF).

**핵심 불변식:** OFF면 모든 신규 동작이 꺼져 종전과 동일(검증됨). 신규 코드는 전부 토글 뒤.

**모델(대칭):** `terrain.py`의 `BARRIERS` = 명명된 고정 장애 6개(자그로스/카라쿰/파미르·천산/타클라마칸/
고비/티베트고원)를 도시 군집 *사이* 회랑에 배치. `difficulty(x,y)=1+Σk·gauss`, `seg_cost=거리×선분평균난이도`.
대칭이라 고전·Brute·QAOA 모두 무변경 정합(QAOA는 nx weight를 C로). 40개 무작위 6도시에서 ~73% 선택이
최적 순서가 갈리고 직관손해 median~3% / p90~13% / max~20%(게임으로서 의도된 분포).

**데이터 흐름:** app.py가 `terrain.cost_matrix`로 ① 선택 솔버에 `C` 전달, ② 선택도시 `costs{a:{b}}`를 iframe에
주입(플레이어 채점이 솔버와 *같은 비용* 쓰도록 — 공정성), ③ `cr`(대도 기준 중심거리비용, 카토그램용).
**terrain 모드가 바뀌면 이전 답 무효화**(`answered_terrain`)로 단위 불일치 방지.

**시각(iframe 자기완결, 줌버튼처럼 토글):** 우상단 viz 패널(TERRAIN일 때만).
- 구간 색칠: 플레이어 경로 간선을 `비용/거리` 비율로 청록→주황. 컴퓨터 답(붉은 점선)과 구분.
- **비용 카토그램:** 중심=대도, 반경=`비용/평균비용배율`(각도 보존). 평균보다 험한(산 너머) 도시는 *밖으로*,
  쉬운 도시는 *안으로*. 0.85 축소+클립 클램프로 화면 안. 600ms rAF 보간, cities/ghosts/player/answer 모두 변형.
- 난이도 음영: 장애를 옅은 방사 음영+라벨로. 영향권: 도시를 대도 비용대(4밴드) 소프트 블롭으로(국경선 없음).

**검증 완료:** Python(분기·파리티·QAOA n=4 정합·OFF 빈값) + E2E(preview MCP: 주입·구간색·채점 +38.5% 예시·
카토그램 양방향·음영/영향권 토글·OFF 완전 회귀, 콘솔 에러 0).

**남은 방향:** (a) 비대칭(ATSP, 오르막·바람) — 단 qiskit `Tsp`가 대칭만이라 QAOA는 대칭근사/비활성 필요.
(b) **L3 실제 지리** — WHG(CC-BY, 중앙아시아 지명사전)에서 실제 좌표, DEM 최소비용으로 비용 유도. 단 합의된
왜곡좌표·한자음·지형제거를 덮어쓰는 큰 전환이고 기성 몽골권 비용망은 없음(합성은 불가피). (c) QAOA는 지형 ON 시
무효해가 약간 잦음(가중 분포 넓어짐) — 기본 maxiter↑ 또는 안내로 완화 가능(현재는 의도된 NISQ 한계로 둠).

## 11. L3 — 실제 지리 + 팍스 몽골리카 75 도시 + 백과사전 (구현됨)
ORBIS를 모델로 한 큰 방향 전환(사용자 승인). **왜곡좌표·한자음·지형제거(§5) 결정은 여기서 의도적으로 대체됨.**

- **실제 좌표**: `geobuild.py`의 `CITIES`(1275 팍스 몽골리카 75개, 권역 20/15/20/20)에 역사 위경도 →
  **고정 bbox(lon[23,130]·lat[20,60]) aspect 보존 등장방형 투영**으로 viewBox x/y. bbox 고정이라 도시
  추가해도 기존 좌표·장애 px 불변(확장성). 대도=동단, 합포(고려)=동단, 갈리치=서단.
- **양피지 지오 베이스맵**: Natural Earth 50m(PD) → `geo.json`(land/lakes/rivers SVG path). map_view가
  바다 바탕+육지(양피지)+호수+강을 최하단 레이어로 렌더. 지형 장애도 lat/lon→투영해 geo.json["barriers"].
- **75 도시 + 백과사전 시스템**(Civ/EU4식): 우상단 📖 **백과사전 팝업**(색인=일반 섹션+'도시' 권역별,
  항목 클릭→본문). 일반 항목=`pedia.json`(sections[].entries[]{title,body}, 사용자 기입), 도시 항목=`cities_info.json`.
  지도 상단 **모드 토글**:
  - 탐험(기본): **강조·페이드·게임패널 없는 깨끗한 지도**(svg에 `.draw` 없을 때 CSS로 숨김). 도시 클릭 → 팝업이 그 도시 항목으로.
  - 순행 그리기: `.draw` 부여 → 강조링·페이드·게임패널 표시. 강조 도시 클릭 → 순행로 추가. `viewMode`/`__setMode`로 분기.
- **자동 채점**(버튼 없음): app.py가 매 렌더에 선택+해법으로 답을 자동 계산해 (숨겨) 주입 → iframe '채점'이 공개.
  고전/Brute 즉시, **QAOA는 ≤5 게이트 + `st.cache_data`(선택 바뀔 때만 1회) + 스피너**. '순행 최적화' 버튼 제거됨.
- **확장법(코드 명시)**: 설명 편집=`cities_info.json`의 `desc`(재빌드 불필요). 새 도시=`geobuild.py CITIES`
  +`cities_info.json` 추가 후 `py geobuild.py`. 장애=`geobuild.py BARRIERS_LL` 편집 후 재빌드. (README에도 명시.)
- **보이지 않는 도시**: 칼비노 21개 유지, 바다에 있던 **클라리체·클로에만 육지 보정**(geobuild GHOST_FIX).
- **검증 완료**(preview MCP): 75도시 투영·지오 렌더, 탐험 카드(이름·권역·설명), 순행 그리기 픽·채점,
  지형비용/음영/카토그램이 새 좌표에서 동작(장애 10개 geo.json 로드), 콘솔 에러 0.
- **Phase 2 곡선 최소비용 경로(구현됨)**: `terrain.least_cost(coords)`=격자(232×140) Dijkstra → 대칭 비용행렬 +
  쌍별 곡선 경로(px). 지형 ON이면 솔버·채점·렌더가 모두 이 '격자 최소비용'으로 일관(직선 대신 고개·회랑 우회).
  app.py가 `@st.cache_data`로 선택 바뀔 때만 1회 계산, `paths`를 iframe에 주입 → map_view `legPath()`가 플레이어/답
  구간을 곡선 폴리라인으로(카토그램 중엔 직선 폴백). 역참 지형(하서주랑=치롄·고비 사이 회랑, 헝두안 협곡)을
  barrier로 반영해 곡선이 실제 회랑을 따름.
- **모드 보존**: viewMode를 `localStorage("mongolMode")`에 저장/복원 → 무작위 뽑기 등 리런에도 탐험/순행 유지.
- **Phase 3 ORBIS풍 결과 패널(구현됨)**: 채점 시 점수 박스에 **구간별 표**(순서·구간·거리/비용) + 합계 + 컴퓨터 비교(gap%).
  map_view grade 핸들러의 `table.legs`. 지형 ON이면 '비용', OFF면 '거리' 단위.
- **편의 개선**: ①양자 계산(수십 초) 중에도 지도·백과사전이 안 흐려지고 상호작용 가능 — app.py에서
  iframe 담은 `stElementContainer`만 `:has(iframe)`로 opacity/pointer-events 강제(경고 등은 미관여).
  ②무작위 뽑기 시 즉시 순행 그리기 모드 — app.py가 `ss["force_mode"]="draw"` → build_map `force_mode` →
  iframe init이 localStorage보다 우선 적용. ③양자 auto-run은 ≤5 게이트, 무효해는 안내로 우아하게 처리.
- **통행 마스크(바다 + 제국 밖 = 통행불가)**: geobuild가 Natural Earth 육지/내해(hole)/호수를 스캔라인
  래스터화하고, **몽골 제국 최대영토(~1294) 경계 폴리곤(`EMPIRE_LL`) 밖도 통행불가로** 합쳐
  `geo.json["sea"]`(통행 비트마스크, terrain 격자와 동일 해상도)에 구움 → 통행가능 = 육지 ∧ 제국 안.
  (75 도시 모두 안, 인도·아라비아·서유럽·일본·동남아는 밖으로 검증.) terrain `_grid()`가 불가 셀에
  `SEA_PENALTY`(≈9) 추가 → 최소비용 경로가 바다·제국밖을 안 지나고 우회(카스피 우회, 고려는 요양 경유).
  도시 셀이 불가면 `_land_cell`로 인접 통행가능 셀 스냅(≤~7px). 마스크 비트는 무거워 iframe엔 미주입
  (app.py `GEO_VIEW`로 land/lakes/rivers만). `cost_from_center`도 격자 최소비용이라 카토그램도 일관.
  ※ 내해(카스피·아랄)는 land 폴리곤 hole → hole→물 처리 필수. 제국 경계 수정: geobuild `EMPIRE_LL` 편집 후 재빌드.
  ※ **제외존 `EXCLUDE_LL`**: 발칸·콘스탄티노플(비잔틴, 흑해 서안)은 제국 폴리곤 안이지만 통행불가로 빼서,
    아나톨리아↔크림/루스가 흑해 서쪽이 아니라 **캅카스(동쪽)로** 연결되게 함(역사적 '철문' 경로).
  ※ 순행 도시 수 슬라이더 2~30(과거 12). Brute>9·QAOA>5는 자동 폴백/안내. least_cost는 `_lcp` 캐시(선택 바뀔 때만).
- **남은 L3 후속**: 비대칭(ATSP), 강 도하/고개 corridor 세밀화. pedia.json 내용 보강은 사용자 몫.
- **실제 DEM 난이도 — 구현됨**: 난이도 = 1 + 경사·K(0.12) + 고도초과·K(1.4, >2500m) + 사막존.
  · 표고: **opentopodata ETOPO1**(1req/sec·100점/요청, 전위도)로 120×72 격자 샘플 → `_geocache/elev_120x72.json`에
    캐시(1회 ~130s, 재실행 무료). geobuild `build_difficulty()`가 표고→경사 후 232×140 난이도 그리드 생성.
  · 사막(평탄해 표고로 안 잡힘): `DESERTS_LL`(타클라마칸·고비·카라쿰·키질쿰·다쉬테카비르/루트·**시리아·아라비아북부**)
    실제 위치 가우시안 가산. ← "아라비아/사막 미구현" 해결.
  · 결과 난이도(검증): 평지 1.1, 사막 4~4.8, 히말라야/파미르 ~5, 티베트 ~6, 최대 9.6. 라우팅이 실제 산맥 우회·
    고개 통과·사막 우회. geo.json에 `diff`(base64, terrain 라우팅용)+`heat`(다운샘플, iframe 음영용) 구움.
  · terrain `_grid()`가 `diff`를 난이도 소스로 사용(`_USE_DEM`); 없으면 가우시안 `BARRIERS` 폴백(레거시 유지).
    음영 토글은 `GEO.heat`를 canvas→PNG 이미지로 렌더(예전 블롭 대체). 표고 격자/공식 조정은 geobuild에서 재빌드.
  · 추가 정밀화 여지: 더 고해상 표고, 토지피복 기반 사막, 강 도하/고개 미세조정.

## 12. ORBIS식 다지표 — 이동수단 × 우선순위 × 계절 (구현됨)
"거리≠시간≠비용". 난이도를 **두 성분**으로 분리해(geobuild가 `geo.json`에 `mtn`=경사+고도, `des`=사막 base64)
지표·수단·계절이 **다르게 가중** → 최적 경로 자체가 달라진다.
- `terrain.py`: `MODES`(**§14에서 페르소나로 재구성: 엘치·오르톡·관료단·포로단** — speed·rate·지형적성 mtnT/desT/mtnC/desC
  +seasonSens), `SEASONS`(봄/여름/가을/겨울: mtn·des 스케일+겨울 북방 한파), 가중 `MT,DT,MC,DC`(시간=산악 민감, 비용=사막 민감).
  `least_cost(coords, mode, priority, season)` → 선택지표 셀격자 Dijkstra → (선택지표 비용행렬 C, 곡선 경로,
  **쌍별 3지표(거리km·시간일·비용관)**). 최단=Σ거리(직선)·최속=산 우회·최저비용=사막 우회. `_grid_for`/`_mults` 캐시.
- `app.py`: 지형비용 ON 시 사이드바 **이동수단·우선순위·계절** 셀렉터. `_lcp` 캐시키에 셋 추가. solver는 C(선택지표)로
  TSP 최소화. 채점용 costs(선택지표)+`metrics`(구간별 3지표)+`orbis`(mode/priority/season/unit/pxkm) 주입.
- `map_view.py`: 결과표를 **거리·시간·비용 3열**로(최적화 지표 열 강조 `.hl`, 헤더 `.ohead`에 수단·우선순위·계절).
  구간 색 `legColor`는 **거리 우회비율**(경로km/직선km, 지표 무관)로. 곡선 경로는 PATHS 그대로.
- 검증: 같은 2도시 바그다드→사마르칸트 최속 2174km/45.8일 vs 최저비용 3367km/26729관(거리↑·비용↓), 파발마 26일 vs
  도보 212일, 낙타≠우마차 경로, 겨울 산악 시간↑ — 모두 분기 확인. E2E: 셀렉터→재계산→경로·결과표 변경, 콘솔0.
- 파라미터(MODES/SEASONS/MT·DT·MC·DC)는 terrain.py에서 조정. 성분은 geobuild 재빌드. OFF면 단순 유클리드.

## 13. 파라미터 밸런싱 측정 (2026-06-06)
코드 수정 전 측정 우선. 일회성 스크립트(`_measure*.py`)로 분기·현실성·난이도를 정량화 후 삭제. **결론 요약**:
- **잘 작동(되돌리지 말 것)**: 낙타=사막 관통 vs 말=우회(카슈가르→우르겐치 1580 vs 2238km, **+42%**), 지표 현실적
  (바그다드→사마르칸트 2174km, 낙타 34km/일, 파발마 프리미엄 비용), 계절 분기(겨울 4세트중 2개 경로변경),
  무작위 순회 페널티 median 36~78%.
- **수단이 TSP *순서*는 거의 안 바꿈**(사막세트+최저비용에서도 5중 1종류). 수단은 leg *모양*(최속 4/5·최저비용 3/5
  분기)·*지표값*만 바꾸고 순열 퍼즐은 불변. 의도된 한계로 수용(전략화하려면 적성 스프레드 확대 필요 — 미실시).
- **우선순위 교차 페널티 0~0.9%**(순서차원 무의미; 숫자만 바뀜). 미조정.
- **#2 "과잉 우회"는 사실상 버그 아님(측정으로 반증)**: 말/최저비용 우회 median 18%km→절약 28%관(효율 1.64),
  낙타는 우회 덜함(11%·효율 2.12). 극단 우회(야르칸드→우루무치 72%, 카슈가르→고창 54%)는 **타클라마칸/이란
  사막을 림으로 우회하는 역사적으로 옳은 실크로드 경로** — 직선 그은 플레이어가 감점되는 건 ORBIS 교훈(기능).
  진짜 무의미 우회는 사마르칸트→타라즈(8%/0.4%) 단 1건. **DC/desC 광역 재조정은 이 건강한 동작을 깨므로 금지.**
  (잡티만 없애려면 동률 타이브레이크용 미세 거리 바이어스가 옵션이나 영향 미미 — 미실시.)
- **#4 난이도 곡선(구현)**: 기본 4도시는 탐욕법(≈인간직관)=최적이라 trivial(NN-vs-최적 median 0%·p90 8~10%),
  격차는 n≥10에서 의미(median 2%·p90 17%). → `app.py` 기본 `sel`을 서향 실크로드 **8도시**(대도·상도·카라코룸·
  알말리크·사마르칸트·부하라·헤라트·바그다드)로, 슬라이더 기본 4→**8**, "8~12개에서 격차 최대" 안내 캡션 추가. E2E 검증.

## 14. 순행 주체(persona) 재구성 — #1 수단 전략화 (2026-06-06, 구현됨)
"이동수단"을 ORBIS식 **여행 주체(누가 가는가)**로 재구성. 각 집단이 지형·계절에 다르게 반응 → leg 모양·3지표가
강하게 캐릭터화되고 TSP 순서도 더 자주 갈린다. **설계 핵심: 오르톡(사막강세·산약점)과 포로단(산 상대강세·사막약점)의
지형 적성을 반대로 벌려 순열이 갈리게, 관료단은 둘 다 회피.** `terrain.MODES`(speed·rate·mtnT/desT/mtnC/desC +
**신규 `seasonSens`**=계절 스윙·한파 증폭계수):
- **엘치**(역참 특사) speed250·rate13·mtnT1.7·desT1.1·…·sens1.1 — 환마로 압도적 속도, 산악 둔화, 사막은 급수로 견딤, 막대한 비용.
- **오르톡**(공인 대상 길드) speed30·rate2.5·desT0.4·desC0.4·sens0.8 — 낙타 상단, **사막 관통**·산악 약점, 연중운행(계절 둔감).
- **관료단**(호구 조사, 기본 주체) speed40·rate5·mtnT2.1·desT1.7·mtnC1.8·desC1.6·**sens1.7** — 장부·서기·호위 대동,
  산·사막 모두 최악, 악천후 최취약. 플레이어 페르소나(순회 감찰관)에 가깝고 지형효과를 가장 잘 드러내 **기본값**.
- **포로단**(강제 이주) speed15·rate1·mtnT1.25·desT1.5·sens1.5 — 도보라 산은 상대적 통과·사막 가혹, 최저비용, 겨울 노출 취약.
- `seasonSens`는 `_mults`에서 `smtn=1+(S.mtn-1)*sens`, `sdes` 동형, `cold*=sens`로 적용(=1이면 기존과 동일).
- `MODE_DESC`(주체별 한줄설명) → app.py 사이드바 셀렉터 라벨 **"순행 주체"** + 선택시 캡션. map_view `.ohead`는 그대로 주체명 표시.
- **측정 검증**: 순서분기 1/5→**보통 2/4**(오르톡 vs 나머지 갈림). leg/지표 캐릭터화 강함 — 카슈가르→우르겐치 최저비용
  **오르톡 1580km 관통 vs 관료단 2288km(+45%) 우회**; 바그다드→사마르칸트 최속 엘치 24일/96k관 vs **포로단 424일**/7.7k관.
  E2E(preview): 셀렉터 4주체·관료단 기본·캡션, iframe ORBIS.mode=관료단·METRICS/PATHS 28쌍, 콘솔0.
- **알려진 튜닝 노브**: 포로단 산악 장거리 최악 케이스가 ~424일로 극단적(도보 nominal 15km/일 존중). 완화 원하면 speed↑ 또는 mtnT↓.
  순서분기를 더 키우려면 mtn/des 적성 스프레드를 더 벌리거나 MT/DT/MC/DC 대비 확대(아직 미실시).

## 15. 게임 시나리오 시스템 v1 — 단일 미션 + gap% 별점 (2026-06-06, 구현됨)
단발 채점 샌드박스 위에 **"칸의 명" 단일 임무 + 별(★) 등급**을 얹어 목표 있는 루프로. **단방향 흐름 보존**:
시나리오 정의=JSON, Python은 config 강제+주입만, 게임/별점/최고기록은 iframe JS+localStorage(콜백 없음).
- **`scenarios.json`**(신규, 사용자 편집): `_README`+`scenarios[]`. 각 항목 `{id,title,khan_command,persona,priority,
  season,cities[],start,terrain,stars:[a,b,c],lore}`. `stars`=gap% 임계(gap≤a→★★★,≤b→★★,≤c→★,그외 ☆; gap<0=★★★).
  persona/priority/season은 terrain.MODE_LIST/PRIORITY_LIST/SEASON_LIST와 일치해야. **빈 템플릿 2개**(실제 도시,
  서사 placeholder) 동봉 — 사용자가 title/khan_command/lore 채워 실제 임무화(재빌드 불필요, 새로고침만).
- **`app.py`**: SCENARIOS 로드, 사이드바 **맨 위 모드 토글** `radio("모드", ["🎲 자유 순행","⚔️ 순행 임무"], horizontal)`.
  **순행 임무** 선택 시에만 `selectbox("임무 선택", 제목들)` 노출(샌드박스 조작 전부 숨김) → sel/start/terrain_on/
  omode/opriority/oseason를 시나리오로 **고정**(읽기전용 마크다운), method는 **Brute(≤9)·아니면 고전**으로 공정 채점,
  `force_mode="draw"`. build_map에 신규 `scenario=` 메타 전달. (임무 없으면 warning 후 샌드박스로 폴백.)
  **자유 순행(기본)은 시나리오 분기 밖 → 기존 동작 100% 동일(회귀 보장).**
- **`map_view.py`**: build_map `scenario=None`+`%%SCENARIO%%`→`var SCENARIO`. 게임패널에 `.khan`('칸의 명') 카드,
  SCENARIO 있으면 draw 강제+패널 제목=임무명. grade 핸들러에 `gap` 호이스팅 후 별점 블록 추가: `starsFor(gap,th)`,
  `RANKS[s]`(재순행하라/명을받들었다/무난한순행/칸의칭송), `lore`(s>0), `localStorage["mongolScen:"+id]`에 max 별 저장·
  "(최고 N★)" 표기. **별점 코드는 `if(SCENARIO&&gap!=null)` 가드 뒤에만** → 자유 순행 결과표 불변.
- **E2E 검증(preview)**: 임무 선택 시 SELECTED=시나리오6도시·viewMode=draw·칸의명카드·임무고정 표시; 6도시 그려 채점→
  **★★☆(gap +6.1%가 [5,15,30]서 2★ 정확)**·등급·lore·localStorage best=2; 자유 순행 전환→SCENARIO=null·자유 UI 복귀·
  8도시. 콘솔0. ※Streamlit terrain/app 모듈 stale → 변경 후 **preview 서버 재시작** 필수(이번에도 겪음).
- **남은 단계**: 캠페인(시나리오 순서·총별 누적·해금, localStorage), 절대 예산/기한 목표, 특수 제약(폐쇄 고개/강 도하),
  사용자가 scenarios.json에 실제 미션·서사 기입(페르소나별 테마).

## 16. 배포 준비 — Streamlit Community Cloud (2026-06-06)
학교 프로젝트를 교내 홈페이지에 **고정 링크**로 걸기 위해 클라우드 배포(내 PC 무관 24시간). **게임(순행 임무)은 베타로 유지.**
- **타깃 = Streamlit Community Cloud**(무료, GitHub 연동, `...streamlit.app` 고정 URL). 배포 절차는 README "배포" 섹션.
- **Python 3.12 권장**: 로컬은 3.14인데 **Community Cloud는 3.9~3.13만** 지원 + qiskit 휠 호환. 고급설정에서 3.12 선택.
- **requirements.txt 핀**(테스트 환경 그대로): streamlit1.58.0·numpy2.4.6·networkx3.6.1·qiskit2.4.1·qiskit-optimization0.7.0.
- **QAOA 4도시 제한**: `app.py`에서 `len(sel)>4` 경고로 낮춤(기존 5). 25큐비트 상태벡터(≈500MB+)가 무료 1GB 인스턴스
  OOM 위험 → 16큐비트로. 실용 최적화는 고전·Brute라 영향 없음. 캡션·경고 문구도 "4개까지" 갱신.
- **게임 베타 표시**: 모드 토글 라벨 `⚔️ 순행 임무 (베타)` + 게임 모드 진입 시 "베타 — 시험 중" 캡션. `game_mode="임무" in mode` 유지.
- **`.streamlit/config.toml`**(신규): 양피지 테마(배경 #f3ece0·청록 #2f6f7a·serif) + headless·gatherUsageStats=false. 로컬 검증서 body배경 적용 확인.
- **`.gitignore`**(신규): `.venv/`·`__pycache__/`·**`_geocache/`**(빌드 전용 3.3MB, 런타임은 geo.json만)·`.streamlit/secrets.toml`·
  `.claude/settings.local.json`(개인 권한설정) 제외. `.claude/launch.json`·map_data.distorted.bak.json은 둠.
- **git**: `git init`+로컬 user(mongol-app, 사용자가 GitHub 푸시 전 본인 것으로 교체)+**초기 커밋 1개**(17파일, .venv/_geocache 제외 확인).
  미푸시 — 사용자가 GitHub 레포 만들어 `git remote add origin … && git push -u origin main` 후 share.streamlit.io 연결.
- **검증(preview)**: 베타 라벨·테마 배경 #f3ece0·QAOA 8도시서 "4개 이하만" 경고, 콘솔0. ※geo.json은 런타임 필수(커밋됨).

## 17. 역참(yam) 네트워크 — 티어2 #1 (2026-06-14, 구현됨)
"네트워크 위에서만 빠르다"는 ORBIS 본질 구현. 엘치(역참 특사)가 *역참 도로 위에서만* 압도적으로 빠르고
벗어나면 일반 기수가 된다. **설계: 별도 그래프가 아니라 기존 격자에 "도로 레이어"를 구워 Dijkstra가 자연히 도로를 선호.**
- **`geobuild.py`**: `YAM_LL`(주요 역참 본선 13개 lat/lon 폴리라인 — 초원로·대운하·하서주랑·타림 남북도·트란스
  옥시아나·호라산·캅카스 철문·볼가·루스 등). `build_yammask`(선 래스터화, 버퍼 R=1셀)→`geo.json["yam"]`(sea와 동일
  232×140 비트, 도로 셀 5.3%). 렌더용 `geo.json["yampaths"]`(13 SVG path, `to_d`). 재빌드는 결정적 → mtn/des/sea/heat
  불변·map_data.json 불변(검증). _geocache 캐시로 오프라인 재빌드.
- **`terrain.py`**: `_YAMBITS` 로드, `_is_road(i,j)`. `MODES`에 **`yamSpeed`**(도로 위 시간 배율): 엘치 0.32(+speed 250→**80**
  으로 낮춰 off-road=일반 기수, on-road≈250급)·오르톡 0.9·관료단 0.85·포로단 0.95. `_grid_for` **최속 분기에서만** 도로
  셀 시간비용 ×yamSpeed(라우팅이 도로 선호). **중요: `_path_metrics`에도 동일 도로 할인 적용**(보고 시간이 도로 속도
  반영 — 안 하면 경로는 도로 따라가나 표시 시간이 안 줄어듦. 이 버그 잡음). 도로는 *시간*만(거리·비용 무관).
- **`map_view.py`/`app.py`**: yam 노선을 강 아래 레이어에 **옅은 금색 점선**으로 렌더(GEO_VIEW에 `yampaths` 추가).
  라스터 비트(`yam`)는 terrain 전용 — iframe 미주입.
- **측정 검증**: 엘치 도로 점유율 8%→**97%**(대도→사마르칸트), 도로 위 실효 **82~92km/일** vs 오르톡 20·관료단 27·
  포로단 11(주체 차별화 극적). 엘치 최속 30일(도로) vs 최저비용 95일·최단 77일(도로 벗어나면 느림 — 내부 정합).
  솔버 Brute≤고전, 6도시 15쌍 경로/지표. E2E: yam 13노선 렌더·75도시·콘솔0.
- **튜닝 노브**: 엘치 `yamSpeed`/`speed`로 도로 실효속도 조절(현 ~90km/일). 노선 추가·수정=`geobuild.YAM_LL` 편집 후 재빌드.
- **남은 티어2**: 오아시스 소프트 페널티(보급), 교역 점수 레이어. 티어3: 연료 사거리(하드)·이윤 최적화·정치 시간축.

## 18. 스토리 모드 대확장 + 오프닝 시네마틱 + UX·사운드 (2026-06, 구현됨)

알파 이후 가장 큰 확장. 마르코 폴로 단일 스토리 + 역참 미니게임 + 인게임 타이틀 + 별자리/항해 오프닝 + UX·사운드.
모두 단방향 흐름 유지(Python 주입 / 게임 로직은 iframe JS 자기완결, 콜백 없음). 상세 맥락은 메모리 `mongol-tsp-game.md` 참고.

### 모드 선택을 인게임 타이틀로 이전 (사이드바 모드 라디오 제거)
- iframe이 Streamlit 재실행 불가(sandbox에 allow-top-navigation 없음)라 **두 모드 설정을 모두 주입**하고 JS로 전환.
- `app.py`: 사이드바는 **샌드박스 조정 전용**. 베이스 config=샌드박스(현행). `_story_bundle()`(@cache_data, scenarios[0]=폴로
  고정 → sel·start·terrain·answer[Brute≤9]·costs·paths·metrics·cr·orbis·scenario 전체 계산) → `STORY` 주입.
- `map_view.py` `window.__applyStory(S)`: 스토리 선택 시 메인 지도 전역(SELECTED/ANSWER/COSTS/PATHS/METRICS/ORBIS/
  SCENARIO/CR…)을 폴로로 교체 + 도시 강조(sel/dim/startcity·selring) 갱신 + 게임패널/칸의명 리셋 + __setMode("draw").
- 타이틀=별자리(`#opening.night`): 「칸이 명한 순행로」 큰 제목 + [📖 스토리 / 🎲 샌드박스] 2줄 버튼. 좌상단 **≡ 타이틀**
  로 복귀(localStorage `mongolEntered`로 샌드박스 리런 시 타이틀 스킵). 타이틀 동안 **부모 페이지 배경까지 밤하늘**(`__pageBg`,
  같은 출처 부모 DOM 접근, 모드 진입 시 복귀).

### 오프닝 시네마틱 (전용 실제 지도, 메인 지도 불변)
- **`openbuild.py` → `opening_map.json`**(둘 다 신규, 런타임/배포 필수): 캐시된 Natural Earth로 제노바~대도 해안선 + **75개
  도시** 투영(오프라인, 네트워크·메인 지도 재생성 불필요). 메인 `geo.json`/`map_data.json`과 무관한 별도 산출물.
- 흐름: 별자리(모드 선택) → **별→지도 전환(3.8s 느린 페이드, 별·도시 메타포)** → **제노바가 떠오르며 카메라 유도→클릭** →
  폴로 독백 → "고향" → **베네치아로 카메라 센터링+제노바 페이드아웃** → 클릭 → 베네치아 카드 → **줌아웃하며 75개 도시 등장
  ("수많은 도시", 넓은 뷰 유지)** → 대도 펄스 클릭 유도 → 클릭 시 **경로 잇기 애니메이션(카라반)** → 대도 도착 → "순행 시작" →
  본 지도 대도에서 줌아웃 리빌.
- 제노바·베네치아는 **오프닝 전용**(별자리·본 게임 지도엔 미표시 — opening_map에만, 본 SELECTED엔 없음). 노드는 등장 시점에만
  페이드인(OPENONLY={제노바,베네치아,대도}, activateNode가 1.0s 페이드+SMIL 펄스). beat 옵션: `focus`(카메라 대상,
  `cities`=줌아웃+75도시)·`next_node`/`next_hint`(클릭 진행)·`route_on_click`(클릭 후 경로 애니, rAF 일시정지 대비 폴백 타이머).
- **연출 텍스트는 플레이스홀더**: `scenarios.json`의 `opening.beats[]`/`closing`, `city_scenes.json`. 채우면 새로고침 반영.

### 역참로 2단계 미니게임 (`map_view.py` 내 전용 스테이지 `#relaystage`)
- 거시 순회 채점 후 "역참로 잇기" → 구간마다 다수 후보 중 **보급 사거리 내 최단 4개**를 잇는 미니-TSP(DP 최적과 비교, 사거리
  초과=빨강·감점). 향후 역참 종류 세분화 대비 노드에 type 필드.
- 스토리 모드: 구간 도착마다 **도시 풍경 연출**(`city_scenes.json`, 도시명 키) + 귀환 후 **칸께 고하다**(closing).

### 도착 연출 데이터 (`city_scenes.json`, 신규)
- `scenes[도시명]={title,lines[],img}`. img=null→회색 삽화 자리. 임무별 덮어쓰기는 scenarios의 `scenes`. 15개 플레이스홀더.

### UX·가독성 + 사운드
- 타이틀 큰 제목·2줄 버튼, 게임패널/연출/역참/백과사전 폰트·행간·대비 ↑, 호버, 지도 라벨 확대. 하단 안내 문구는 **`ℹ️ 도움말`
  익스팬더(기본 접힘)**로 축소(몰입).
- **사운드(`sounds/` 폴더)**: `page`(책 넘기는 소리)·`bgm`·`select`·`arrive`·`star`.(mp3/ogg/wav/m4a) 넣으면 자동 인식.
  `app.py` base64 인코딩 주입(무파일=무음·무오류, 별도 서버 설정 없이 로컬·배포 동일). 첫 클릭에 오디오 해제, 우상단 🔊 토글
  (localStorage). page-turn 훅=오프닝 beat·도착/보고 연출·백과사전 항목. **사용자가 CC0 등 음원 직접 추가**(sounds/README.md).

### 검증·주의
- 전 과정 preview MCP E2E + 콘솔0. ※Streamlit은 import 모듈(map_view/app/terrain) 변경 시 stale → **preview 서버 재시작** 필요.
- ※헤드리스 preview는 백그라운드에서 rAF 일시정지 → 애니메이션 검증은 폴백 타이머·프레임경과(eval 라운드트립)로.
- ※`st.components.v1.html` deprecation 경고(후일 `st.iframe` 이전 검토).
- **남은 일**: 연출/스토리 본문·삽화 채우기(플레이스홀더), 사운드 파일 추가, (파킹) 캠페인·역참 종류 세분화·교역 점수·ATSP.

### 18-추가. 오프닝 최종 다듬기 (2026-06-22)
- **타이틀 = 전 화면 밤하늘**: `__pageBg(true)`가 부모 페이지의 stApp·main·header·block-container·body 배경을
  `#070b1c`로(좌우 여백·상단 사이드바 토글 바까지). `#opening.night` 자체도 `#070b1c`(SVG 레터박스 여백 제거). 모드 진입 시 복귀.
  타이틀 하단 카드도 단색 `#070b1c`(그라데이션 제거). 별→지도 전환 3.8s(느리게). 모드 선택 시 카드 즉시 사라짐(opacity 0).
- **베네치아→대도 첫 여행 = 튜토리얼 노드 연결 씬**(`runTutorial`): "수많은 도시" → "여정을 시작하라" → route의 도시가
  **하나씩 떠오르며(펄스) 클릭 유도**, 각 클릭마다 **이전 지점→도시로 부드러운 곡선(2차 베지어)이 자라며 카라반 이동**.
  소제목 "첫 번째 여정". route·소제목은 `scenarios.json` cities beat의 `tutorial`(도시명 배열)·`tutorial_title`로 편집(도시
  좌표는 `opening_map.json`의 75개에서 이름 조회 — 이름 정확히! 예 "에르주룸"). 마지막 대도 클릭 후 대도 카드→리빌.
- ※부모 DOM·rAF는 같은 출처 가정(allow-same-origin)·헤드리스선 rAF 일시정지 → 곡선/이동은 폴백 타이머로 완성.
