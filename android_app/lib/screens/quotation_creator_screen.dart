import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/customer.dart';
import '../models/brand.dart';
import '../models/salesperson.dart';
import '../models/quotation.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class QuotationCreatorScreen extends StatefulWidget {
  const QuotationCreatorScreen({super.key});

  @override
  State<QuotationCreatorScreen> createState() => _QuotationCreatorScreenState();
}

class _QuotationCreatorScreenState extends State<QuotationCreatorScreen> {
  bool _isLoading = true;
  bool _isSaving = false;

  List<CustomerModel> _customers = [];
  List<BrandModel> _brands = [];
  List<SalesPersonModel> _salespersons = [];

  CustomerModel? _selectedCustomer;
  SalesPersonModel? _selectedSalesPerson;
  SalesPersonModel? _selectedAssistedBy;
  String _splitType = 'none'; // none, percentage, amount
  final TextEditingController _assistedShareController = TextEditingController(text: '0');

  final TextEditingController _targetTotalController = TextEditingController();

  final List<QuotationItemInput> _items = [];
  final currencyFormat = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    try {
      final results = await Future.wait([
        ApiService.fetchCustomers(),
        ApiService.fetchBrands(),
        ApiService.fetchSalespersons(),
      ]);

      if (mounted) {
        setState(() {
          _customers = results[0] as List<CustomerModel>;
          _brands = results[1] as List<BrandModel>;
          _salespersons = results[2] as List<SalesPersonModel>;

          if (_customers.isNotEmpty) _selectedCustomer = _customers.first;
          if (_salespersons.isNotEmpty) _selectedSalesPerson = _salespersons.first;

          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load metadata: $e')),
        );
      }
    }
  }

  void _addItem() {
    setState(() {
      String defaultBrand = _brands.isNotEmpty ? _brands.first.name : 'AMA Ceramics';
      String defaultSize = (_brands.isNotEmpty && _brands.first.sizes.isNotEmpty)
          ? _brands.first.sizes.first.sizeLabel
          : '600X1200';
      String defaultType = (_brands.isNotEmpty && _brands.first.sizes.isNotEmpty)
          ? _brands.first.sizes.first.productType
          : 'Box';
      double defaultRate = (_brands.isNotEmpty && _brands.first.sizes.isNotEmpty)
          ? _brands.first.sizes.first.defaultRatePerBox
          : 1000.0;

      final newItem = QuotationItemInput(
        slNo: _items.length + 1,
        description: '$defaultBrand Ceramic Tile',
        brand: defaultBrand,
        size: defaultSize,
        productType: defaultType,
        quantityBoxes: defaultType == 'Sqft' ? 0 : 1,
        ratePerBox: defaultType == 'Sqft' ? 0 : defaultRate,
        quantitySqft: defaultType == 'Sqft' ? 50 : 0,
        ratePerSqft: defaultType == 'Sqft' ? 45 : 0,
        taxMode: 'exclusive',
        taxPercent: 18.0,
      );

      _recalculateItem(newItem);
      _items.add(newItem);
    });
  }

  void _recalculateItem(QuotationItemInput item) {
    double taxable = 0.0;
    if (item.productType == 'Sqft') {
      taxable = item.quantitySqft * item.ratePerSqft;
    } else {
      taxable = item.quantityBoxes * item.ratePerBox;
    }

    item.taxableAmount = taxable;
    if (item.taxMode == 'exclusive') {
      item.gstAmount = (taxable * item.taxPercent) / 100.0;
      item.totalAmount = taxable + item.gstAmount;
    } else {
      // Inclusive
      item.totalAmount = taxable;
      item.gstAmount = taxable - (taxable / (1.0 + item.taxPercent / 100.0));
      item.taxableAmount = taxable - item.gstAmount;
    }
  }

  double get _subtotalTaxable => _items.fold(0.0, (sum, i) => sum + i.taxableAmount);
  double get _totalGst => _items.fold(0.0, (sum, i) => sum + i.gstAmount);
  double get _grossNetTotal => _items.fold(0.0, (sum, i) => sum + i.totalAmount);

