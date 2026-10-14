import 'package:flutter/material.dart';
import 'config/api_config.dart';
import 'theme/app_theme.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiConfig.init();
  runApp(const AmaQuotationApp());
}

class AmaQuotationApp extends StatelessWidget {
  const AmaQuotationApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AMA Ceramics Quotation',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const HomeScreen(),
    );
  }
}
