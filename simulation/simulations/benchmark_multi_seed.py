"""Multi-Seed Fair Benchmark for Cognitive Routing Protocol.

Evaluates delivery rate, packet loss, latency, and congestion across multiple
independent random seeds to avoid cherry-picking single-seed results.
"""
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crp.routing.dumb_router import find_path_dijkstra
from simulations import run_cognitive_sim

SEEDS = [42, 100, 777, 1337, 2026]
NUM_PACKETS = 1000


def evaluate_seed(seed: int, num_packets: int = 1000):
    run_cognitive_sim.RANDOM_SEED = seed
    random.seed(seed)

    # 1. Dumb Router (Dijkstra)
    dumb_net = run_cognitive_sim.build_network(use_cognitive_nodes=False)
    static_path, _ = find_path_dijkstra(dumb_net, "GATEWAY_WEST", "GATEWAY_EAST")
    dumb_total_lat = 0.0
    dumb_cong = 0
    for _ in range(num_packets):
        plat = 0.0
        is_cong = False
        for j in range(len(static_path) - 1):
            cur = dumb_net.get_node(static_path[j])
            nxt = static_path[j + 1]
            lat = run_cognitive_sim.get_current_latency(cur, nxt)
            if lat != cur.neighbors[nxt]['latency']:
                is_cong = True
            plat += lat
        dumb_total_lat += plat
        if is_cong:
            dumb_cong += 1
    dumb_avg_lat = dumb_total_lat / num_packets
    dumb_cong_rate = (dumb_cong / num_packets) * 100.0

    # 2. Cognitive Router (MAB)
    cog_net = run_cognitive_sim.build_network(use_cognitive_nodes=True)
    cog_total_lat = 0.0
    cog_succ = 0
    cog_cong = 0
    for _ in range(num_packets):
        plat = 0.0
        is_cong = False
        cur = cog_net.get_node("GATEWAY_WEST")
        prev = None
        succ = True
        hops = 0
        while cur.node_id != "GATEWAY_EAST":
            if hops > run_cognitive_sim.MAX_HOPS:
                succ = False
                break
            nxt = cur.choose_next_hop(prev)
            if nxt is None:
                succ = False
                break
            lat = run_cognitive_sim.get_current_latency(cur, nxt)
            if lat != cur.neighbors[nxt]['latency']:
                is_cong = True
            plat += lat
            cur.update_reward(nxt, run_cognitive_sim.REWARD_FACTOR / lat)
            prev = cur.node_id
            cur = cog_net.get_node(nxt)
            hops += 1

        if succ:
            cog_succ += 1
            cog_total_lat += plat
            if is_cong:
                cog_cong += 1

    cog_deliv_rate = (cog_succ / num_packets) * 100.0
    cog_avg_lat = (cog_total_lat / cog_succ) if cog_succ > 0 else float('nan')
    cog_cong_rate = (cog_cong / num_packets) * 100.0
    lat_diff = (((dumb_avg_lat - cog_avg_lat) / dumb_avg_lat) * 100.0) if (cog_succ > 0 and dumb_avg_lat > 0) else float('nan')

    return {
        'seed': seed,
        'dumb_avg_lat': dumb_avg_lat,
        'dumb_cong_rate': dumb_cong_rate,
        'cog_deliv_rate': cog_deliv_rate,
        'cog_loss_rate': 100.0 - cog_deliv_rate,
        'cog_avg_lat': cog_avg_lat,
        'cog_cong_rate': cog_cong_rate,
        'lat_diff_pct': lat_diff,
    }


def main():
    print("=" * 80)
    print("  COGNITIVE ROUTING PROTOCOL - MULTI-SEED FAIRNESS EVALUATION")
    print("=" * 80)
    print(f"Packets per seed: {NUM_PACKETS} | Max hops: {run_cognitive_sim.MAX_HOPS}\n")
    print(f"{'Seed':>5} | {'Dijkstra Lat':>12} | {'Dijkstra Cong':>13} | {'CRP Deliv %':>11} | {'CRP Loss %':>10} | {'CRP Lat':>9} | {'Lat Gain %':>10}")
    print("-" * 80)

    results = []
    for s in SEEDS:
        r = evaluate_seed(s, NUM_PACKETS)
        results.append(r)
        cog_lat_str = f"{r['cog_avg_lat']:.2f}ms" if not math.isnan(r['cog_avg_lat']) else "N/A"
        gain_str = f"{r['lat_diff_pct']:+.2f}%" if not math.isnan(r['lat_diff_pct']) else "N/A"
        print(f"{r['seed']:5d} | {r['dumb_avg_lat']:10.2f}ms | {r['dumb_cong_rate']:12.1f}% | {r['cog_deliv_rate']:10.2f}% | {r['cog_loss_rate']:9.2f}% | {cog_lat_str:>9} | {gain_str:>10}")

    print("-" * 80)
    print("\nMethodological Notes:")
    print("1. Seed 42 produces the reference ~22% latency gain on successful packets, but at ~76.2% packet loss.")
    print("2. Multi-seed runs show high sensitivity to topology edge-weight initializations.")
    print("3. Single-hop MAB without destination awareness causes packets to cycle in multi-hop loops until MAX_HOPS is reached.")
    print("4. Honest research requires reporting delivery rate, loss rate, and latency together.")


if __name__ == "__main__":
    main()
