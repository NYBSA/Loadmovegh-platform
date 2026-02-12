import 'package:hive_flutter/hive_flutter.dart';
import 'package:loadmovegh/core/config/app_config.dart';

/// Hive-based offline cache for loads, bids, wallet state, and notifications.
///
/// Each feature has its own box. Stale entries are pruned by [maxAge].

class LocalCache {
  static const String _loadsBox = 'loads_cache';
  static const String _bidsBox = 'bids_cache';
  static const String _walletBox = 'wallet_cache';
  static const String _notificationsBox = 'notifications_cache';
  static const String _pendingActionsBox = 'pending_actions';

  /// Call once in main() before runApp.
  static Future<void> init() async {
    await Hive.initFlutter();
    await Future.wait([
      Hive.openBox<Map>(_loadsBox),
      Hive.openBox<Map>(_bidsBox),
      Hive.openBox<Map>(_walletBox),
      Hive.openBox<Map>(_notificationsBox),
      Hive.openBox<Map>(_pendingActionsBox),
    ]);
  }

  // ── Generic accessors ────────────────────────────────────
  static Box<Map> get loadsBox => Hive.box<Map>(_loadsBox);
  static Box<Map> get bidsBox => Hive.box<Map>(_bidsBox);
  static Box<Map> get walletBox => Hive.box<Map>(_walletBox);
  static Box<Map> get notificationsBox => Hive.box<Map>(_notificationsBox);
  static Box<Map> get pendingActionsBox => Hive.box<Map>(_pendingActionsBox);

  /// Store a value with a timestamp for expiry checking.
  static Future<void> put(Box<Map> box, String key, Map<String, dynamic> data) async {
    await box.put(key, {
      'data': data,
      'cached_at': DateTime.now().toIso8601String(),
    });
  }

  /// Retrieve a value if it has not expired.
  static Map<String, dynamic>? get(Box<Map> box, String key) {
    final entry = box.get(key);
    if (entry == null) return null;

    final cachedAt = DateTime.tryParse(entry['cached_at']?.toString() ?? '');
    if (cachedAt == null) return null;

    if (DateTime.now().difference(cachedAt) > AppConfig.offlineCacheDuration) {
      box.delete(key); // stale
      return null;
    }

    final data = entry['data'];
    if (data is Map) return Map<String, dynamic>.from(data);
    return null;
  }

  /// Queue an action to sync when connectivity returns.
  static Future<void> queuePendingAction(Map<String, dynamic> action) async {
    final id = DateTime.now().millisecondsSinceEpoch.toString();
    await pendingActionsBox.put(id, action);
  }

  /// Return and clear all pending actions (FIFO).
  static List<Map<String, dynamic>> drainPendingActions() {
    final actions = pendingActionsBox.values
        .map((e) => Map<String, dynamic>.from(e))
        .toList();
    pendingActionsBox.clear();
    return actions;
  }
}
