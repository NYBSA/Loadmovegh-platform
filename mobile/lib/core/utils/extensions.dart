import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// Convenience extensions used across the app.

// ── String ─────────────────────────────────────────────────

extension StringX on String {
  /// Capitalize first letter.
  String get capitalised =>
      isEmpty ? this : '${this[0].toUpperCase()}${substring(1)}';

  /// Truncate to [max] chars with ellipsis.
  String truncate(int max) =>
      length <= max ? this : '${substring(0, max)}…';
}

// ── DateTime ───────────────────────────────────────────────

extension DateTimeX on DateTime {
  /// "12 Feb 2026"
  String get formatted => DateFormat('d MMM yyyy').format(this);

  /// "12 Feb, 3:45 PM"
  String get formattedWithTime =>
      DateFormat('d MMM, h:mm a').format(this);

  /// "2 hours ago" / "Just now"
  String get timeAgo {
    final diff = DateTime.now().difference(this);
    if (diff.inSeconds < 60) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return formatted;
  }
}

// ── double (currency) ──────────────────────────────────────

extension DoubleX on double {
  /// "GHS 1,234.50"
  String get ghs => 'GHS ${NumberFormat('#,##0.00').format(this)}';
}

// ── BuildContext ────────────────────────────────────────────

extension ContextX on BuildContext {
  ThemeData get theme => Theme.of(this);
  TextTheme get textTheme => theme.textTheme;
  ColorScheme get colorScheme => theme.colorScheme;
  Size get screenSize => MediaQuery.sizeOf(this);
  bool get isMobile => screenSize.width < 600;

  void showSnack(String message, {bool isError = false}) {
    ScaffoldMessenger.of(this).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red.shade700 : null,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );
  }
}