  // Exact CERA brand exclusion discount distribution formula
  void _applyDiscountAdjustment() {
    final targetStr = _targetTotalController.text.trim();
    if (targetStr.isEmpty) return;
    final targetVal = double.tryParse(targetStr);
    if (targetVal == null || targetVal <= 0) return;

    double currentTotal = _grossNetTotal;
    if (targetVal >= currentTotal) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Discounted value must be less than current total.')),
      );
      return;
    }

    double discountAmount = currentTotal - targetVal;

    // Calculate sum of eligible non-CERA items
    double nonCeraEligibleSum = 0.0;
    for (var item in _items) {
      if (!item.brand.toUpperCase().contains('CERA')) {
        nonCeraEligibleSum += item.totalAmount;
      }
    }

    if (nonCeraEligibleSum <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Cannot apply discount: All items are CERA brand which cannot be discounted.')),
      );
      return;
    }

    if (discountAmount > nonCeraEligibleSum) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Discount ₹${discountAmount.toStringAsFixed(0)} exceeds non-CERA value ₹${nonCeraEligibleSum.toStringAsFixed(0)}.',
          ),
        ),
      );
      return;
    }

    double discountRatio = discountAmount / nonCeraEligibleSum;

    setState(() {
      for (var item in _items) {
        if (!item.brand.toUpperCase().contains('CERA')) {
          double itemTargetTotal = item.totalAmount * (1.0 - discountRatio);

          if (item.productType == 'Sqft') {
            if (item.quantitySqft > 0) {
              if (item.taxMode == 'exclusive') {
                double newTaxable = itemTargetTotal / (1.0 + item.taxPercent / 100.0);
                item.ratePerSqft = newTaxable / item.quantitySqft;
              } else {
                item.ratePerSqft = itemTargetTotal / item.quantitySqft;
              }
            }
          } else {
            if (item.quantityBoxes > 0) {
              if (item.taxMode == 'exclusive') {
                double newTaxable = itemTargetTotal / (1.0 + item.taxPercent / 100.0);
                item.ratePerBox = newTaxable / item.quantityBoxes;
              } else {
                item.ratePerBox = itemTargetTotal / item.quantityBoxes;
              }
            }
          }
          _recalculateItem(item);
        }
      }
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Discount of ₹${discountAmount.toStringAsFixed(0)} distributed across non-CERA items (CERA items preserved).',
        ),
        backgroundColor: AppTheme.successGreen,
      ),
    );
  }

  Future<void> _saveQuotation() async {
    if (_selectedCustomer == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a customer')),
      );
      return;
    }
    if (_selectedSalesPerson == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a sales person')),
      );
      return;
    }
    if (_items.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please add at least one item to quote')),
      );
      return;
    }

    setState(() => _isSaving = true);

    try {
      final payload = {
        'customer_id': _selectedCustomer!.id,
        'sales_person_id': _selectedSalesPerson!.id,
        'assisted_by_id': _selectedAssistedBy?.id,
        'split_type': _splitType,
        'assisted_share_value': double.tryParse(_assistedShareController.text) ?? 0.0,
        'tax_mode': 'exclusive',
        'areas': [
          {
            'area_name': 'Quoted Items',
            'display_order': 1,
            'items': _items.map((i) => i.toJson()).toList(),
          }
        ],
      };

      final result = await ApiService.saveQuotation(payload);
      if (mounted) {
        setState(() => _isSaving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Quotation ${result['quotation_number']} saved & synced to cloud!'),
            backgroundColor: AppTheme.successGreen,
          ),
        );
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSaving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error saving quotation: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Create Quotation')),
        body: const Center(child: CircularProgressIndicator(color: AppTheme.primaryCoral)),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('New Ceramic Quotation'),
        actions: [
          IconButton(
            icon: _isSaving
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(color: AppTheme.primaryCoral, strokeWidth: 2),
                  )
                : const Icon(Icons.check, color: AppTheme.successGreen, size: 28),
            onPressed: _isSaving ? null : _saveQuotation,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Customer Selector
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
                  const Text('Select Customer', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(height: 6),
                  DropdownButtonFormField<CustomerModel>(
                    value: _selectedCustomer,
                    decoration: const InputDecoration(isDense: true),
                    items: _customers.map((c) {
                      return DropdownMenuItem(
                        value: c,
                        child: Text('${c.name} (${c.phone})', overflow: TextOverflow.ellipsis),
                      );
                    }).toList(),
                    onChanged: (val) => setState(() => _selectedCustomer = val),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // Sales Team & Assisted Collaboration
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
                  const Text('Sales Attribution', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(height: 6),
                  DropdownButtonFormField<SalesPersonModel>(
                    value: _selectedSalesPerson,
                    decoration: const InputDecoration(labelText: 'Lead Salesperson', isDense: true),
                    items: _salespersons.map((s) {
                      return DropdownMenuItem(
                        value: s,
                        child: Text(s.name),
                      );
                    }).toList(),
                    onChanged: (val) => setState(() => _selectedSalesPerson = val),
                  ),
                  const SizedBox(height: 10),

                  // Assisted By
                  DropdownButtonFormField<SalesPersonModel?>(
                    value: _selectedAssistedBy,
                    decoration: const InputDecoration(labelText: 'Assisted by (Optional)', isDense: true),
                    items: [
                      const DropdownMenuItem(value: null, child: Text('None (Sole Deal)')),
                      ..._salespersons.where((s) => s != _selectedSalesPerson).map((s) {
                        return DropdownMenuItem(value: s, child: Text(s.name));
                      }),
                    ],
                    onChanged: (val) => setState(() => _selectedAssistedBy = val),
                  ),

                  if (_selectedAssistedBy != null) ...[
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            value: _splitType,
                            decoration: const InputDecoration(labelText: 'Split Type', isDense: true),
                            items: const [
                              DropdownMenuItem(value: 'none', child: Text('None')),
                              DropdownMenuItem(value: 'percentage', child: Text('Percentage %')),
                              DropdownMenuItem(value: 'amount', child: Text('Fixed Amount ₹')),
                            ],
                            onChanged: (val) => setState(() => _splitType = val ?? 'none'),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: TextFormField(
                            controller: _assistedShareController,
                            keyboardType: TextInputType.number,
                            decoration: InputDecoration(
                              labelText: _splitType == 'percentage' ? 'Share %' : 'Share ₹',
                              isDense: true,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Line Items
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Line Items', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ElevatedButton.icon(
                  icon: const Icon(Icons.add, size: 16),
                  label: const Text('Add Item'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  ),
                  onPressed: _addItem,
                ),
              ],
            ),
            const SizedBox(height: 8),

            ..._items.asMap().entries.map((entry) {
              final idx = entry.key;
              final item = entry.value;

              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.borderLight),
                ),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: DropdownButtonFormField<String>(
                            value: item.brand,
                            isDense: true,
                            decoration: const InputDecoration(labelText: 'Brand', isDense: true),
                            items: _brands.map((b) => DropdownMenuItem(value: b.name, child: Text(b.name, overflow: TextOverflow.ellipsis))).toList(),
                            onChanged: (newBrand) {
                              if (newBrand != null) {
                                setState(() {
                                  item.brand = newBrand;
                                  item.description = '$newBrand Tile';
                                });
                              }
                            },
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          flex: 1,
                          child: DropdownButtonFormField<String>(
                            value: item.productType,
                            isDense: true,
                            decoration: const InputDecoration(labelText: 'Unit', isDense: true),
                            items: ['Box', 'Sqft', 'Pieces', 'Bags', 'Nos'].map((u) {
                              return DropdownMenuItem(value: u, child: Text(u));
                            }).toList(),
                            onChanged: (newType) {
                              if (newType != null) {
                                setState(() {
                                  item.productType = newType;
                                  _recalculateItem(item);
                                });
                              }
                            },
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete_outline, color: AppTheme.errorRed, size: 20),
                          onPressed: () => setState(() => _items.removeAt(idx)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),

                    // Inputs based on Product Type
                    if (item.productType == 'Sqft')
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              initialValue: item.quantitySqft.toString(),
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(labelText: 'Quantity (Sqft)', isDense: true),
                              onChanged: (v) {
                                item.quantitySqft = double.tryParse(v) ?? 0;
                                setState(() => _recalculateItem(item));
                              },
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextFormField(
                              initialValue: item.ratePerSqft.toString(),
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(labelText: 'Rate / Sqft', isDense: true),
                              onChanged: (v) {
                                item.ratePerSqft = double.tryParse(v) ?? 0;
                                setState(() => _recalculateItem(item));
                              },
                            ),
                          ),
                        ],
                      )
                    else
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              initialValue: item.quantityBoxes.toString(),
                              keyboardType: TextInputType.number,
                              decoration: InputDecoration(
                                labelText: 'Quantity (${item.productType})',
                                isDense: true,
                              ),
                              onChanged: (v) {
                                item.quantityBoxes = double.tryParse(v) ?? 0;
                                setState(() => _recalculateItem(item));
                              },
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextFormField(
                              initialValue: item.ratePerBox.toString(),
                              keyboardType: TextInputType.number,
                              decoration: InputDecoration(
                                labelText: 'Rate / ${item.productType}',
                                isDense: true,
                              ),
                              onChanged: (v) {
                                item.ratePerBox = double.tryParse(v) ?? 0;
                                setState(() => _recalculateItem(item));
                              },
                            ),
                          ),
                        ],
                      ),

                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Total (+18% GST):', style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
                        Text(
                          currencyFormat.format(item.totalAmount),
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.primaryCoral),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }),

            if (_items.isEmpty)
              Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 20),
                  child: Text(
                    'No items added yet. Click "+ Add Item" above.',
                    style: TextStyle(color: Colors.grey.shade500),
                  ),
                ),
              ),

            const SizedBox(height: 12),

            // CERA Discount Formula Section
            if (_items.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.amber.shade200),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.percent, size: 18, color: AppTheme.warningOrange),
                        SizedBox(width: 6),
                        Text(
                          'Target Total & Smart Discount',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Enter desired final deal value. CERA items are protected with 0% discount and remaining items are discounted proportionally.',
                      style: TextStyle(fontSize: 11, color: AppTheme.textDark),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _targetTotalController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              hintText: 'e.g. 100000',
                              isDense: true,
                              fillColor: Colors.white,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        ElevatedButton(
                          onPressed: _applyDiscountAdjustment,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppTheme.warningOrange,
                          ),
                          child: const Text('Apply'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

            const SizedBox(height: 16),

            // Grand Total Footer
            Container(
              padding: const EdgeInsets.all(16),
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
                      Text(currencyFormat.format(_subtotalTaxable)),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Total GST (18%)'),
                      Text(currencyFormat.format(_totalGst)),
                    ],
                  ),
                  const Divider(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Net Total Payable', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Text(
                        currencyFormat.format(_grossNetTotal),
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 20, color: AppTheme.primaryCoral),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.cloud_upload_outlined),
                      label: Text(_isSaving ? 'Saving to Cloud...' : 'Save & Sync Quotation'),
                      onPressed: _isSaving ? null : _saveQuotation,
                    ),
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
