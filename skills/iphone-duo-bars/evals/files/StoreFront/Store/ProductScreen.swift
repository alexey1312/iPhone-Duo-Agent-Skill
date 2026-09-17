import SwiftUI

struct Product {
    let name: String
    let details: String
    let heroImage: String
}

struct ProductScreen: View {
    let product: Product
    @State private var showsSizeGuide = false
    @State private var isSaved = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Image(product.heroImage)
                        .resizable()
                        .scaledToFill()
                        .frame(maxWidth: .infinity)
                        .frame(height: 320)
                        .clipped()
                    Text(product.name)
                        .font(.title)
                    Text(product.details)
                }
                .padding(.horizontal)
            }
            .navigationTitle(product.name)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Size Guide") { showsSizeGuide = true }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button(isSaved ? "Saved" : "Save") { isSaved.toggle() }
                }
                ToolbarItem(placement: .bottomBar) {
                    Button("Add to Bag", systemImage: "bag") {}
                }
            }
            .sheet(isPresented: $showsSizeGuide) {
                NavigationStack {
                    SizeGuideView()
                        .navigationTitle("Size Guide")
                        .toolbar {
                            ToolbarItem(placement: .topBarTrailing) {
                                Button("Close") { showsSizeGuide = false }
                            }
                        }
                }
            }
        }
    }
}

struct SizeGuideView: View {
    var body: some View {
        List(["XS", "S", "M", "L", "XL"], id: \.self) { size in
            LabeledContent(size, value: "Chest 86–94 cm")
        }
    }
}
