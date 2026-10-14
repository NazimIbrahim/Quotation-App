class CustomerModel {
  final int id;
  final String name;
  final String phone;
  final String? email;
  final String? billingAddress;
  final String? deliveryAddress;
  final String? gstin;
  final int totalQuotations;
  final double totalWonValue;

  CustomerModel({
    required this.id,
    required this.name,
    required this.phone,
    this.email,
    this.billingAddress,
    this.deliveryAddress,
    this.gstin,
    this.totalQuotations = 0,
    this.totalWonValue = 0.0,
  });

  factory CustomerModel.fromJson(Map<String, dynamic> json) {
    return CustomerModel(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      phone: json['phone'] ?? '',
      email: json['email'],
      billingAddress: json['billing_address'],
      deliveryAddress: json['delivery_address'],
      gstin: json['gstin'],
      totalQuotations: json['total_quotations'] ?? 0,
      totalWonValue: (json['total_won_value'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != 0) 'id': id,
      'name': name,
      'phone': phone,
      'email': email,
      'billing_address': billingAddress,
      'delivery_address': deliveryAddress,
      'gstin': gstin,
    };
  }
}
