import 'package:flutter/material.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/features/assistant/domain/entities/chat_entity.dart';

/// Renders a rich card for tool call results (loads, pricing, route, etc.).

class ToolResultCard extends StatelessWidget {
  final ToolCallEntity toolCall;
  const ToolResultCard({super.key, required this.toolCall});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.85,
        ),
        child: _buildCard(),
      ),
    );
  }

  Widget _buildCard() {
    return switch (toolCall.toolName) {
      'suggest_best_loads' => _buildLoadsCard(),
      'recommend_pricing' => _buildPricingCard(),
      'show_profit_forecast' => _buildProfitCard(),
      'optimize_route' => _buildRouteCard(),
      _ => _buildGenericCard(),
    };
  }

  // ── Load suggestions ─────────────────────────────────────

  Widget _buildLoadsCard() {
    final loads = (toolCall.result['loads'] as List?)?.cast<Map>() ?? [];
    final found = toolCall.result['loads_found'] ?? 0;

    return _cardWrapper(
      icon: Icons.inventory_2_outlined,
      iconColor: AppColors.brand600,
      title: '$found loads found',
      child: Column(
        children: loads.take(3).map((load) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.gray50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          load['route']?.toString() ?? '',
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: AppColors.gray800,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${load["cargo_type"]} • ${load["weight_kg"]} kg • ${load["urgency"]}',
                          style: const TextStyle(fontSize: 11, color: AppColors.gray500),
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        load['budget']?.toString() ?? '',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppColors.brand700,
                        ),
                      ),
                      Text(
                        'Score: ${load["match_score"]}',
                        style: const TextStyle(fontSize: 10, color: AppColors.gray500),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  // ── Pricing recommendation ───────────────────────────────

  Widget _buildPricingCard() {
    final rec = toolCall.result['recommended_price']?.toString() ?? 'N/A';
    final range = toolCall.result['price_range'] as Map? ?? {};
    final courier = toolCall.result['for_courier'] as Map? ?? {};

    return _cardWrapper(
      icon: Icons.attach_money,
      iconColor: AppColors.accent600,
      title: 'Price Recommendation',
      child: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.brand50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              children: [
                const Text('Recommended', style: TextStyle(fontSize: 11, color: AppColors.gray500)),
                Text(
                  rec,
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                    color: AppColors.brand700,
                  ),
                ),
                Text(
                  'Range: ${range["min"]} – ${range["max"]}',
                  style: const TextStyle(fontSize: 12, color: AppColors.gray600),
                ),
              ],
            ),
          ),
          if (courier.isNotEmpty) ...[
            const SizedBox(height: 8),
            _detailRow('Commission', courier['commission_amount']?.toString() ?? ''),
            _detailRow('Net Earnings', courier['net_earnings']?.toString() ?? ''),
          ],
        ],
      ),
    );
  }

  // ── Profit forecast ──────────────────────────────────────

  Widget _buildProfitCard() {
    final forecast = toolCall.result['forecast'] as Map? ?? {};
    final history = toolCall.result['historical_basis'] as Map? ?? {};

    return _cardWrapper(
      icon: Icons.trending_up,
      iconColor: AppColors.success,
      title: '${toolCall.result["forecast_days"]}-Day Forecast',
      child: Column(
        children: [
          if (forecast.isNotEmpty) ...[
            _metricTile('Projected Revenue', forecast['projected_revenue']?.toString() ?? '', AppColors.brand600),
            _metricTile('Fuel Costs', forecast['estimated_fuel_costs']?.toString() ?? '', AppColors.warning),
            _metricTile('Commission', forecast['platform_commission']?.toString() ?? '', AppColors.gray500),
            const Divider(height: 16),
            _metricTile('Net Profit', forecast['projected_net_profit']?.toString() ?? '', AppColors.success),
          ] else ...[
            Text(
              toolCall.result['message']?.toString() ?? 'No forecast available.',
              style: const TextStyle(fontSize: 13, color: AppColors.gray600),
            ),
          ],
        ],
      ),
    );
  }

  // ── Route optimization ───────────────────────────────────

  Widget _buildRouteCard() {
    return _cardWrapper(
      icon: Icons.map_outlined,
      iconColor: AppColors.info,
      title: toolCall.result['route']?.toString() ?? 'Route Info',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (toolCall.result['distance_km'] != null ||
              toolCall.result['estimated_distance_km'] != null)
            _detailRow('Distance', '${toolCall.result["distance_km"] ?? toolCall.result["estimated_distance_km"]} km'),
          if (toolCall.result['estimated_time'] != null)
            _detailRow('Est. Time', toolCall.result['estimated_time'].toString()),
          if (toolCall.result['road_type'] != null)
            _detailRow('Road', toolCall.result['road_type'].toString()),
          if (toolCall.result['road_condition'] != null)
            _detailRow('Condition', toolCall.result['road_condition'].toString()),
          if (toolCall.result['estimated_fuel_cost'] != null)
            _detailRow('Fuel Cost', toolCall.result['estimated_fuel_cost'].toString()),
          if (toolCall.result['tips'] != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.accent50,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.lightbulb_outline, size: 14, color: AppColors.accent600),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      toolCall.result['tips'].toString(),
                      style: const TextStyle(fontSize: 12, color: AppColors.accent600),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ── Generic fallback ─────────────────────────────────────

  Widget _buildGenericCard() {
    return _cardWrapper(
      icon: Icons.info_outline,
      iconColor: AppColors.gray600,
      title: toolCall.toolName.replaceAll('_', ' '),
      child: Text(
        toolCall.result.toString(),
        style: const TextStyle(fontSize: 12, color: AppColors.gray600),
        maxLines: 5,
        overflow: TextOverflow.ellipsis,
      ),
    );
  }

  // ── Shared wrapper ───────────────────────────────────────

  Widget _cardWrapper({
    required IconData icon,
    required Color iconColor,
    required String title,
    required Widget child,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.gray100),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.05),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(14)),
            ),
            child: Row(
              children: [
                Icon(icon, size: 16, color: iconColor),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: iconColor,
                  ),
                ),
              ],
            ),
          ),
          // Body
          Padding(
            padding: const EdgeInsets.all(14),
            child: child,
          ),
        ],
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: AppColors.gray500)),
          Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.gray800)),
        ],
      ),
    );
  }

  Widget _metricTile(String label, String value, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: AppColors.gray600)),
          Text(value, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: color)),
        ],
      ),
    );
  }
}
