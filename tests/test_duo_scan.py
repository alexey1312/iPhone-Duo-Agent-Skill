from __future__ import annotations

import importlib.util
import io
import json
import plistlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "duo_scan.py"
SPEC = importlib.util.spec_from_file_location("duo_scan", SCRIPT)
assert SPEC and SPEC.loader
duo_scan = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = duo_scan
SPEC.loader.exec_module(duo_scan)


class ProjectFixture:
    def __init__(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.root = Path(self._directory.name)

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def write_plist(self, relative: str, value: dict) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as stream:
            plistlib.dump(value, stream)

    def scan(self, **kwargs) -> dict:
        return duo_scan.scan(self.root, **kwargs)

    def rules(self, **kwargs) -> list[str]:
        return [finding["rule"] for finding in self.scan(**kwargs)["findings"]]

    def close(self) -> None:
        self._directory.cleanup()


class ScanTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.project = ProjectFixture()

    def tearDown(self) -> None:
        self.project.close()

    def assertRules(self, source: str, expected: list[str], name: str = "Sources/View.swift") -> None:
        self.project.write(name, source)
        self.assertEqual(sorted(self.project.rules()), sorted(expected))


class SourceRuleTests(ScanTestCase):
    def test_main_screen_swift_and_objc(self) -> None:
        self.assertRules("let s = UIScreen.main.scale\n", ["DUO001"])
        self.project.close()
        self.project = ProjectFixture()
        self.assertRules("CGFloat s = [UIScreen mainScreen].scale;\n", ["DUO001"], name="Sources/View.m")

    def test_screen_bounds_supersedes_main_screen(self) -> None:
        self.assertRules("let w = UIScreen.main.bounds.width\n", ["DUO002"])

    def test_objc_screen_bounds_message_send(self) -> None:
        self.assertRules("CGRect r = [[UIScreen mainScreen] bounds];\n", ["DUO002"], name="Sources/View.m")

    def test_window_scene_screen_bounds(self) -> None:
        self.assertRules("let w = view.window?.windowScene?.screen.bounds.width\n", ["DUO002"])

    def test_trait_display_scale_is_clean(self) -> None:
        self.assertRules("let s = traitCollection.displayScale\nlet w = view.bounds.width\n", [])

    def test_idiom(self) -> None:
        self.assertRules("if traitCollection.userInterfaceIdiom == .pad {}\n", ["DUO003"])

    def test_orientation_variants(self) -> None:
        source = "\n".join(
            [
                "if UIDevice.current.orientation.isLandscape {}",
                "let o = windowScene.interfaceOrientation",
                "if UIInterfaceOrientationIsPortrait(o) {}",
            ]
        )
        self.assertRules(source + "\n", ["DUO004", "DUO004", "DUO004"])

    def test_supported_orientations_override_is_not_a_layout_read(self) -> None:
        self.assertRules(
            "override var supportedInterfaceOrientations: UIInterfaceOrientationMask { .all }\n", []
        )

    def test_symmetric_safe_area(self) -> None:
        self.assertRules("let w = view.bounds.width - view.safeAreaInsets.left * 2\n", ["DUO006"])
        self.project.close()
        self.project = ProjectFixture()
        self.assertRules("let w = bounds.width - 2 * safeAreaInsets.left\n", ["DUO006"])

    def test_symmetric_inset_through_a_local(self) -> None:
        source = "let inset = view.safeAreaInsets.left\nlet width = view.bounds.width - inset * 2\n"
        self.assertRules(source, ["DUO006"])
        self.project.close()
        self.project = ProjectFixture()
        self.assertRules("let w = bounds.width - 2 * horizontalInset\n", ["DUO006"])

    def test_symmetric_padding_is_not_an_inset(self) -> None:
        self.assertRules("let w = bounds.width - padding * 2\n", [])

    def test_member_chain_across_lines(self) -> None:
        source = "\n".join(
            [
                "let scene = UIApplication.shared.connectedScenes",
                "    .compactMap { $0 as? UIWindowScene }",
                "    .first?",
                "    .interfaceOrientation",
            ]
        )
        self.project.write("Sources/View.swift", source + "\n")
        findings = self.project.scan()["findings"]
        self.assertEqual(sorted(f["rule"] for f in findings), ["DUO004", "DUO009"])
        self.assertEqual({f["line"] for f in findings}, {1})

    def test_inset_by_is_clean(self) -> None:
        self.assertRules("let w = view.bounds.inset(by: view.safeAreaInsets).width\n", [])

    def test_standalone_bars(self) -> None:
        self.assertRules("let toolbar = UIToolbar()\n", ["DUO007"])
        self.project.close()
        self.project = ProjectFixture()
        self.assertRules("UINavigationBar *bar = [[UINavigationBar alloc] init];\n", ["DUO007"], name="Sources/Bar.m")

    def test_bar_appearance_proxy_is_clean(self) -> None:
        self.assertRules("UINavigationBar.appearance().tintColor = .red\n", [])

    def test_navigation_view(self) -> None:
        self.assertRules("var body: some View { NavigationView { Text(\"a\") } }\n", ["DUO008"])

    def test_global_window_state(self) -> None:
        source = "\n".join(
            [
                "let w = UIApplication.shared.keyWindow",
                "let s = UIApplication.shared.connectedScenes.first",
                "let f = UIApplication.shared.statusBarFrame",
            ]
        )
        self.assertRules(source + "\n", ["DUO009", "DUO009", "DUO009"])

    def test_scene_activation_without_error_handler(self) -> None:
        self.assertRules(
            "UIApplication.shared.requestSceneSessionActivation(nil, userActivity: a, options: nil, errorHandler: nil)\n",
            ["DUO010"],
        )

    def test_scene_activation_with_error_handler_is_clean(self) -> None:
        self.assertRules(
            "UIApplication.shared.activateSceneSession(for: request) { error in log(error) }\n", []
        )

    def test_custom_ellipsis(self) -> None:
        self.assertRules('Image(systemName: "ellipsis.circle")\n', ["DUO011"])

    def test_face_id_copy(self) -> None:
        for name, source in [
            ("Sources/A.swift", 'Text("Unlock with Face ID")\n'),
            ("Sources/B.m", 'label.text = @"Use FaceID to continue";\n'),
            ("Sources/C.swift", 'Image(systemName: "faceid")\n'),
            ("Sources/D.swift", 'let t = "unlock with face id"\n'),
            ("Sources/E.swift", 'let t = "Set up Face-ID"\n'),
            ("Sources/F.swift", 'let intro = """\n    Set up Face ID to unlock faster.\n    """\n'),
        ]:
            with self.subTest(name=name):
                self.project.close()
                self.project = ProjectFixture()
                self.assertRules(source, ["DUO013"], name=name)

    def test_face_id_enum_cases_and_identifiers_are_clean(self) -> None:
        self.assertRules("case .faceID:\n    icon = faceIDImage\nlet faceID = LAContext()\n", [])

    def test_face_id_read_on_the_same_line_is_clean(self) -> None:
        self.assertRules('let name = context.biometryType == .faceID ? "Face ID" : "Touch ID"\n', [])

    def test_face_id_copy_next_to_a_biometry_read_is_low(self) -> None:
        source = "\n".join(
            [
                "switch context.biometryType {",
                "case .faceID:",
                '    title = "Face ID"',
                "case .touchID:",
                '    title = "Touch ID"',
                "}",
                'reason = "Face ID is required to open your vault"',
            ]
        )
        self.project.write("Sources/View.swift", source + "\n")
        findings = self.project.scan()["findings"]
        self.assertEqual([(f["rule"], f["line"], f["severity"]) for f in findings], [("DUO013", 3, "low"), ("DUO013", 7, "low")])

    def test_face_id_downgrade_is_per_file(self) -> None:
        self.project.write("Sources/Unlock.swift", 'let kind = LAContext().biometryType\nlet hint = "Look at the camera for Face ID"\n')
        self.project.write("Sources/Strings.swift", 'static let unlock = "Unlock with Face ID"\n')
        findings = self.project.scan()["findings"]
        self.assertEqual(
            [(f["file"], f["severity"]) for f in findings],
            [("Sources/Strings.swift", "medium"), ("Sources/Unlock.swift", "low")],
        )

    def test_face_id_app_enum_does_not_count_as_handled(self) -> None:
        source = "enum AuthMethod { case faceID, touchID }\nlet method: AuthMethod = .faceID\nlet title = \"Unlock with Face ID\"\n"
        self.project.write("Sources/View.swift", source)
        findings = self.project.scan()["findings"]
        self.assertEqual([(f["rule"], f["severity"]) for f in findings], [("DUO013", "medium")])


class CommentAndStringTests(ScanTestCase):
    def test_line_and_block_comments_are_ignored(self) -> None:
        source = "\n".join(
            [
                "// UIScreen.main.scale",
                "/* UIDevice.current.orientation",
                "   /* nested UIScreen.main */",
                "   still comment UIScreen.main */",
                "let url = \"https://example.com\" // UIScreen.main",
            ]
        )
        self.assertRules(source + "\n", [])

    def test_code_after_a_url_string_is_still_scanned(self) -> None:
        self.assertRules('let u = "https://example.com"; let s = UIScreen.main.scale\n', ["DUO001"])

    def test_line_numbers_survive_block_comments(self) -> None:
        self.project.write("Sources/View.swift", "/*\n\n*/\nlet s = UIScreen.main.scale\n")
        finding = self.project.scan()["findings"][0]
        self.assertEqual(finding["line"], 4)
        self.assertEqual(finding["snippet"], "let s = UIScreen.main.scale")
        self.assertEqual(finding["id"], "DUO001:Sources/View.swift:4")


class ProjectRuleTests(ScanTestCase):
    def test_app_delegate_only_is_critical(self) -> None:
        self.project.write(
            "App/AppDelegate.swift",
            "@main\nclass AppDelegate: UIResponder, UIApplicationDelegate {\n    var window: UIWindow?\n}\n",
        )
        report = self.project.scan()
        self.assertEqual(report["project"]["lifecycle"], "app-delegate-only")
        critical = [f for f in report["findings"] if f["rule"] == "DUO005"]
        self.assertEqual(len(critical), 1)
        self.assertEqual(critical[0]["severity"], "critical")

    def test_swiftui_app_has_scene_lifecycle(self) -> None:
        self.project.write("App/MyApp.swift", "import SwiftUI\n@main\nstruct MyApp: App {\n}\n")
        self.project.write("App/Delegate.swift", "final class D: NSObject, UIApplicationDelegate {}\n")
        report = self.project.scan()
        self.assertEqual(report["project"]["lifecycle"], "swiftui-app")
        self.assertNotIn("DUO005", [f["rule"] for f in report["findings"]])

    def test_scene_delegate_with_manifest(self) -> None:
        self.project.write("App/AppDelegate.swift", "class AppDelegate: UIResponder, UIApplicationDelegate {}\n")
        self.project.write("App/SceneDelegate.swift", "class SceneDelegate: UIResponder, UIWindowSceneDelegate {}\n")
        self.project.write_plist(
            "App/Info.plist",
            {"UIApplicationSceneManifest": {"UIApplicationSupportsMultipleScenes": True}},
        )
        report = self.project.scan()
        self.assertEqual(report["project"]["lifecycle"], "scene")
        self.assertTrue(report["project"]["scene_manifest_found"])
        self.assertTrue(report["project"]["supports_multiple_scenes"])
        self.assertEqual(report["findings"], [])

    def test_scene_delegate_without_manifest_is_low(self) -> None:
        self.project.write("App/SceneDelegate.swift", "class SceneDelegate: UIResponder, UIWindowSceneDelegate {}\n")
        self.assertEqual(self.project.rules(), ["DUO012"])

    def test_generated_manifest_setting_counts(self) -> None:
        self.project.write("App/SceneDelegate.swift", "class SceneDelegate: UIResponder, UIWindowSceneDelegate {}\n")
        self.project.write(
            "App.xcodeproj/project.pbxproj",
            "INFOPLIST_KEY_UIApplicationSceneManifest_Generation = YES;\n",
        )
        self.assertEqual(self.project.rules(), [])

    def test_plist_full_screen_and_portrait_only(self) -> None:
        self.project.write_plist(
            "App/Info.plist",
            {
                "UIRequiresFullScreen": True,
                "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait"],
            },
        )
        self.assertEqual(sorted(self.project.rules()), ["DUO020", "DUO021"])

    def test_plist_with_landscape_is_not_portrait_only(self) -> None:
        self.project.write_plist(
            "App/Info.plist",
            {
                "UISupportedInterfaceOrientations": [
                    "UIInterfaceOrientationPortrait",
                    "UIInterfaceOrientationLandscapeLeft",
                ]
            },
        )
        self.assertEqual(self.project.rules(), [])

    def test_build_setting_portrait_only(self) -> None:
        self.project.write(
            "App.xcodeproj/project.pbxproj",
            'INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone = "UIInterfaceOrientationPortrait";\n'
            "INFOPLIST_KEY_UIRequiresFullScreen = YES;\n",
        )
        self.assertEqual(sorted(self.project.rules()), ["DUO020", "DUO021"])


