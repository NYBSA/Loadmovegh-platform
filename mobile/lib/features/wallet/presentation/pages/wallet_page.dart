import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/utils/extensions.dart';
import 'package:loadmovegh/core/utils/validators.dart';

/// Wallet page — balance, deposit/withdraw via MoMo, transaction history.

class WalletPage extends ConsumerStatefulWidget {
  const WalletPage({super.key});

  @override
  ConsumerState<WalletPage> createState() => _WalletPageState();
}

class _WalletPageState extends ConsumerState<WalletPage> {
  // Mock data
  final double _balance = 3450.00;
  final double _escrow = 850.00;
  final double _earnings = 12800.00;

  final _transactions = <_TxData>[
    _TxData('Deposit via MTN MoMo', 500, 'deposit', 'completed',
        DateTime.now().subtract(const Duration(hours: 1))),
    _TxData('Escrow hold — BID-001', -850, 'escrow_hold', 'completed',
        DateTime.now().subtract(const Duration(hours: 5))),
    _TxData('Payout — Trip #TRP-042', 1200, 'payout', 'completed',
        DateTime.now().subtract(const Duration(days: 1))),
    _TxData('Commission — 5%', -60, 'commission', 'completed',
        DateTime.now().subtract(const Duration(days: 1))),
    _TxData('Withdrawal to MoMo', -400, 'withdrawal', 'completed',
        DateTime.now().subtract(const Duration(days: 3))),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Wallet')),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // ── Balance card ──────────────────────────
            Container(
              width: double.infinity,
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.brand700, AppColors.brand500],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.brand600.withOpacity(0.3),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Available Balance',
                    style: TextStyle(
                      color: Colors.white70,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _balance.ghs,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 32,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      _balanceStat('In Escrow', _escrow.ghs),
                      const SizedBox(width: 24),
                      _balanceStat('Total Earnings', _earnings.ghs),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // ── Action buttons ──────────────────
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () => _showMoMoSheet(context, isDeposit: true),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.white,
                            foregroundColor: AppColors.brand700,
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                          icon: const Icon(Icons.add_circle_outline, size: 18),
                          label: const Text('Deposit'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () =>
                              _showMoMoSheet(context, isDeposit: false),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.white,
                            side: const BorderSide(color: Colors.white54),
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                          icon: const Icon(Icons.arrow_upward_rounded, size: 18),
                          label: const Text('Withdraw'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // ── Transaction history ───────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Recent Transactions',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.gray900,
                    ),
                  ),
                  TextButton(
                    onPressed: () {},
                    child: const Text('See All'),
                  ),
                ],
              ),
            ),

            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 80),
              itemCount: _transactions.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final tx = _transactions[index];
                final isPositive = tx.amount >= 0;

                return ListTile(
                  contentPadding: const EdgeInsets.symmetric(vertical: 6),
                  leading: Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isPositive
                          ? AppColors.badgeGreenBg
                          : AppColors.badgeRedBg,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      _txIcon(tx.type),
                      size: 20,
                      color: isPositive
                          ? AppColors.badgeGreenFg
                          : AppColors.badgeRedFg,
                    ),
                  ),
                  title: Text(
                    tx.description,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: AppColors.gray800,
                    ),
                  ),
                  subtitle: Text(
                    tx.date.timeAgo,
                    style: const TextStyle(fontSize: 12, color: AppColors.gray400),
                  ),
                  trailing: Text(
                    '${isPositive ? "+" : ""}${tx.amount.ghs}',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color:
                          isPositive ? AppColors.success : AppColors.error,
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _balanceStat(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: const TextStyle(color: Colors.white60, fontSize: 11)),
        const SizedBox(height: 2),
        Text(value,
            style: const TextStyle(
                color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
      ],
    );
  }

  IconData _txIcon(String type) {
    return switch (type) {
      'deposit' => Icons.arrow_downward_rounded,
      'withdrawal' => Icons.arrow_upward_rounded,
      'escrow_hold' => Icons.lock_outline,
      'payout' => Icons.payments_outlined,
      'commission' => Icons.percent,
      _ => Icons.receipt_outlined,
    };
  }

  void _showMoMoSheet(BuildContext context, {required bool isDeposit}) {
    final amountCtrl = TextEditingController();
    final phoneCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();
    String provider = 'mtn';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => StatefulBuilder(
        builder: (context, setSheetState) => Padding(
          padding: EdgeInsets.fromLTRB(
            24,
            24,
            24,
            MediaQuery.of(context).viewInsets.bottom + 24,
          ),
          child: Form(
            key: formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: AppColors.gray300,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  isDeposit ? 'Deposit via Mobile Money' : 'Withdraw to Mobile Money',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: AppColors.gray900,
                  ),
                ),
                const SizedBox(height: 20),

                // Provider chips
                Row(
                  children: ['mtn', 'vodafone', 'airteltigo'].map((p) {
                    final selected = provider == p;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(p.toUpperCase()),
                        selected: selected,
                        selectedColor: AppColors.brand100,
                        onSelected: (_) =>
                            setSheetState(() => provider = p),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 16),

                TextFormField(
                  controller: phoneCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Phone Number',
                    hintText: '024XXXXXXX',
                    prefixIcon: Icon(Icons.phone_outlined, size: 20),
                  ),
                  keyboardType: TextInputType.phone,
                  validator: Validators.phone,
                ),
                const SizedBox(height: 16),

                TextFormField(
                  controller: amountCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Amount (GHS)',
                    prefixText: 'GHS ',
                    prefixIcon: Icon(Icons.attach_money, size: 20),
                  ),
                  keyboardType: TextInputType.number,
                  validator: Validators.amount,
                ),
                const SizedBox(height: 24),

                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      if (formKey.currentState!.validate()) {
                        Navigator.pop(context);
                        // Call deposit / withdraw via provider
                      }
                    },
                    child: Text(isDeposit ? 'Deposit' : 'Withdraw'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TxData {
  final String description;
  final double amount;
  final String type;
  final String status;
  final DateTime date;
  _TxData(this.description, this.amount, this.type, this.status, this.date);
}
