import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/widgets/status_badge.dart';

/// Map tracking page — shows active trips with real-time courier position.

class TrackingPage extends ConsumerStatefulWidget {
  const TrackingPage({super.key});

  @override
  ConsumerState<TrackingPage> createState() => _TrackingPageState();
}

class _TrackingPageState extends ConsumerState<TrackingPage> {
  String? _selectedTripId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Live Tracking')),
      body: Column(
        children: [
          // ── Map area ────────────────────────────────
          Expanded(
            flex: 3,
            child: Container(
              width: double.infinity,
              color: AppColors.gray100,
              child: Stack(
                children: [
                  // Placeholder for GoogleMap widget
                  const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.map_rounded, size: 64, color: AppColors.gray300),
                        SizedBox(height: 8),
                        Text(
                          'Map View',
                          style: TextStyle(
                            color: AppColors.gray400,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Real-time GPS tracking appears here',
                          style: TextStyle(color: AppColors.gray400, fontSize: 12),
                        ),
                      ],
                    ),
                  ),

                  // ── Map controls ────────────────────
                  Positioned(
                    right: 16,
                    bottom: 16,
                    child: Column(
                      children: [
                        _mapButton(Icons.my_location, () {}),
                        const SizedBox(height: 8),
                        _mapButton(Icons.layers_outlined, () {}),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),

          // ── Trip list ───────────────────────────────
          Expanded(
            flex: 2,
            child: Container(
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black12,
                    blurRadius: 10,
                    offset: Offset(0, -2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Drag handle
                  Center(
                    child: Container(
                      margin: const EdgeInsets.only(top: 12),
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: AppColors.gray300,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  const Padding(
                    padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
                    child: Text(
                      'Active Shipments',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: AppColors.gray900,
                      ),
                    ),
                  ),
                  Expanded(
                    child: ListView(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      children: [
                        _tripTile(
                          id: 'trip_1',
                          route: 'Accra → Kumasi',
                          status: 'in_transit',
                          eta: '2h 15m',
                          distance: '248 km',
                        ),
                        _tripTile(
                          id: 'trip_2',
                          route: 'Tema → Takoradi',
                          status: 'pickup_pending',
                          eta: 'Awaiting pickup',
                          distance: '218 km',
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _tripTile({
    required String id,
    required String route,
    required String status,
    required String eta,
    required String distance,
  }) {
    final isSelected = _selectedTripId == id;
    return GestureDetector(
      onTap: () => setState(() => _selectedTripId = id),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.brand50 : AppColors.gray50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? AppColors.brand400 : AppColors.gray100,
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: status == 'in_transit'
                    ? AppColors.brand100
                    : AppColors.accent100,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                status == 'in_transit'
                    ? Icons.local_shipping_rounded
                    : Icons.schedule_rounded,
                size: 20,
                color: status == 'in_transit'
                    ? AppColors.brand700
                    : AppColors.accent600,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    route,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: AppColors.gray800,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '$eta • $distance',
                    style: const TextStyle(
                        fontSize: 12, color: AppColors.gray500),
                  ),
                ],
              ),
            ),
            StatusBadge(
              label: status == 'in_transit' ? 'In Transit' : 'Pending',
              variant: status == 'in_transit'
                  ? StatusBadgeVariant.success
                  : StatusBadgeVariant.warning,
            ),
          ],
        ),
      ),
    );
  }

  Widget _mapButton(IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          boxShadow: const [
            BoxShadow(color: Colors.black12, blurRadius: 4),
          ],
        ),
        child: Icon(icon, size: 20, color: AppColors.gray700),
      ),
    );
  }
}