class TraversalTests(ScanTestCase):
    def test_dependencies_and_hidden_directories_are_skipped(self) -> None:
        self.project.write("Pods/Lib/Screen.swift", "let s = UIScreen.main.scale\n")
        self.project.write(".build/checkouts/Lib/Screen.swift", "let s = UIScreen.main.scale\n")
        self.project.write(".claude/worktrees/copy/Screen.swift", "let s = UIScreen.main.scale\n")
        self.project.write("DerivedData/Screen.swift", "let s = UIScreen.main.scale\n")
        self.assertEqual(self.project.rules(), [])
        self.assertEqual(self.project.rules(include_dependencies=True), ["DUO001"])

    def test_inventory_counts_capabilities(self) -> None:
        self.project.write("Sources/Unlock.swift", "import LocalAuthentication\nlet kind = LAContext().biometryType\n")
        self.project.write("Sources/Widget.swift", "import WidgetKit\n")
        self.project.write(
            "Sources/Camera.swift",
            "let coordinator = AVCaptureDeviceDirectionCoordinator(view: view, deviceTypes: []) { _ in }\n"
            "connection.isVideoMirrored = true\n",
        )
        inventory = self.project.scan()["inventory"]
        self.assertEqual(inventory["biometryType reads"], 1)
        self.assertEqual(inventory["WidgetKit"], 1)
        self.assertEqual(inventory["direction coordinator"], 1)
        self.assertEqual(inventory["video mirroring"], 1)
        self.assertNotIn("Live Activities", inventory)

    def test_inventory_counts_containers(self) -> None:
        self.project.write(
            "Sources/Root.swift",
            "NavigationStack { List {} .toolbar { ToolbarItem(placement: .primaryAction) {} } }\n",
        )
        inventory = self.project.scan()["inventory"]
        self.assertEqual(inventory["NavigationStack"], 1)
        self.assertEqual(inventory["toolbar modifier"], 1)
        self.assertEqual(inventory["ToolbarItem"], 1)
        self.assertNotIn("TabView", inventory)


