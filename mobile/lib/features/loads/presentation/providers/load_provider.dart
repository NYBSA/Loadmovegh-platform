import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/network/api_client.dart';
import 'package:loadmovegh/features/loads/data/datasources/load_local_datasource.dart';
import 'package:loadmovegh/features/loads/data/datasources/load_remote_datasource.dart';
import 'package:loadmovegh/features/loads/data/repositories/load_repository_impl.dart';
import 'package:loadmovegh/features/loads/domain/entities/load_entity.dart';
import 'package:loadmovegh/features/loads/domain/repositories/load_repository.dart';

// ── Repository ─────────────────────────────────────────────

final loadRepositoryProvider = Provider<LoadRepository>((ref) {
  return LoadRepositoryImpl(
    remoteDataSource: LoadRemoteDataSource(dio: ref.read(apiClientProvider)),
    localDataSource: LoadLocalDataSource(),
  );
});

// ── Loads State ────────────────────────────────────────────

class LoadBoardState {
  final List<LoadEntity> loads;
  final bool isLoading;
  final bool isOffline;
  final String? error;
  final int currentPage;
  final bool hasMore;

  // Active filters
  final String? searchQuery;
  final String? regionFilter;
  final String? cargoTypeFilter;
  final String? vehicleTypeFilter;
  final String? urgencyFilter;

  const LoadBoardState({
    this.loads = const [],
    this.isLoading = false,
    this.isOffline = false,
    this.error,
    this.currentPage = 1,
    this.hasMore = true,
    this.searchQuery,
    this.regionFilter,
    this.cargoTypeFilter,
    this.vehicleTypeFilter,
    this.urgencyFilter,
  });

  LoadBoardState copyWith({
    List<LoadEntity>? loads,
    bool? isLoading,
    bool? isOffline,
    String? error,
    int? currentPage,
    bool? hasMore,
    String? searchQuery,
    String? regionFilter,
    String? cargoTypeFilter,
    String? vehicleTypeFilter,
    String? urgencyFilter,
  }) =>
      LoadBoardState(
        loads: loads ?? this.loads,
        isLoading: isLoading ?? this.isLoading,
        isOffline: isOffline ?? this.isOffline,
        error: error,
        currentPage: currentPage ?? this.currentPage,
        hasMore: hasMore ?? this.hasMore,
        searchQuery: searchQuery ?? this.searchQuery,
        regionFilter: regionFilter ?? this.regionFilter,
        cargoTypeFilter: cargoTypeFilter ?? this.cargoTypeFilter,
        vehicleTypeFilter: vehicleTypeFilter ?? this.vehicleTypeFilter,
        urgencyFilter: urgencyFilter ?? this.urgencyFilter,
      );
}

// ── Notifier ───────────────────────────────────────────────

class LoadBoardNotifier extends StateNotifier<LoadBoardState> {
  final LoadRepository _repository;

  LoadBoardNotifier(this._repository) : super(const LoadBoardState()) {
    fetchLoads();
  }

  Future<void> fetchLoads({bool refresh = false}) async {
    if (state.isLoading) return;

    final page = refresh ? 1 : state.currentPage;
    state = state.copyWith(isLoading: true, error: null);

    final result = await _repository.getLoads(
      page: page,
      search: state.searchQuery,
      region: state.regionFilter,
      cargoType: state.cargoTypeFilter,
      vehicleType: state.vehicleTypeFilter,
      urgency: state.urgencyFilter,
    );

    result.fold(
      (failure) => state = state.copyWith(
        isLoading: false,
        error: failure.message,
        isOffline: failure.message.contains('internet'),
      ),
      (loads) => state = state.copyWith(
        loads: refresh ? loads : [...state.loads, ...loads],
        isLoading: false,
        isOffline: false,
        currentPage: page + 1,
        hasMore: loads.length >= 20,
      ),
    );
  }

  void applyFilters({
    String? search,
    String? region,
    String? cargoType,
    String? vehicleType,
    String? urgency,
  }) {
    state = state.copyWith(
      searchQuery: search,
      regionFilter: region,
      cargoTypeFilter: cargoType,
      vehicleTypeFilter: vehicleType,
      urgencyFilter: urgency,
      currentPage: 1,
      loads: [],
    );
    fetchLoads(refresh: true);
  }

  void clearFilters() {
    state = const LoadBoardState();
    fetchLoads(refresh: true);
  }
}

final loadBoardProvider =
    StateNotifierProvider<LoadBoardNotifier, LoadBoardState>((ref) {
  return LoadBoardNotifier(ref.read(loadRepositoryProvider));
});
