import 'package:flutter/material.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';

/// Colored status badge matching the web dashboard badge styles.

class StatusBadge extends StatelessWidget {
  final String label;
  final StatusBadgeVariant variant;

  const StatusBadge({
    super.key,
    required this.label,
    this.variant = StatusBadgeVariant.info,
  });

  factory StatusBadge.success(String label) =>
      StatusBadge(label: label, variant: StatusBadgeVariant.success);
  factory StatusBadge.warning(String label) =>
      StatusBadge(label: label, variant: StatusBadgeVariant.warning);
  factory StatusBadge.error(String label) =>
      StatusBadge(label: label, variant: StatusBadgeVariant.error);
  factory StatusBadge.info(String label) =>
      StatusBadge(label: label, variant: StatusBadgeVariant.info);

  @override
  Widget build(BuildContext context) {
    final (bg, fg) = switch (variant) {
      StatusBadgeVariant.success => (AppColors.badgeGreenBg, AppColors.badgeGreenFg),
      StatusBadgeVariant.warning => (AppColors.badgeYellowBg, AppColors.badgeYellowFg),
      StatusBadgeVariant.error => (AppColors.badgeRedBg, AppColors.badgeRedFg),
      StatusBadgeVariant.info => (AppColors.badgeBlueBg, AppColors.badgeBlueFg),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: fg,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

enum StatusBadgeVariant { success, warning, error, info }
