import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:share_plus/share_plus.dart';
import '../config/api_config.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class QuotationDetailScreen extends StatefulWidget {
  final int quotationId;

  const QuotationDetailScreen({super.key, required this.quotationId});

  @override
  State<QuotationDetailScreen> createState() => _QuotationDetailScreenState();
}

class _QuotationDetailScreenState extends State<QuotationDetailScreen> {
  Map<String, dynamic>? _data;
  bool _isLoading = true;
  final currencyFormat = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _loadDetails();
  }

  Future<void> _loadDetails() async {
    setState(() => _isLoading = true);
    try {
      final details = await ApiService.fetchQuotationDetails(widget.quotationId);
      if (mounted) {
        setState(() {
          _data = details;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading quotation: $e')),
        );
      }
    }
  }

  Future<void> _changeStatus(String newStatus) async {
    try {
      final success = await ApiService.updateQuotationStatus(widget.quotationId, newStatus);
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Status updated to $newStatus')),
        );
        _loadDetails();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to update status: $e')),
      );
    }
  }

  void _shareViaWhatsApp() async {
    if (_data == null) return;
    final quote = _data!['quotation'];
    final pdfUrl = ApiConfig.quotationPdfUrl(widget.quotationId, encrypted: false);
    final msg = "Hello ${quote['customer_name']},\n\nHere is your quotation ${quote['quotation_number']} for ${currencyFormat.format(quote['net_total'])} from AMA Ceramics.\n\nView PDF: $pdfUrl\n\nThank you for choosing AMA Ceramics!";
    
    final phone = (quote['customer_phone'] ?? '').toString().replaceAll(RegExp(r'[^0-9]'), '');
    final cleanPhone = phone.startsWith('91') ? phone : '91$phone';
    final waUrl = Uri.parse("https://api.whatsapp.com/send?phone=$cleanPhone&text=${Uri.encodeComponent(msg)}");
    
    if (await canLaunchUrl(waUrl)) {
      await launchUrl(waUrl, mode: LaunchMode.externalApplication);
    } else {
      Share.share(msg, subject: "AMA Ceramics Quotation ${quote['quotation_number']}");
    }
  }

  void _openPdf({bool encrypted = false}) async {
    final url = Uri.parse(ApiConfig.quotationPdfUrl(widget.quotationId, encrypted: encrypted));
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open PDF')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Quotation Details')),
        body: const Center(child: CircularProgressIndicator(color: AppTheme.primaryCoral)),
      );
    }

    if (_data == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Quotation Details')),
        body: const Center(child: Text('Quotation not found')),
      );
    }

    final quote = _data!['quotation'];
    final areas = _data!['areas'] as List? ?? [];

    return Scaffold(
      appBar: AppBar(
        title: Text(quote['quotation_number'] ?? 'Quote Details'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert),
            onSelected: (val) {
              if (val == 'pdf_std') _openPdf(encrypted: false);
              if (val == 'pdf_enc') _openPdf(encrypted: true);
              if (val == 'wa_share') _shareViaWhatsApp();
            },
            itemBuilder: (_) => [
              const PopupMenuItem(
                value: 'pdf_std',
                child: Row(
                  children: [
                    Icon(Icons.picture_as_pdf, color: Colors.blue, size: 20),
                    SizedBox(width: 10),
                    Text('View Standard PDF'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'pdf_enc',
                child: Row(
                  children: [
                    Icon(Icons.lock, color: AppTheme.warningOrange, size: 20),
                    SizedBox(width: 10),
                    Text('Export Encrypted PDF (-AMA)'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'wa_share',
                child: Row(
                  children: [
                    Icon(Icons.send, color: AppTheme.successGreen, size: 20),
                    SizedBox(width: 10),
                    Text('Share on WhatsApp'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status & Action Bar
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.borderLight),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Total Quotation Value', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                          const SizedBox(height: 2),
                          Text(
                            currencyFormat.format(quote['net_total']),
                            style: const TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.primaryCoral,
                            ),
                          ),
                        ],
                      ),
                      DropdownButton<String>(
                        value: quote['status'],
                        underline: const SizedBox(),
                        items: ['Won', 'Open', 'In-Review', 'Lost'].map((s) {
                          return DropdownMenuItem(
                            value: s,
                            child: Text(s, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          );
                        }).toList(),
                        onChanged: (newStatus) {
                          if (newStatus != null && newStatus != quote['status']) {
                            _changeStatus(newStatus);
                          }
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          icon: const Icon(Icons.picture_as_pdf, size: 16),
                          label: const Text('PDF', style: TextStyle(fontSize: 12)),
                          onPressed: () => _openPdf(encrypted: false),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutlinedButton.icon(
                          icon: const Icon(Icons.lock, size: 16, color: AppTheme.warningOrange),
                          label: const Text('Encrypted', style: TextStyle(fontSize: 12)),
                          onPressed: () => _openPdf(encrypted: true),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: ElevatedButton.icon(
                          icon: const Icon(Icons.send, size: 16),
                          label: const Text('WhatsApp', style: TextStyle(fontSize: 12)),
                          style: ElevatedButton.styleFrom(backgroundColor: AppTheme.successGreen),
                          onPressed: _shareViaWhatsApp,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Customer Info Card
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.borderLight),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Customer & Sales Details', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  const SizedBox(height: 8),
                  Text('Customer: ${quote['customer_name']}', style: const TextStyle(fontWeight: FontWeight.w600)),
                  Text('Phone: ${quote['customer_phone']}'),
                  if (quote['delivery_address'] != null) Text('Delivery: ${quote['delivery_address']}'),
                  const Divider(height: 16),
                  Text('Lead Salesperson: ${quote['sales_person_name']}'),
                  if (quote['assisted_by_name'] != null && quote['assisted_by_name'].isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        '🤝 Assisted by: ${quote['assisted_by_name']} (${quote['split_type']} split)',
                        style: TextStyle(color: Colors.indigo.shade800, fontWeight: FontWeight.w500),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Items List
            const Text('Quoted Items', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 8),

            ...areas.map((area) {
              final items = area['items'] as List? ?? [];
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.borderLight),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade50,
                        borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.room_preferences_outlined, size: 16, color: AppTheme.primaryCoral),
                          const SizedBox(width: 6),
                          Text(
                            area['area_name'] ?? 'Section',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                    ListView.separated(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: items.length,
                      separatorBuilder: (_, __) => const Divider(height: 1, indent: 14, endIndent: 14),
                      itemBuilder: (context, i) {
                        final item = items[i];
                        final pType = item['product_type'] ?? 'Box';
                        String qtyStr;
                        if (pType == 'Box') {
                          qtyStr = "${item['quantity_boxes']} Boxes @ ₹${item['rate_per_box']}/Box";
                        } else if (pType == 'Sqft') {
                          qtyStr = "${item['quantity_sqft']} Sqft @ ₹${item['rate_per_sqft']}/Sqft";
                        } else {
                          qtyStr = "${item['quantity_boxes']} $pType @ ₹${item['rate_per_box']}/$pType";
                        }

                        return ListTile(
                          dense: true,
                          title: Text(
                            item['description'] ?? 'Ceramic Tile',
                            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                          ),
                          subtitle: Text(
                            "${item['brand']} • ${item['size']}\n$qtyStr",
                            style: const TextStyle(fontSize: 11),
                          ),
                          trailing: Text(
                            currencyFormat.format(item['total_amount']),
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              );
            }),

            // Price Summary
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.borderLight),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Taxable Subtotal'),
                      Text(currencyFormat.format(quote['taxable_amount'])),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('GST (18%)'),
                      Text(currencyFormat.format(quote['total_tax'])),
                    ],
                  ),
                  const Divider(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Final Net Payable', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                      Text(
                        currencyFormat.format(quote['net_total']),
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppTheme.primaryCoral),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
