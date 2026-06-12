# -*- coding: utf-8 -*-
"""순행 경로 최적화 솔버: 고전(NN+2-opt), Brute Force, 양자(QAOA).
거리는 지도상의 2D 좌표(상대 위치) 기준."""
import math, itertools, time
import numpy as np


def distance_matrix(coords):
    n = len(coords); D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                D[i, j] = math.hypot(coords[i][0]-coords[j][0], coords[i][1]-coords[j][1])
    return D


def route_length(order, D):
    return float(sum(D[order[k], order[(k+1) % len(order)]] for k in range(len(order))))


def nearest_neighbor(D, start=0):
    n = len(D); unv = set(range(n)); order = [start]; unv.discard(start); cur = start
    while unv:
        nxt = min(unv, key=lambda j: D[cur, j]); order.append(nxt); unv.discard(nxt); cur = nxt
    return order


def two_opt(order, D):
    best = order[:]; improved = True
    while improved:
        improved = False
        for i in range(1, len(best)-1):
            for j in range(i+1, len(best)):
                if j-i == 1:
                    continue
                cand = best[:i] + best[i:j][::-1] + best[j:]
                if route_length(cand, D) < route_length(best, D) - 1e-9:
                    best = cand; improved = True
    return best


def solve_classical(coords, C=None):
    D = C if C is not None else distance_matrix(coords)
    t0 = time.perf_counter()
    order = two_opt(nearest_neighbor(D, 0), D)
    return order, route_length(order, D), time.perf_counter()-t0


def solve_bruteforce(coords, C=None):
    D = C if C is not None else distance_matrix(coords)
    n = len(coords); t0 = time.perf_counter()
    best, bestL = None, float("inf")
    for perm in itertools.permutations(range(1, n)):
        o = [0]+list(perm); L = route_length(o, D)
        if L < bestL:
            bestL, best = L, o
    return best, bestL, time.perf_counter()-t0


def solve_qaoa(coords, reps=2, maxiter=100, C=None):
    """선택 도시(보통 4개)에 대한 TSP를 QAOA로. 실패/무효해면 (None, info).
    C: 선택적 대칭 비용행렬(지형비용). None이면 좌표의 유클리드 거리."""
    info = {}
    try:
        import networkx as nx
        from qiskit.primitives import StatevectorSampler
        from qiskit_optimization.applications import Tsp
        from qiskit_optimization.algorithms import MinimumEigenOptimizer
        from qiskit_optimization.minimum_eigensolvers import QAOA
        from qiskit_optimization.optimizers import COBYLA
    except Exception as e:  # noqa: BLE001
        info["error"] = f"qiskit import 실패: {e}"; return None, info
    try:
        n = len(coords); D = C if C is not None else distance_matrix(coords)
        scale = D.max() if D.max() > 0 else 1.0  # 정규화 -> 제약 페널티 상대적 강화
        G = nx.Graph()
        for i in range(n):
            G.add_node(i)
        for i in range(n):
            for j in range(i+1, n):
                G.add_edge(i, j, weight=float(D[i, j]/scale))
        tsp = Tsp(G); qp = tsp.to_quadratic_program()
        info["n_qubits"] = n*n
        sampler = StatevectorSampler()
        qaoa = QAOA(sampler=sampler, optimizer=COBYLA(maxiter=maxiter), reps=reps)
        opt = MinimumEigenOptimizer(qaoa)
        t0 = time.perf_counter(); res = opt.solve(qp); info["elapsed"] = time.perf_counter()-t0
        mat = np.array(res.x, dtype=float).reshape((n, n))  # [도시, 순서]
        order, feasible = [], True
        for k in range(n):
            sel = np.where(mat[:, k] > 0.5)[0]
            if len(sel) != 1:
                feasible = False; break
            order.append(int(sel[0]))
        if feasible and sorted(order) != list(range(n)):
            feasible = False
        info["feasible"] = feasible
        if not feasible:
            info["note"] = "QAOA가 제약을 만족하는 유효 경로를 못 찾음. reps/maxiter를 올려보세요."
            return None, info
        info["length"] = route_length(order, D)
        return order, info
    except Exception as e:  # noqa: BLE001
        info["error"] = f"QAOA 실행 실패: {e}"; return None, info
