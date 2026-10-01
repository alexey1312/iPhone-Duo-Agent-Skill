"""Tests for scripts/duo_pose.py that never touch a simulator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import duo_pose  # noqa: E402

LISTING = {
    "devices": {
        "com.apple.CoreSimulator.SimRuntime.iOS-27-1": [
            {"udid": "AAAA", "name": "iPhone 17 Pro", "state": "Booted",
             "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro"},
            {"udid": "DUO1", "name": "iPhone Duo", "state": "Booted",
             "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-Duo"},
            {"udid": "DUO2", "name": "iPhone Duo (2)", "state": "Shutdown",
             "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-Duo"},
        ]
    }
}


class DeviceSelectionTests(unittest.TestCase):
    def test_only_duo_simulators_are_candidates(self) -> None:
        self.assertEqual([d.udid for d in duo_pose.duo_devices(LISTING)], ["DUO1", "DUO2"])

    def test_picks_the_booted_duo_not_the_first_booted_simulator(self) -> None:
        devices = duo_pose.duo_devices(LISTING)
        self.assertEqual(duo_pose.pick_device(devices, None).udid, "DUO1")

    def test_named_device_must_be_booted(self) -> None:
        devices = duo_pose.duo_devices(LISTING)
        with self.assertRaisesRegex(duo_pose.PoseError, "not booted"):
            duo_pose.pick_device(devices, "DUO2")

    def test_non_duo_device_is_refused(self) -> None:
        devices = duo_pose.duo_devices(LISTING)
        with self.assertRaisesRegex(duo_pose.PoseError, "no iPhone Duo simulator matches"):
            duo_pose.pick_device(devices, "AAAA")

    def test_two_booted_duos_need_an_explicit_choice(self) -> None:
        devices = [duo_pose.Device("DUO1", "iPhone Duo", True), duo_pose.Device("DUO2", "iPhone Duo (2)", True)]
        with self.assertRaisesRegex(duo_pose.PoseError, "--device"):
            duo_pose.pick_device(devices, None)

    def test_no_duo_at_all(self) -> None:
        with self.assertRaisesRegex(duo_pose.PoseError, "Xcode 27.1"):
            duo_pose.pick_device([], None)


class AngleTests(unittest.TestCase):
    def test_parses_devicectl_output(self) -> None:
        output = "Monitoring hinge angle for iPhone Duo...\nAngle: 90.0°\nAngle: 91.5°\n"
        self.assertEqual(duo_pose.parse_angle(output), 90.0)

    def test_parses_a_decimal_comma(self) -> None:
        self.assertEqual(duo_pose.parse_angle("Angle: 174,05°"), 174.05)

    def test_no_angle(self) -> None:
        self.assertIsNone(duo_pose.parse_angle("error: device not found"))

    def test_pose_names_and_degrees(self) -> None:
        self.assertEqual(duo_pose.pose_angle("closed"), 0.0)
        self.assertEqual(duo_pose.pose_angle("book"), 90.0)
        self.assertEqual(duo_pose.pose_angle("flat"), 180.0)
        self.assertEqual(duo_pose.pose_angle("120"), 120.0)

    def test_rejects_unknown_pose_and_out_of_range(self) -> None:
        for pose in ("tabletop", "181", "-5"):
            with self.subTest(pose), self.assertRaises(duo_pose.PoseError):
                duo_pose.pose_angle(pose)

    def test_reached_allows_the_simulators_smoothing(self) -> None:
        self.assertTrue(duo_pose.reached(179, 174.1))
        self.assertFalse(duo_pose.reached(90, 120))
        self.assertFalse(duo_pose.reached(90, None))


class DisplayTests(unittest.TestCase):
    def test_displays_are_named_explicitly(self) -> None:
        self.assertEqual(duo_pose.DISPLAYS["outer"], ["--display=1"])
        self.assertEqual(duo_pose.DISPLAYS["inner"], ["--display=3"])

    def test_closed_shows_the_outer_display(self) -> None:
        self.assertEqual(duo_pose.expected_display(0), "outer")
        self.assertEqual(duo_pose.expected_display(90), "inner")


if __name__ == "__main__":
    unittest.main()
