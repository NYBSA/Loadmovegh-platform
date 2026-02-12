import 'package:flutter/material.dart';

/// LoadMoveGH — Color palette matching Tailwind config.
///
/// Brand = green (freight/go), Accent = amber (alerts/highlights).

class AppColors {
  const AppColors._();

  // ── Brand (Green) — from tailwind.config.ts ──────────────
  static const Color brand50 = Color(0xFFF0FDF4);
  static const Color brand100 = Color(0xFFDCFCE7);
  static const Color brand200 = Color(0xFFBBF7D0);
  static const Color brand300 = Color(0xFF86EFAC);
  static const Color brand400 = Color(0xFF4ADE80);
  static const Color brand500 = Color(0xFF22C55E);
  static const Color brand600 = Color(0xFF16A34A);
  static const Color brand700 = Color(0xFF15803D);
  static const Color brand800 = Color(0xFF166534);
  static const Color brand900 = Color(0xFF14532D);

  // ── Accent (Amber) ───────────────────────────────────────
  static const Color accent50 = Color(0xFFFFFBEB);
  static const Color accent100 = Color(0xFFFEF3C7);
  static const Color accent400 = Color(0xFFFBBF24);
  static const Color accent500 = Color(0xFFF59E0B);
  static const Color accent600 = Color(0xFFD97706);

  // ── Grays ────────────────────────────────────────────────
  static const Color gray50 = Color(0xFFF9FAFB);
  static const Color gray100 = Color(0xFFF3F4F6);
  static const Color gray200 = Color(0xFFE5E7EB);
  static const Color gray300 = Color(0xFFD1D5DB);
  static const Color gray400 = Color(0xFF9CA3AF);
  static const Color gray500 = Color(0xFF6B7280);
  static const Color gray600 = Color(0xFF4B5563);
  static const Color gray700 = Color(0xFF374151);
  static const Color gray800 = Color(0xFF1F2937);
  static const Color gray900 = Color(0xFF111827);

  // ── Semantic ─────────────────────────────────────────────
  static const Color success = Color(0xFF10B981);
  static const Color warning = Color(0xFFF59E0B);
  static const Color error = Color(0xFFEF4444);
  static const Color info = Color(0xFF3B82F6);

  // ── Badge backgrounds ────────────────────────────────────
  static const Color badgeGreenBg = Color(0xFFECFDF5);
  static const Color badgeGreenFg = Color(0xFF047857);
  static const Color badgeYellowBg = Color(0xFFFFFBEB);
  static const Color badgeYellowFg = Color(0xFFB45309);
  static const Color badgeRedBg = Color(0xFFFEF2F2);
  static const Color badgeRedFg = Color(0xFFB91C1C);
  static const Color badgeBlueBg = Color(0xFFEFF6FF);
  static const Color badgeBlueFg = Color(0xFF1D4ED8);
}
