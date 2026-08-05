"""Smoke tests for the CRP simulation scripts.

These run the shipped entry points end to end with a reduced packet count
and assert the behavioural properties the README advertises, so that future
changes to the routing or network code cannot silently break the prototype's
reference results.
"""
import contextlib
import io
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simulations import run_baseline_sim, run_cognitive_sim

PACKETS = 200


def run_sim(module):
    """Run a sim main() with a small packet budget and capture stdout."""
    module.NUM_PACKETS = PACKETS
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        module.main()
    return buf.getvalue()


class CognitiveSimSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = run_sim(run_cognitive_sim)

    def test_simulation_completes(self):
        self.assertIn("[SUCCESS] Phase 4: Comparative analysis complete.", self.output)

    def test_dumb_router_delivers_all_packets(self):
        self.assertIn(f"Success Rate: 100.00% ({PACKETS}/{PACKETS})", self.output)

    def test_cognitive_router_avoids_congested_link(self):
        # Second "Trips through Congested Link" line is the cognitive router.
        trips = re.findall(r"Trips through Congested Link: (\d+)/", self.output)
        self.assertEqual(len(trips), 2)
        cognitive_trips = int(trips[1])
        self.assertLess(
            cognitive_trips / PACKETS,
            0.05,
            "cognitive router should use the congested link in <5% of trips",
        )

    def test_cognitive_router_reports_latency_gain(self):
        match = re.search(r"Performance Improvement \(Lower Latency\): ([\d.]+)%", self.output)
        self.assertIsNotNone(match, "expected a latency improvement summary line")
        self.assertGreater(float(match.group(1)), 0.0)

    def test_cognitive_router_delivers_some_packets(self):
        match = re.search(r"COGNITIVE ROUTER \(CRP\) ---\n  Success Rate: ([\d.]+)%", self.output)
        self.assertIsNotNone(match)
        self.assertGreater(float(match.group(1)), 0.0)


class BaselineSimSmokeTest(unittest.TestCase):
    def test_baseline_finds_west_to_east_route(self):
        output = run_sim(run_baseline_sim)
        self.assertIn("GATEWAY_WEST", output)
        self.assertIn("GATEWAY_EAST", output)
        self.assertIn("[SUCCESS] Phase 2: Baseline 'Dumb' Router executed.", output)


if __name__ == "__main__":
    unittest.main()
