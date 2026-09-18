# Research Notes: Simulation Dynamics & Fairness Analysis

## Overview
This document records the empirical analysis of the Cognitive Routing Protocol (CRP) prototype simulator, specifically addressing the interaction between local Multi-Armed Bandit (MAB / UCB1) reinforcement learning and multi-hop network topologies.

## Empirical Findings

### 1. Multi-Seed Performance Matrix
When evaluating 1,000 packets per trial across diverse pseudorandom generator seeds, the protocol exhibits significant sensitivity to network edge initialization:

| Seed | Dijkstra Latency | Dijkstra Congestion | CRP Delivery % | CRP Loss % | CRP Latency (Delivered) | Latency Difference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **42** (Ref) | 71.79 ms | 37.3% | 23.80% | 76.20% | 55.94 ms | **+22.08%** |
| **100** | 79.95 ms | 40.1% | 0.20% | 99.80% | 170.02 ms | -112.65% |
| **777** | 89.35 ms | 40.8% | 0.80% | 99.20% | 313.54 ms | -250.91% |
| **1337** | 76.10 ms | 39.4% | 100.00% | 0.00% | 128.27 ms | -68.55% |
| **2026** | 86.50 ms | 38.8% | 2.20% | 97.80% | 299.87 ms | -246.67% |

### 2. Root Cause Analysis: Local MAB vs Global Topology
The mechanism driving this distribution consists of two factors:

1. **Immediate 1-Hop Memory vs Multi-Hop Cycles**:
   - `CognitiveNode.choose_next_hop` filters only `prev_node_id` (`nid != prev_node_id`).
   - While this prevents immediate 2-node bounce (`A -> B -> A`), it permits 3-node or larger cycles (`A -> B -> C -> A`).
   - Once trapped in a cyclic subgraph, packets traverse links repeatedly until exhausting `MAX_HOPS = 25`, after which the packet is dropped as failed.

2. **Greedy Link-Local Rewards vs Destination Progress**:
   - Node reward is calculated as `REWARD_FACTOR / link_latency`.
   - The reward is granted immediately upon traversal of a low-latency edge, regardless of whether that hop moves the packet closer to `GATEWAY_EAST`.
   - In certain topologies (e.g. seeds 100, 777), low-latency internal links form an attractive local reward trap that actively reinforces cyclic behavior.

### 3. Latency Metric Context
- At seed 42, the reported **~22% latency improvement** applies strictly to the subset of packets that successfully reach the destination gateway without getting caught in cycles (~23.8% of total traffic).
- For packets that exit the cycle trap or find the direct path, avoiding the 10x congestion link (`NODE_2 <-> NODE_3`) does result in faster packet transit.
- However, reporting latency improvements without simultaneously reporting packet delivery rates or multi-seed bounds would constitute cherry-picking.

## Future Protocol Directions

To bridge the delivery gap while retaining adaptive congestion avoidance, future iterations should incorporate:
1. **Destination-Aware Reinforcement Learning (Q-Routing)**:
   - State should incorporate destination target, maintaining Q-values per `(destination, neighbor)`.
2. **Loop Suppression Mechanisms**:
   - Packet header hop-tracing or Bloom filter visited-set tracking.
   - Negative rewards (penalties) for packets hitting TTL / hop thresholds.
3. **Directed Acyclic Graph (DAG) Constraints**:
   - Combining distance-vector bounds with cognitive bandit exploration so nodes only explore forward-progressing neighbors.
