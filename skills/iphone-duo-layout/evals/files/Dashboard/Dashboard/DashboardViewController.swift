import UIKit

/// Section 0: two summary cards side by side ("This week", "This month").
/// Section 1: a photo grid that scrolls vertically.
final class DashboardViewController: UICollectionViewController {
    init() {
        super.init(collectionViewLayout: DashboardViewController.makeLayout())
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }

    static func makeLayout() -> UICollectionViewCompositionalLayout {
        UICollectionViewCompositionalLayout { section, environment in
            section == 0 ? summarySection(environment) : photoSection(environment)
        }
    }

    /// In book pose the hinge shows up in the container's insets, so splitting the
    /// remaining width in two keeps the gap between the cards on the crease.
    private static func summarySection(_ environment: NSCollectionLayoutEnvironment) -> NSCollectionLayoutSection {
        // On the compact outer display there is no room for the cards: hide them.
        let compact = environment.traitCollection.horizontalSizeClass == .compact
        let height: NSCollectionLayoutDimension = compact ? .absolute(0.1) : .absolute(120)
        let insets = environment.container.effectiveContentInsets
        let card = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .fractionalWidth(0.5),
                                                            heightDimension: height))
        let group = NSCollectionLayoutGroup.horizontal(
            layoutSize: .init(widthDimension: .fractionalWidth(1), heightDimension: height),
            repeatingSubitem: card, count: 2)
        group.interItemSpacing = .fixed(max(insets.leading, 16))
        return NSCollectionLayoutSection(group: group)
    }

    /// Every row keeps the middle gutter on the crease too.
    private static func photoSection(_ environment: NSCollectionLayoutEnvironment) -> NSCollectionLayoutSection {
        let tile = NSCollectionLayoutItem(layoutSize: .init(widthDimension: .fractionalWidth(0.25),
                                                            heightDimension: .fractionalWidth(0.25)))
        tile.contentInsets = .init(top: 2, leading: 2, bottom: 2, trailing: 2)
        let row = NSCollectionLayoutGroup.horizontal(
            layoutSize: .init(widthDimension: .fractionalWidth(1), heightDimension: .fractionalWidth(0.25)),
            repeatingSubitem: tile, count: 4)
        let section = NSCollectionLayoutSection(group: row)
        section.contentInsetsReference = .safeArea
        return section
    }
}
