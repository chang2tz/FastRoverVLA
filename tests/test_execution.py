import math
import unittest

from fastrovervla import FastRoverPolicy, FrameContext, PolicyConfig, RefreshConfig
from fastrovervla.geometry import integrate
from fastrovervla.refresh import calibrate_scales, roughness


class ExecutionTests(unittest.TestCase):
    def test_callback_is_only_invoked_at_k_plus_one_intervals(self):
        policy = FastRoverPolicy(refresh=RefreshConfig(mode="fixed", fixed_k=3))
        requests = []
        def planner(context):
            requests.append(context.observation)
            return [(1.0, 0.0)] * 6
        output = [policy.step(FrameContext("a", 1.0, 0.0, observation=i), planner) for i in range(10)]
        self.assertEqual(requests, [0, 4, 8])
        self.assertEqual([r.reuse_age for r in output], [0, 1, 2, 3, 0, 1, 2, 3, 0, 1])
        # A different scene must never inherit a stale buffer.
        self.assertTrue(policy.step(FrameContext("b", 1.0, 0.0, observation=10), planner).refreshed)

    def test_correction_is_written_back(self):
        cfg = PolicyConfig(alpha=1.0, beta=0.5, speed_step=None)
        policy = FastRoverPolicy(cfg, RefreshConfig(mode="fixed", fixed_k=8))
        first = policy.step(FrameContext("a", 0.0, 0.0), lambda _: [(2.0, 0.2)] * 6)
        second = policy.step(FrameContext("a", 0.0, 0.0), lambda _: self.fail("unexpected request"))
        self.assertEqual(first.actions[0], (1.0, 0.1))
        self.assertEqual(second.actions[0], (0.5, 0.05))

    def test_adaptive_threshold_and_short_output_use_unpadded_actions(self):
        rule = RefreshConfig(mode="adaptive", short_k=2, long_k=5, threshold=1.0,
                             speed_scale=0.25, curvature_scale=1.0)
        self.assertEqual(rule.budget([(1.0, 0.0), (1.25, 0.0)]), 2)
        self.assertEqual(rule.budget([(1.0, 0.0)]), 5)
        self.assertEqual(roughness([]), (1.0, 1.0))
        p = FastRoverPolicy(PolicyConfig(alpha=1.0, beta=1.0, speed_step=None), rule)
        result = p.step(FrameContext("a", 1.0, 0.0), lambda _: [(1.25, 0.0)])
        self.assertEqual(result.actions, ((1.25, 0.0),) * 6)
        self.assertEqual(result.reuse_budget, 5)

    def test_empty_output_falls_back_to_current_motion(self):
        result = FastRoverPolicy().step(FrameContext("a", 1.5, -0.1), lambda _: [])
        self.assertTrue(result.used_motion_fallback)
        self.assertEqual(result.parsed_actions, 0)
        self.assertEqual(result.actions, ((1.5, -0.1),) * 6)

    def test_bound_and_previous_heading_integration(self):
        policy = FastRoverPolicy(PolicyConfig(alpha=1.0, beta=1.0, speed_step=0.25))
        result = policy.step(FrameContext("a", 0.0, 0.0), lambda _: [(10.0, 0.1)] * 6)
        self.assertEqual([a[0] for a in result.actions], [0.25, 0.5, 0.75, 1.0, 1.25, 1.5])
        self.assertEqual(integrate([(2.0, 1.0)], 0.5), [(1.0, 0.0)])

    def test_invalid_values_are_rejected(self):
        with self.assertRaises(ValueError):
            PolicyConfig(beta=math.nan)
        with self.assertRaises(ValueError):
            RefreshConfig(speed_scale=0)
        with self.assertRaises(ValueError):
            FastRoverPolicy().step(FrameContext("a", 1.0, 0.0), lambda _: [(math.nan, 0)])
        with self.assertRaises(ValueError):
            FastRoverPolicy().step(FrameContext("a", 1.0, 0.0), lambda _: [], force_refresh=False)

    def test_calibration_is_validation_only(self):
        self.assertEqual(calibrate_scales([[(1.0, 0.0)], [(1.0, 0.0)]]), (1e-4, 1e-4))
        with self.assertRaises(ValueError):
            calibrate_scales([])


if __name__ == "__main__":
    unittest.main()
