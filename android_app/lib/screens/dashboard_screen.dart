import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'settings_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic> _stats = {};
  bool _isLoading = true;
  final currencyFormat = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    setState(() => _isLoading = true);
    try {
      final s = await ApiService.fetchDashboardStats();
      if (mounted) {
        setState(() {
          _stats = s;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Widget _buildKpiCard(String title, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
              Icon(icon, size: 18, color: color),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final kpis = _stats['kpis'] ?? {};
    final salesReps = _stats['sales_reps'] as List? ?? [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Performance Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SettingsScreen()),
              );
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryCoral))
          : RefreshIndicator(
              onRefresh: _loadStats,
              color: AppTheme.primaryCoral,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Grid of 4 KPIs
                    GridView.count(
                      crossAxisCount: 2,
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      childAspectRatio: 1.6,
                      children: [
                        _buildKpiCard(
                          'Won Value (MTD)',
                          currencyFormat.format(kpis['won_amount'] ?? 0),
                          Icons.verified,
                          AppTheme.successGreen,
                        ),
                        _buildKpiCard(
                          'Open Pipeline',
                          currencyFormat.format(kpis['open_amount'] ?? 0),
                          Icons.timelapse,
                          Colors.blue,
                        ),
                        _buildKpiCard(
                          'Total Quotes',
                          '${kpis['total_count'] ?? 0}',
                          Icons.description_outlined,
                          AppTheme.navyDark,
                        ),
                        _buildKpiCard(
                          'Conversion Rate',
                          '${(kpis['conversion_rate'] ?? 0).toStringAsFixed(1)}%',
                          Icons.trending_up,
                          AppTheme.warningOrange,
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Sales Rep Targets Progress
                    const Text('Sales Team Target Progress', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    const SizedBox(height: 10),

                    ...salesReps.map((rep) {
                      final target = (rep['monthly_target'] as num?)?.toDouble() ?? 500000.0;
                      final achieved = (rep['achieved_won'] as num?)?.toDouble() ?? 0.0;
                      final pct = target > 0 ? (achieved / target).clamp(0.0, 1.0) : 0.0;

                      return Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppTheme.borderLight),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  rep['name'] ?? '',
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                ),
                                Text(
                                  '${(pct * 100).toStringAsFixed(1)}%',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: AppTheme.primaryCoral,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            LinearProgressIndicator(
                              value: pct,
                              backgroundColor: Colors.grey.shade200,
                              color: pct >= 1.0 ? AppTheme.successGreen : AppTheme.primaryCoral,
                              minHeight: 6,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            const SizedBox(height: 6),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  'Achieved: ${currencyFormat.format(achieved)}',
                                  style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                                ),
                                Text(
                                  'Target: ${currencyFormat.format(target)}',
                                  style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                                ),
                              ],
                            ),
                          ],
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ),
    );
  }
}
