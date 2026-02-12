import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import 'package:loadmovegh/core/storage/local_cache.dart';

/// Offline-to-online sync service.
///
/// When the device regains connectivity, this service:
///   1. Drains all pending actions from the Hive queue
///   2. Replays them against the API in FIFO order
///   3. Logs failures for retry on next sync cycle
///
/// Start listening in main() or at app shell level.

class OfflineSyncService {
  final Dio dio;
  final _log = Logger(printer: PrettyPrinter(methodCount: 0));
  bool _isSyncing = false;

  OfflineSyncService({required this.dio});

  /// Begin listening for connectivity changes.
  void startListening() {
    Connectivity().onConnectivityChanged.listen((result) {
      if (!result.contains(ConnectivityResult.none)) {
        syncPendingActions();
      }
    });
  }

  /// Drain and replay all queued actions.
  Future<void> syncPendingActions() async {
    if (_isSyncing) return;
    _isSyncing = true;

    try {
      final actions = LocalCache.drainPendingActions();
      if (actions.isEmpty) return;

      _log.i('Syncing ${actions.length} pending offline actions…');

      for (final action in actions) {
        try {
          final method = action['method'] as String? ?? 'POST';
          final path = action['path'] as String? ?? '';
          final data = action['data'] as Map<String, dynamic>?;

          await dio.request(
            path,
            data: data,
            options: Options(method: method),
          );

          _log.d('✓ Synced: $method $path');
        } catch (e) {
          _log.e('✗ Sync failed: ${action['path']}', error: e);
          // Re-queue for next sync cycle
          await LocalCache.queuePendingAction(action);
        }
      }
    } finally {
      _isSyncing = false;
    }
  }

  /// Enqueue an action for later sync.
  ///
  /// Call this when a write operation fails due to no connectivity.
  static Future<void> enqueue({
    required String method,
    required String path,
    Map<String, dynamic>? data,
  }) async {
    await LocalCache.queuePendingAction({
      'method': method,
      'path': path,
      'data': data,
      'queued_at': DateTime.now().toIso8601String(),
    });
  }
}
