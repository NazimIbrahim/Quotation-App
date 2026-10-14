class SalesPersonModel {
  final int id;
  final String name;
  final String contactNumber;
  final String? email;
  final String role;
  final double currentMonthlyTarget;
  final double wonAchievedThisMonth;
  final double pipelineTotal;

  SalesPersonModel({
    required this.id,
    required this.name,
    required this.contactNumber,
    this.email,
    required this.role,
    this.currentMonthlyTarget = 0.0,
    this.wonAchievedThisMonth = 0.0,
    this.pipelineTotal = 0.0,
  });

  factory SalesPersonModel.fromJson(Map<String, dynamic> json) {
    return SalesPersonModel(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      contactNumber: json['contact_number'] ?? '',
      email: json['email'],
      role: json['role'] ?? 'Sales Person',
      currentMonthlyTarget: (json['current_monthly_target'] as num?)?.toDouble() ?? 0.0,
      wonAchievedThisMonth: (json['won_achieved_this_month'] as num?)?.toDouble() ?? 0.0,
      pipelineTotal: (json['pipeline_total'] as num?)?.toDouble() ?? 0.0,
    );
  }
}
