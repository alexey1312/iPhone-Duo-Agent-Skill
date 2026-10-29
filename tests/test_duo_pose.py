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


POSTURE = """{
  "device": {"udid": "DUO1", "name": "iPhone Duo"},
  "angle": 90.0,
  "orientation": "landscape-left",
  "activeDisplay": "LCD-1",
  "displays": [
    {"name": "LCD", "id": 1, "primary": true, "active": false, "backlight": "off", "rotation": "rot0", "size": [1398, 2034], "scale": 3},
    {"name": "LCD-1", "id": 3, "primary": false, "active": true, "backlight": "activeOn", "rotation": "rot0", "size": [2007, 2853], "scale": 3}
  ]
}"""


class PostureTests(unittest.TestCase):
    def test_parses_hinge_posture(self) -> None:
        posture = duo_pose.parse_posture(POSTURE)
        self.assertEqual(posture, duo_pose.Posture(90.0, "landscape-left", "inner", "rot0"))

    def test_the_primary_display_is_the_outer_one(self) -> None:
        folded = POSTURE.replace('"primary": true, "active": false', '"primary": true, "active": true')
        folded = folded.replace('"primary": false, "active": true', '"primary": false, "active": false')
        self.assertEqual(duo_pose.parse_posture(folded).display, "outer")

    def test_no_active_display(self) -> None:
        posture = duo_pose.parse_posture('{"angle": null, "orientation": "portrait", "displays": []}')
        self.assertIsNone(posture.display)
        self.assertIsNone(posture.angle)

    def test_versions(self) -> None:
        self.assertEqual(duo_pose.parse_version("0.3.0\n"), (0, 3, 0))
        self.assertLess(duo_pose.parse_version("0.2.0"), duo_pose.MIN_HINGE)
        self.assertIsNone(duo_pose.parse_version("hinge: command not found"))


class PoseTests(unittest.TestCase):
    def test_every_matrix_pose_the_simulator_can_reach(self) -> None:
        rows = {pose.row for pose in duo_pose.POSES.values()}
        self.assertEqual(rows, {"P1", "P2", "P3", "P4", "P5", "P6"})

    def test_one_device_orientation_rotates_the_displays_differently(self) -> None:
        self.assertEqual(duo_pose.POSES["closed-landscape"].rotation, "rot270")
        self.assertEqual(duo_pose.POSES["flat-portrait"].rotation, "rot0")
        self.assertEqual(duo_pose.POSES["closed-landscape"].orientation,
                         duo_pose.POSES["flat-portrait"].orientation)

    def test_default_shots_are_known_poses(self) -> None:
        for name in duo_pose.DEFAULT_SHOTS.split(","):
            with self.subTest(name):
                self.assertIn(name, duo_pose.POSES)

    def test_names_and_degrees(self) -> None:
        self.assertEqual(duo_pose.pose_for("closed").angle, 0.0)
        self.assertEqual(duo_pose.pose_for("tabletop"), duo_pose.Pose(90.0, "landscape-left", "rot0", "P6"))
        degrees = duo_pose.pose_for("120")
        self.assertEqual((degrees.angle, degrees.orientation, degrees.rotation), (120.0, None, None))

    def test_rejects_unknown_pose_and_out_of_range(self) -> None:
        for name in ("tent", "181", "-5"):
            with self.subTest(name), self.assertRaises(duo_pose.PoseError):
                duo_pose.pose_for(name)

    def test_reached_allows_the_simulators_smoothing(self) -> None:
        self.assertTrue(duo_pose.reached(179, 174.1))
        self.assertFalse(duo_pose.reached(90, 120))
        self.assertFalse(duo_pose.reached(90, None))

    def test_in_pose_checks_the_rotation_too(self) -> None:
        tabletop = duo_pose.POSES["tabletop"]
        self.assertTrue(duo_pose.in_pose(tabletop, duo_pose.Posture(90.0, "landscape-left", "inner", "rot0")))
        self.assertFalse(duo_pose.in_pose(tabletop, duo_pose.Posture(90.0, "portrait", "inner", "rot90")))
        self.assertFalse(duo_pose.in_pose(tabletop, None))


class CommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.commands: list[list[str]] = []
        self.original_run = duo_pose.run
        duo_pose.run = lambda command, check=True: self.commands.append(command)  # type: ignore[assignment]

    def tearDown(self) -> None:
        duo_pose.run = self.original_run

    def test_hinge_moves_sweep_instead_of_jumping(self) -> None:
        duo_pose.Simulator("hinge", "DUO1", 0.6).move_hinge(0, 174.1)
        self.assertEqual(self.commands, [["hinge", "-d", "DUO1", "sweep", "174.1", "0", "0.6"]])

    def test_an_unknown_angle_falls_back_to_set(self) -> None:
        duo_pose.Simulator("hinge", "DUO1").move_hinge(90, None)
        self.assertEqual(self.commands, [["hinge", "-d", "DUO1", "set", "90"]])

    def test_no_move_when_already_there(self) -> None:
        duo_pose.Simulator("hinge", "DUO1").move_hinge(90, 90.2)
        self.assertEqual(self.commands, [])

    def test_every_hinge_command_names_the_device(self) -> None:
        sim = duo_pose.Simulator("hinge", "DUO1")
        sim.move_hinge(180, 0)
        sim.orient("landscape-left")
        for command in self.commands:
            self.assertEqual(command[1:3], ["-d", "DUO1"])


class DisplayTests(unittest.TestCase):
    def test_displays_are_named_explicitly(self) -> None:
        self.assertEqual(duo_pose.DISPLAYS["outer"], ["--display=1"])
        self.assertEqual(duo_pose.DISPLAYS["inner"], ["--display=3"])


if __name__ == "__main__":
    unittest.main()
