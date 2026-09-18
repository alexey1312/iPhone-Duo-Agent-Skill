from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "sdk_api_check.py"
SPEC = importlib.util.spec_from_file_location("sdk_api_check", SCRIPT)
assert SPEC and SPEC.loader
sdk_api_check = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sdk_api_check
SPEC.loader.exec_module(sdk_api_check)


def make_fake_sdk(root: Path) -> Path:
    # Synthetic SDK. The script never parses this name -- `--sdk` short-circuits
    # `--show-sdk-version` -- so naming it after a release would only go stale.
    # The assertions below cover the availability extractor, not any real SDK.
    sdk = root / "iPhoneOS.sdk"
    uikit = sdk / "System/Library/Frameworks/UIKit.framework"
    (uikit / "Headers").mkdir(parents=True)
    (uikit / "Headers/UIBarMinimization.h").write_text(
        "/// Access this configuration through navigationBarMinimization\n"
        "@property (nonatomic, readwrite, copy) UIBarMinimization *navigationBarMinimization "
        "API_AVAILABLE(ios(27.0));\n",
        encoding="utf-8",
    )
    swiftui = sdk / "System/Library/Frameworks/SwiftUI.framework/Modules/SwiftUI.swiftmodule"
    swiftui.mkdir(parents=True)
    (swiftui / "arm64-apple-ios.swiftinterface").write_text(
        "@available(iOS 27.1, *)\npublic func visibilityPriority(_ p: Priority) -> some ToolbarContent\n",
        encoding="utf-8",
    )
    # A second architecture must not be double counted or preferred.
    (swiftui / "x86_64-apple-ios-simulator.swiftinterface").write_text("axisBehavior\n", encoding="utf-8")
    # A framework with no Swift interface, declaring only an Objective-C constant.
    # The Swift name is synthesized by the importer and appears in no file on disk.
    avf = sdk / "System/Library/Frameworks/AVFoundation.framework/Headers"
    avf.mkdir(parents=True)
    # Laid out as AVFoundation really lays it out: a HeaderDoc block with no
    # leading `*` on its lines, and the previous constant's availability just above.
    (avf / "AVCaptureDevice.h").write_text(
        "/*!\n @constant AVCaptureDeviceTypeBuiltInUltraWideCamera\n    Older camera.\n */\n"
        "AVF_EXPORT AVCaptureDeviceType const AVCaptureDeviceTypeBuiltInUltraWideCamera "
        "API_AVAILABLE(ios(13.0));\n"
        "\n"
        "/*!\n @constant AVCaptureDeviceTypeBuiltInOuterUltraWideCamera\n    Outer camera.\n */\n"
        "AVF_EXPORT AVCaptureDeviceType const AVCaptureDeviceTypeBuiltInOuterUltraWideCamera "
        "API_AVAILABLE(ios(27.1));\n",
        encoding="utf-8",
    )
    return sdk


class SdkApiCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.sdk = make_fake_sdk(Path(self._directory.name))

    def tearDown(self) -> None:
        self._directory.cleanup()

    def test_found_and_missing_symbols(self) -> None:
        symbols = [
            sdk_api_check.Symbol("navigationBarMinimization", "navigation", "iOS 27.0"),
            sdk_api_check.Symbol("visibilityPriority", "bars", "iOS 27"),
            sdk_api_check.Symbol("axisBehavior", "bars", "iOS 27.1"),
        ]
        rows = {row["symbol"]: row for row in sdk_api_check.check(self.sdk, symbols)["symbols"]}
        self.assertTrue(rows["navigationBarMinimization"]["found"])
        self.assertEqual(rows["navigationBarMinimization"]["frameworks"], ["UIKit"])
        self.assertFalse(rows["axisBehavior"]["found"], "only the preferred interface is read")
        self.assertTrue(rows["visibilityPriority"]["found"])

    def test_declaration_skips_documentation_lines(self) -> None:
        symbols = [sdk_api_check.Symbol("navigationBarMinimization", "navigation", "iOS 27.0")]
        row = sdk_api_check.check(self.sdk, symbols)["symbols"][0]
        self.assertTrue(row["declaration"]["line"].startswith("@property"))
        self.assertEqual(row["declaration"]["availability"], "API_AVAILABLE(ios(27.0)")

    def test_swift_availability_from_previous_line(self) -> None:
        symbols = [sdk_api_check.Symbol("visibilityPriority", "bars", "iOS 27")]
        row = sdk_api_check.check(self.sdk, symbols)["symbols"][0]
        self.assertEqual(row["declaration"]["availability"], "@available(iOS 27.1, *)")

    def test_command_line_json(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            status = sdk_api_check.main(["--sdk", str(self.sdk), "--symbol", "axisBehavior", "--format", "json"])
        report = json.loads(buffer.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(report["symbols"][0]["symbol"], "axisBehavior")
        self.assertFalse(report["symbols"][0]["found"])

    def test_markdown_warns_about_missing_symbols(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            sdk_api_check.main(["--sdk", str(self.sdk), "--symbol", "axisBehavior"])
        self.assertIn("Do not write code against them", buffer.getvalue())

    def test_objective_c_spelling_proves_a_swift_name(self) -> None:
        """A Swift name synthesized by the importer is never text in the SDK.

        Searching for it alone reported `builtInOuterUltraWideCamera` as missing
        against a real iOS 27.1 SDK that declares it, which under the repo's own
        rules would report compiling code as blocked on a newer Xcode.
        """
        symbol = sdk_api_check.Symbol(
            "builtInOuterUltraWideCamera",
            "cameras",
            "iOS 27.1",
            also=("AVCaptureDeviceTypeBuiltInOuterUltraWideCamera",),
        )
        row = sdk_api_check.check(self.sdk, [symbol])["symbols"][0]
        self.assertTrue(row["found"], "the Objective-C constant proves the symbol exists")
        self.assertEqual(row["frameworks"], ["AVFoundation"])
        self.assertEqual(row["matched_as"], ["AVCaptureDeviceTypeBuiltInOuterUltraWideCamera"])
        self.assertIn("API_AVAILABLE(ios(27.1)", row["declaration"]["availability"])

    def test_headerdoc_block_is_not_read_as_a_declaration(self) -> None:
        """A `/*! @constant ... */` line has no leading `*` to give it away.

        Reading it as the declaration makes the extractor scrape availability
        from the lines above, which belong to the previous constant -- it
        reported this ios(27.1) API as ios(13.0).
        """
        symbol = sdk_api_check.Symbol(
            "builtInOuterUltraWideCamera",
            "cameras",
            "iOS 27.1",
            also=("AVCaptureDeviceTypeBuiltInOuterUltraWideCamera",),
        )
        row = sdk_api_check.check(self.sdk, [symbol])["symbols"][0]
        self.assertTrue(row["declaration"]["line"].startswith("AVF_EXPORT"))
        self.assertEqual(row["declaration"]["availability"], "API_AVAILABLE(ios(27.1)")

    def test_swift_name_alone_would_miss_it(self) -> None:
        """The guard for the above: without `also`, the symbol is not found."""
        symbol = sdk_api_check.Symbol("builtInOuterUltraWideCamera", "cameras", "iOS 27.1")
        row = sdk_api_check.check(self.sdk, [symbol])["symbols"][0]
        self.assertFalse(row["found"])

    def test_markdown_names_the_spelling_that_matched(self) -> None:
        buffer = io.StringIO()
        report = sdk_api_check.check(
            self.sdk,
            [
                sdk_api_check.Symbol(
                    "builtInOuterUltraWideCamera",
                    "cameras",
                    "iOS 27.1",
                    also=("AVCaptureDeviceTypeBuiltInOuterUltraWideCamera",),
                )
            ],
        )
        report.update(sdk_path="x", sdk_version="27.1", xcode_version="Xcode 27.1")
        buffer.write(sdk_api_check.render_markdown(report))
        self.assertIn("yes (as `AVCaptureDeviceTypeBuiltInOuterUltraWideCamera`)", buffer.getvalue())

    def test_camera_device_types_carry_their_objective_c_spelling(self) -> None:
        """Regression guard on the shipped list, not on a fixture."""
        by_name = {s.name: s for s in sdk_api_check.DEFAULT_SYMBOLS}
        for name in ("builtInOuterUltraWideCamera", "builtInInnerUltraWideCamera"):
            with self.subTest(name):
                self.assertTrue(by_name[name].also, "AVFoundation ships no Swift interface")

    def test_default_symbols_are_unique(self) -> None:
        names = [symbol.name for symbol in sdk_api_check.DEFAULT_SYMBOLS]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
