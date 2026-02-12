import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/utils/extensions.dart';
import 'package:loadmovegh/core/utils/validators.dart';
import 'package:loadmovegh/core/widgets/status_badge.dart';

/// Bid management page — couriers see their bids, shippers see bids on loads.

class BidPage extends ConsumerStatefulWidget {
  const BidPage({super.key});

  @override
  ConsumerState<BidPage> createState() => _BidPageState();
}

class _BidPageState extends ConsumerState<BidPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Bids'),
        bottom: TabBar(
          controller: _tabCtrl,
          labelColor: AppColors.brand600,
          unselectedLabelColor: AppColors.gray500,
          indicatorColor: AppColors.brand600,
          tabs: const [
            Tab(text: 'Active'),
            Tab(text: 'History'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabCtrl,
        children: [
          _buildBidList(active: true),
          _buildBidList(active: false),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showNewBidSheet(context),
        backgroundColor: AppColors.brand600,
        icon: const Icon(Icons.gavel_rounded, color: Colors.white),
        label:
            const Text('New Bid', style: TextStyle(color: Colors.white)),
      ),
    );
  }

  Widget _buildBidList({required bool active}) {
    // Mock bid data
    final bids = active
        ? [
            _BidData('BID-001', 'Accra → Kumasi', 850, 'pending', DateTime.now()),
            _BidData('BID-002', 'Tema → Tamale', 2100, 'pending',
                DateTime.now().subtract(const Duration(hours: 3))),
          ]
        : [
            _BidData('BID-003', 'Takoradi → Accra', 920, 'accepted',
                DateTime.now().subtract(const Duration(days: 2))),
            _BidData('BID-004', 'Cape Coast → Kumasi', 650, 'rejected',
                DateTime.now().subtract(const Duration(days: 5))),
          ];

    if (bids.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.gavel_outlined, size: 48, color: AppColors.gray300),
            const SizedBox(height: 12),
            Text(
              active ? 'No active bids' : 'No bid history',
              style: const TextStyle(color: AppColors.gray500),
            ),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: bids.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final bid = bids[index];
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.gray100),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      bid.route,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: AppColors.gray800,
                      ),
                    ),
                  ),
                  _statusBadge(bid.status),
                ],
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  const Icon(Icons.monetization_on_outlined,
                      size: 16, color: AppColors.brand600),
                  const SizedBox(width: 6),
                  Text(
                    bid.amount.ghs,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.brand700,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    bid.date.timeAgo,
                    style:
                        const TextStyle(fontSize: 12, color: AppColors.gray400),
                  ),
                ],
              ),
              if (bid.status == 'pending') ...[
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () {
                          // Withdraw bid
                        },
                        child: const Text('Withdraw'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () {
                          // Edit bid
                        },
                        child: const Text('Edit'),
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _statusBadge(String status) {
    return switch (status) {
      'accepted' => StatusBadge.success('Accepted'),
      'rejected' => StatusBadge.error('Rejected'),
      'withdrawn' => StatusBadge.info('Withdrawn'),
      _ => StatusBadge.warning('Pending'),
    };
  }

  void _showNewBidSheet(BuildContext context) {
    final amountCtrl = TextEditingController();
    final noteCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => Padding(
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
              const Text(
                'Place a Bid',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: AppColors.gray900,
                ),
              ),
              const SizedBox(height: 20),
              TextFormField(
                controller: amountCtrl,
                decoration: const InputDecoration(
                  labelText: 'Bid Amount (GHS)',
                  prefixText: 'GHS ',
                  prefixIcon: Icon(Icons.attach_money, size: 20),
                ),
                keyboardType: TextInputType.number,
                validator: Validators.amount,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: noteCtrl,
                decoration: const InputDecoration(
                  labelText: 'Note (Optional)',
                  hintText: 'E.g. can deliver same day',
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    if (formKey.currentState!.validate()) {
                      Navigator.pop(context);
                      // Submit bid via provider
                    }
                  },
                  child: const Text('Submit Bid'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _BidData {
  final String id;
  final String route;
  final double amount;
  final String status;
  final DateTime date;
  _BidData(this.id, this.route, this.amount, this.status, this.date);
}
