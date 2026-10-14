class PackagingSizeModel {
  final int id;
  final String sizeLabel;
  final String productType; // Box, Sqft, Pieces, Bags, Nos
  final double sqftPerBox;
  final int piecesPerBox;
  final double defaultRatePerBox;

  PackagingSizeModel({
    required this.id,
    required this.sizeLabel,
    required this.productType,
    required this.sqftPerBox,
    required this.piecesPerBox,
    required this.defaultRatePerBox,
  });

  factory PackagingSizeModel.fromJson(Map<String, dynamic> json) {
    return PackagingSizeModel(
      id: json['id'] ?? 0,
      sizeLabel: json['size_label'] ?? '',
      productType: json['product_type'] ?? 'Box',
      sqftPerBox: (json['sqft_per_box'] as num?)?.toDouble() ?? 0.0,
      piecesPerBox: json['pieces_per_box'] ?? 1,
      defaultRatePerBox: (json['default_rate_per_box'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class BrandModel {
  final int id;
  final String name;
  final String? code;
  final List<PackagingSizeModel> sizes;

  BrandModel({
    required this.id,
    required this.name,
    this.code,
    required this.sizes,
  });

  factory BrandModel.fromJson(Map<String, dynamic> json) {
    var rawSizes = json['sizes'] as List? ?? [];
    List<PackagingSizeModel> parsedSizes =
        rawSizes.map((s) => PackagingSizeModel.fromJson(s)).toList();

    return BrandModel(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      code: json['code'],
      sizes: parsedSizes,
    );
  }
}
