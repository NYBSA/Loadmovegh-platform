import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/utils/extensions.dart';
import 'package:loadmovegh/core/widgets/status_badge.dart';
import 'package:loadmovegh/features/loads/presentation/providers/load_provider.dart';

class LoadDetailPage extends ConsumerWidget {
  final String loadId;
  const LoadDetailPage({super.key, required this.loadId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(loadBoardProvider);
    final load = state.loads.where((l) => l.id == loadId).firstOrNull;

    if (load == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: Text('Load not found')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Load Details'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Title & status ────────────────────────
            Row(
              children: [
                Expanded(
                  child: Text(
                    load.title,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: AppColors.gray900,
                    ),
                  ),
                ),
                StatusBadge.success(load.status.toUpperCase()),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'Posted by ${load.shipperName}',
              style: const TextStyle(fontSize: 13, color: AppColors.gray500),
            ),
            const SizedBox(height: 20),

            // ── Route card ────────────────────────────
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.gray100),
              ),
              child: Column(
                children: [
                  _routeRow(
                    icon: Icons.circle,
                    iconColor: AppColors.brand500,
                    city: load.originCity,
                    region: load.originRegion,
                    label: 'PICKUP',
                  ),
                  Padding(
                    padding: const EdgeInsets.only(left: 8),
                    child: Column(
                      children: List.generate(
                        3,
                        (_) => Container(
                          width: 1.5,
                          height: 6,
                          margin: const EdgeInsets.symmetric(vertical: 2),
                          color: AppColors.gray300,
                        ),
                      ),
                    ),
                  ),
                  _routeRow(
                    icon: Icons.location_on,
                    iconColor: AppColors.error,
                    city: load.destCity,
                    region: load.destRegion,
                    label: 'DELIVERY',
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '${load.distanceKm.toStringAsFixed(0)} km',
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          color: AppColors.gray700,
                        ),
                      ),
                      Text(
                        'Pickup: ${load.pickupDate.formatted}',
                        style: const TextStyle(
                            fontSize: 13, color: AppColors.gray500),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // ── Details grid ──────────────────────────
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.gray100),
              ),
              child: Column(
                children: [
                  _detailRow('Cargo Type', load.cargoType),
                  _detailRow('Vehicle Type', load.vehicleType),
                  _detailRow('Weight', '${load.weightKg.toStringAsFixed(0)} kg'),
                  _detailRow('Urgency', load.urgency),
                  _detailRow('Bids', '${load.bidCount}'),
                  if (load.budgetMin != null)
                    _detailRow('Budget',
                        '${load.budgetMin!.ghs} – ${load.budgetMax?.ghs ?? "N/A"}'),
                  if (load.aiPriceMin != null)
                    _detailRow('AI Price Range',
                        '${load.aiPriceMin!.ghs} – ${load.aiPriceMax?.ghs ?? "N/A"}'),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // ── Description ───────────────────────────
            if (load.description.isNotEmpty) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.gray100),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Description',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: AppColors.gray700,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      load.description,
                      style: const TextStyle(
                          fontSize: 14, color: AppColors.gray600, height: 1.5),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],
          ],
        ),
      ),

      // ── Bottom bid button ───────────────────────────
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: ElevatedButton.icon(
            onPressed: () {
              // Navigate to bid page or show bid modal
              context.pushNamed('bids');
            },
            icon: const Icon(Icons.gavel_rounded, size: 20),
            label: const Text('Place Bid'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ),
      ),
    );
  }

  Widget _routeRow({
    required IconData icon,
    required Color iconColor,
    required String city,
    required String region,
    required String label,
  }) {
    return Row(
      children: [
        Icon(icon, size: 16, color: iconColor),
        const SizedBox(width: 12),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: AppColors.gray400,
                letterSpacing: 1,
              ),
            ),
            Text(
              '$city, $region',
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: AppColors.gray800,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.gray500, fontSize: 13)),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.w600,
              color: AppColors.gray800,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}
