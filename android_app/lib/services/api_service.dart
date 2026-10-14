import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/quotation.dart';
import '../models/customer.dart';
import '../models/brand.dart';
import '../models/salesperson.dart';

class ApiService {
  static Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

  static Future<bool> checkHealth() async {
    try {
      final res = await http.get(Uri.parse(ApiConfig.healthUrl)).timeout(
            const Duration(seconds: 4),
          );
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<List<QuotationSummary>> fetchQuotations({
    String? status,
    int? salesPersonId,
    String? search,
  }) async {
    final queryParams = <String, String>{};
    if (status != null && status != 'All') queryParams['status'] = status;
    if (salesPersonId != null) queryParams['sales_person_id'] = salesPersonId.toString();
    if (search != null && search.isNotEmpty) queryParams['search'] = search;

    final uri = Uri.parse(ApiConfig.quotationsUrl).replace(queryParameters: queryParams);
    final res = await http.get(uri, headers: _headers);

    if (res.statusCode == 200) {
      final data = json.decode(res.body);
      final list = data['quotations'] as List? ?? [];
      return list.map((q) => QuotationSummary.fromJson(q)).toList();
    } else {
      throw Exception('Failed to load quotations: ${res.statusCode}');
    }
  }

  static Future<Map<String, dynamic>> fetchQuotationDetails(int id) async {
    final res = await http.get(Uri.parse("${ApiConfig.quotationsUrl}/$id"), headers: _headers);
    if (res.statusCode == 200) {
      return json.decode(res.body);
    } else {
      throw Exception('Failed to load quotation details');
    }
  }

  static Future<Map<String, dynamic>> saveQuotation(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse(ApiConfig.quotationsUrl),
      headers: _headers,
      body: json.encode(payload),
    );
    if (res.statusCode == 200) {
      return json.decode(res.body);
    } else {
      final body = json.decode(res.body);
      throw Exception(body['detail'] ?? 'Failed to save quotation');
    }
  }

  static Future<bool> updateQuotationStatus(int id, String status, {String? note}) async {
    final uri = Uri.parse("${ApiConfig.quotationsUrl}/$id/status").replace(
      queryParameters: {
        'status': status,
        if (note != null) 'note': note,
      },
    );
    final res = await http.put(uri, headers: _headers);
    return res.statusCode == 200;
  }

  static Future<List<CustomerModel>> fetchCustomers({String? search}) async {
    final uri = Uri.parse(ApiConfig.customersUrl).replace(
      queryParameters: search != null && search.isNotEmpty ? {'search': search} : null,
    );
    final res = await http.get(uri, headers: _headers);
    if (res.statusCode == 200) {
      final data = json.decode(res.body);
      final list = data['customers'] as List? ?? [];
      return list.map((c) => CustomerModel.fromJson(c)).toList();
    }
    return [];
  }

  static Future<CustomerModel> createCustomer(Map<String, dynamic> payload) async {
    final res = await http.post(
      Uri.parse(ApiConfig.customersUrl),
      headers: _headers,
      body: json.encode(payload),
    );
    if (res.statusCode == 200) {
      return CustomerModel.fromJson(json.decode(res.body));
    } else {
      throw Exception('Failed to save customer');
    }
  }

  static Future<List<BrandModel>> fetchBrands() async {
    final res = await http.get(Uri.parse(ApiConfig.brandsUrl), headers: _headers);
    if (res.statusCode == 200) {
      final data = json.decode(res.body);
      final list = data['brands'] as List? ?? [];
      return list.map((b) => BrandModel.fromJson(b)).toList();
    }
    return [];
  }

  static Future<List<SalesPersonModel>> fetchSalespersons() async {
    final res = await http.get(Uri.parse(ApiConfig.salespersonsUrl), headers: _headers);
    if (res.statusCode == 200) {
      final data = json.decode(res.body);
      final list = data['salespersons'] as List? ?? [];
      return list.map((s) => SalesPersonModel.fromJson(s)).toList();
    }
    return [];
  }

  static Future<Map<String, dynamic>> fetchDashboardStats() async {
    final res = await http.get(Uri.parse(ApiConfig.reportsDashboardUrl), headers: _headers);
    if (res.statusCode == 200) {
      return json.decode(res.body);
    }
    return {};
  }
}
