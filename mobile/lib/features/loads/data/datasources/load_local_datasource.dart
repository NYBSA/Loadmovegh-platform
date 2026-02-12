import 'package:loadmovegh/core/storage/local_cache.dart';
import 'package:loadmovegh/features/loads/data/models/load_model.dart';

/// Local data source — Hive cache for offline load browsing.

class LoadLocalDataSource {
  /// Cache a list of loads.
  Future<void> cacheLoads(List<LoadModel> loads) async {
    for (final load in loads) {
      await LocalCache.put(
        LocalCache.loadsBox,
        load.id,
        (load as LoadModel).toJson(),
      );
    }
    // Also store the ordered ID list for the board.
    await LocalCache.put(
      LocalCache.loadsBox,
      '_id_list',
      {'ids': loads.map((l) => l.id).toList()},
    );
  }

  /// Retrieve cached loads.
  List<LoadModel> getCachedLoads() {
    final idListEntry = LocalCache.get(LocalCache.loadsBox, '_id_list');
    if (idListEntry == null) return [];

    final ids = (idListEntry['ids'] as List?)?.cast<String>() ?? [];
    return ids
        .map((id) {
          final data = LocalCache.get(LocalCache.loadsBox, id);
          return data != null ? LoadModel.fromJson(data) : null;
        })
        .whereType<LoadModel>()
        .toList();
  }

  /// Retrieve a single cached load.
  LoadModel? getCachedLoad(String id) {
    final data = LocalCache.get(LocalCache.loadsBox, id);
    return data != null ? LoadModel.fromJson(data) : null;
  }
}