class CommandLineTests(ScanTestCase):
    def run_main(self, *args: str) -> tuple[int, str]:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            status = duo_scan.main([str(self.project.root), *args])
        return status, buffer.getvalue()

    def test_json_output_shape(self) -> None:
        self.project.write("Sources/View.swift", "let s = UIScreen.main.scale\n")
        status, output = self.run_main("--format", "json")
        report = json.loads(output)
        self.assertEqual(status, 0)
        self.assertTrue(report["read_only"])
        self.assertEqual(report["summary"]["by_severity"]["high"], 1)
        finding = report["findings"][0]
        for key in ("id", "rule", "title", "severity", "skill", "file", "line", "snippet", "source", "advice"):
            self.assertIn(key, finding)
        self.assertIn("111461", finding["source"])

    def test_fail_on_threshold(self) -> None:
        self.project.write("Sources/View.swift", "let s = UIScreen.main.scale\n")
        self.assertEqual(self.run_main("--fail-on", "high")[0], 2)
        self.assertEqual(self.run_main("--fail-on", "critical")[0], 0)

    def test_markdown_output(self) -> None:
        self.project.write("Sources/View.swift", "let s = UIScreen.main.scale\n")
        status, output = self.run_main("--format", "markdown")
        self.assertEqual(status, 0)
        self.assertIn("# iPhone Duo readiness scan", output)
        self.assertIn("DUO001", output)

    def test_scan_does_not_modify_files(self) -> None:
        path = self.project.write("Sources/View.swift", "let s = UIScreen.main.scale\n")
        before = path.read_bytes()
        self.run_main("--format", "json")
        self.assertEqual(path.read_bytes(), before)


class RuleMetadataTests(unittest.TestCase):
    def test_every_rule_cites_a_session_and_names_a_skill(self) -> None:
        skills = {
            "iphone-duo-adaptivity-audit",
            "iphone-duo-bars",
            "iphone-duo-layout",
            "iphone-duo-displays",
        }
        rules = list(duo_scan.RULES) + list(duo_scan.PROJECT_RULES.values())
        self.assertEqual(len({rule.id for rule in rules}), len(rules))
        for rule in rules:
            self.assertIn(rule.skill, skills, rule.id)
            self.assertRegex(rule.source, r"(Tech Talk 1114\d\d|WWDC26 278) .+ \d+:\d\d", rule.id)
            self.assertIn(rule.severity, duo_scan.SEVERITIES, rule.id)


if __name__ == "__main__":
    unittest.main()
