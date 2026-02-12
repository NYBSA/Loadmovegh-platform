import 'package:flutter/material.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/utils/extensions.dart';
import 'package:loadmovegh/core/widgets/status_badge.dart';
import 'package:loadmovegh/features/loads/domain/entities/load_entity.dart';

/// A card displaying a freight load summary — used on the load board.

class LoadCard extends StatelessWidget {
  final LoadEntity load;
  final VoidCallback? onTap;

  const LoadCard({super.key, required this.load, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.gray100),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.03),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header row ────────────────────────────
            Row(
              children: [
                Expanded(
                  child: Text(
                    load.title,
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: AppColors.gray900,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                _urgencyBadge(load.urgency),
              ],
            ),
            const SizedBox(height: 10),

            // ── Route ─────────────────────────────────
            Row(
              children: [
                const Icon(Icons.circle, size: 8, color: AppColors.brand500),
                const SizedBox(width: 6),
                Text(
                  load.originCity,
                  style: const TextStyle(fontSize: 13, color: AppColors.gray700),
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 6),
                  child: Icon(Icons.arrow_forward, size: 14, color: AppColors.gray400),
                ),
                const Icon(Icons.location_on, size: 14, color: AppColors.error),
                const SizedBox(width: 4),
                Text(
                  load.destCity,
                  style: const TextStyle(fontSize: 13, color: AppColors.gray700),
                ),
                const Spacer(),
                Text(
                  '${load.distanceKm.toStringAsFixed(0)} km',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.gray500,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // ── Details row ───────────────────────────
            Row(
              children: [
                _infoChip(Icons.category_outlined, load.cargoType),
                const SizedBox(width: 8),
                _infoChip(Icons.local_shipping_outlined, load.vehicleType),
                const SizedBox(width: 8),
                _infoChip(Icons.scale_outlined, '${load.weightKg.toStringAsFixed(0)} kg'),
                const Spacer(),
                Text(
                  '${load.bidCount} bids',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.gray500,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // ── Price / date row ──────────────────────
            Row(
              children: [
                if (load.budgetMax != null)
                  Text(
                    'Budget: ${load.budgetMax!.ghs}',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: AppColors.brand700,
                    ),
                  ),
                if (load.aiPriceMin != null && load.aiPriceMax != null) ...[
                  const SizedBox(width: 12),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.accent50,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      'AI: ${load.aiPriceMin!.ghs}–${load.aiPriceMax!.ghs}',
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.accent600,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
                const Spacer(),
                Text(
                  load.pickupDate.formatted,
                  style: const TextStyle(fontSize: 12, color: AppColors.gray400),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _urgencyBadge(String urgency) {
    return switch (urgency) {
      'urgent' => StatusBadge.error('Urgent'),
      'express' => StatusBadge.warning('Express'),
      'scheduled' => StatusBadge.info('Scheduled'),
      _ => StatusBadge.success('Standard'),
    };
  }

  Widget _infoChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.gray50,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: AppColors.gray500),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(fontSize: 11, color: AppColors.gray600),
          ),
        ],
      ),
    );
  }
}
