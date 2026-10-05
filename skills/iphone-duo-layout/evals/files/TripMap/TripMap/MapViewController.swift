import MapKit
import UIKit

/// A full-screen map. Tapping a pin opens a sheet with the place's details.
/// Design: centred when the iPhone Duo lies flat, on the trailing side when folded like a book.
final class MapViewController: UIViewController {
    private let mapView = MKMapView()
    private var detailsSheet: PlaceDetailsViewController?

    override func viewDidLoad() {
        super.viewDidLoad()
        mapView.frame = view.bounds
        mapView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(mapView)

        // Sheets got stuck on the crease, so take the sheet down and put it back up
        // whenever the hinge moves.
        view.addInteraction(UIHingeInteraction { [weak self] _, update in
            guard let self, let sheet = self.detailsSheet, update.hinge?.status == .partiallyOpen else { return }
            sheet.dismiss(animated: false) {
                self.present(sheet, animated: true)
            }
        })
    }

    func showDetails(for place: Place) {
        let details = PlaceDetailsViewController(place: place)
        details.modalPresentationStyle = .pageSheet
        if let sheet = details.sheetPresentationController {
            sheet.detents = [.medium(), .large()]
            sheet.preferredPlacement = .trailing
        }
        detailsSheet = details
        present(details, animated: true)
    }
}

struct Place {
    let name: String
}

final class PlaceDetailsViewController: UIViewController {
    let place: Place

    init(place: Place) {
        self.place = place
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is not supported") }
}
