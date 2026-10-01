// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "FoldKit",
    platforms: [.iOS(.v26), .macOS(.v26)],
    products: [.library(name: "FoldKit", targets: ["FoldKit"])],
    targets: [
        .target(name: "FoldKit"),
        .testTarget(name: "FoldKitTests", dependencies: ["FoldKit"]),
    ]
)
