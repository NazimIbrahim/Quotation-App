class QuotationSummary {
  final int id;
  final String quotationNumber;
  final String quotationDate;
  final int customerId;
  final String customerName;
  final String customerPhone;
  final String? deliveryAddress;
  final int salesPersonId;
  final String salesPersonName;
  final int? assistedById;
  final String? assistedByName;
  final String splitType;
  final String status;
  final String taxMode;
  final double taxableAmount;
  final double totalTax;
  final double grossTotal;
  final double netTotal;
  final double clearedPayments;
  final double outstandingBalance;
  final String paymentStatus;

  QuotationSummary({
    required this.id,
    required this.quotationNumber,
    required this.quotationDate,
    required this.customerId,
    required this.customerName,
    required this.customerPhone,
    this.deliveryAddress,
    required this.salesPersonId,
    required this.salesPersonName,
    this.assistedById,
    this.assistedByName,
    required this.splitType,
    required this.status,
    required this.taxMode,
    required this.taxableAmount,
    required this.totalTax,
    required this.grossTotal,
    required this.netTotal,
    required this.clearedPayments,
    required this.outstandingBalance,
    required this.paymentStatus,
  });

  factory QuotationSummary.fromJson(Map<String, dynamic> json) {
    return QuotationSummary(
      id: json['id'] ?? 0,
      quotationNumber: json['quotation_number'] ?? '',
      quotationDate: json['quotation_date'] ?? '',
      customerId: json['customer_id'] ?? 0,
      customerName: json['customer_name'] ?? '',
      customerPhone: json['customer_phone'] ?? '',
      deliveryAddress: json['delivery_address'],
      salesPersonId: json['sales_person_id'] ?? 0,
      salesPersonName: json['sales_person_name'] ?? '',
      assistedById: json['assisted_by_id'],
      assistedByName: json['assisted_by_name'],
      splitType: json['split_type'] ?? 'none',
      status: json['status'] ?? 'Open',
      taxMode: json['tax_mode'] ?? 'exclusive',
      taxableAmount: (json['taxable_amount'] as num?)?.toDouble() ?? 0.0,
      totalTax: (json['total_tax'] as num?)?.toDouble() ?? 0.0,
      grossTotal: (json['gross_total'] as num?)?.toDouble() ?? 0.0,
      netTotal: (json['net_total'] as num?)?.toDouble() ?? 0.0,
      clearedPayments: (json['cleared_payments'] as num?)?.toDouble() ?? 0.0,
      outstandingBalance: (json['outstanding_balance'] as num?)?.toDouble() ?? 0.0,
      paymentStatus: json['payment_status'] ?? 'Pending',
    );
  }
}

class QuotationItemInput {
  int? id;
  int slNo;
  String description;
  String size;
  String brand;
  String productType; // Box, Sqft, Pieces, Bags, Nos
  double coverageArea;
  double quantitySqft;
  double ratePerSqft;
  double quantityBoxes;
  double ratePerBox;
  String taxMode;
  double taxPercent;
  double taxableAmount;
  double gstAmount;
  double totalAmount;

  QuotationItemInput({
    this.id,
    this.slNo = 1,
    this.description = '',
    this.size = '',
    this.brand = '',
    this.productType = 'Box',
    this.coverageArea = 0.0,
    this.quantitySqft = 0.0,
    this.ratePerSqft = 0.0,
    this.quantityBoxes = 0.0,
    this.ratePerBox = 0.0,
    this.taxMode = 'exclusive',
    this.taxPercent = 18.0,
    this.taxableAmount = 0.0,
    this.gstAmount = 0.0,
    this.totalAmount = 0.0,
  });

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'sl_no': slNo,
      'description': description,
      'size': size,
      'brand': brand,
      'product_type': productType,
      'coverage_area': coverageArea,
      'quantity_sqft': quantitySqft,
      'rate_per_sqft': ratePerSqft,
      'quantity_boxes': quantityBoxes,
      'rate_per_box': ratePerBox,
      'tax_mode': taxMode,
      'tax_percent': taxPercent,
      'taxable_amount': taxableAmount,
      'gst_amount': gstAmount,
      'total_amount': totalAmount,
    };
  }

  factory QuotationItemInput.fromJson(Map<String, dynamic> json) {
    return QuotationItemInput(
      id: json['id'],
      slNo: json['sl_no'] ?? 1,
      description: json['description'] ?? '',
      size: json['size'] ?? '',
      brand: json['brand'] ?? '',
      productType: json['product_type'] ?? 'Box',
      coverageArea: (json['coverage_area'] as num?)?.toDouble() ?? 0.0,
      quantitySqft: (json['quantity_sqft'] as num?)?.toDouble() ?? 0.0,
      ratePerSqft: (json['rate_per_sqft'] as num?)?.toDouble() ?? 0.0,
      quantityBoxes: (json['quantity_boxes'] as num?)?.toDouble() ?? 0.0,
      ratePerBox: (json['rate_per_box'] as num?)?.toDouble() ?? 0.0,
      taxMode: json['tax_mode'] ?? 'exclusive',
      taxPercent: (json['tax_percent'] as num?)?.toDouble() ?? 18.0,
      taxableAmount: (json['taxable_amount'] as num?)?.toDouble() ?? 0.0,
      gstAmount: (json['gst_amount'] as num?)?.toDouble() ?? 0.0,
      totalAmount: (json['total_amount'] as num?)?.toDouble() ?? 0.0,
    );
  }
}
