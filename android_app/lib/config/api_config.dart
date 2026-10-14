import 'package:shared_preferences/shared_preferences.dart';

class ApiConfig {
  static const String prefKeyBaseUrl = "ama_server_url";
  // Default URL: fallback for local testing or change to your deployed cloud URL
  static const String defaultBaseUrl = "http://10.0.2.2:8000";

  static String _baseUrl = defaultBaseUrl;

  static String get baseUrl => _baseUrl;

  static Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(prefKeyBaseUrl) ?? defaultBaseUrl;
  }

  static Future<void> setBaseUrl(String url) async {
    String cleanUrl = url.trim();
    if (cleanUrl.endsWith("/")) {
      cleanUrl = cleanUrl.substring(0, cleanUrl.length - 1);
    }
    _baseUrl = cleanUrl;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(prefKeyBaseUrl, cleanUrl);
  }

  // Endpoints
  static String get quotationsUrl => "$_baseUrl/api/quotations";
  static String get customersUrl => "$_baseUrl/api/customers";
  static String get brandsUrl => "$_baseUrl/api/brands";
  static String get salespersonsUrl => "$_baseUrl/api/salespersons";
  static String get paymentsUrl => "$_baseUrl/api/payments";
  static String get reportsDashboardUrl => "$_baseUrl/api/reports/dashboard";
  static String get healthUrl => "$_baseUrl/api/health";

  static String quotationPdfUrl(int id, {bool encrypted = false}) {
    return "$quotationsUrl/$id/pdf?encrypted=$encrypted";
  }
}
