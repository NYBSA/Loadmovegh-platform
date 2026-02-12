import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/utils/extensions.dart';
import 'package:loadmovegh/core/widgets/empty_state.dart';
import 'package:loadmovegh/core/widgets/offline_banner.dart';
import 'package:loadmovegh/features/loads/domain/entities/load_entity.dart';
import 'package:loadmovegh/features/loads/presentation/providers/load_provider.dart';
import 'package:loadmovegh/features/loads/presentation/widgets/load_card.dart';
import 'package:loadmovegh/features/loads/presentation/widgets/load_filters.dart';

class LoadBoardPage extends ConsumerWidget {
  const LoadBoardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(loadBoardProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Load Board'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list_rounded),
            onPressed: () => _showFilters(context, ref),
          ),
          IconButton(
            icon: const Icon(Icons.my_location_rounded),
            onPressed: () {
              // TODO: Set near-me filter using device GPS
            },
          ),
        ],
      ),
      body: Column(
        children: [
          const OfflineBanner(),

          // ── Search bar ──────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Search loads by route, cargo...',
                prefixIcon: const Icon(Icons.search, size: 20),
                suffixIcon: state.searchQuery != null
                    ? IconButton(
                        icon: const Icon(Icons.close, size: 18),
                        onPressed: () =>
                            ref.read(loadBoardProvider.notifier).clearFilters(),
                      )
                    : null,
                isDense: true,
              ),
              onSubmitted: (value) {
                ref
                    .read(loadBoardProvider.notifier)
                    .applyFilters(search: value);
              },
            ),
          ),

          // ── Active filter chips ─────────────────────
          if (_hasActiveFilters(state))
            SizedBox(
              height: 36,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                children: [
                  if (state.regionFilter != null)
                    _filterChip(state.regionFilter!, ref),
                  if (state.cargoTypeFilter != null)
                    _filterChip(state.cargoTypeFilter!, ref),
                  if (state.vehicleTypeFilter != null)
                    _filterChip(state.vehicleTypeFilter!, ref),
                  if (state.urgencyFilter != null)
                    _filterChip(state.urgencyFilter!, ref),
                ],
              ),
            ),

          // ── Load list ───────────────────────────────
          Expanded(
            child: _buildContent(context, ref, state),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(
      BuildContext context, WidgetRef ref, LoadBoardState state) {
    if (state.isLoading && state.loads.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null && state.loads.isEmpty) {
      return EmptyState(
        icon: Icons.error_outline,
        title: 'Something went wrong',
        subtitle: state.error!,
        actionLabel: 'Retry',
        onAction: () =>
            ref.read(loadBoardProvider.notifier).fetchLoads(refresh: true),
      );
    }

    if (state.loads.isEmpty) {
      return EmptyState(
        icon: Icons.inventory_2_outlined,
        title: 'No loads available',
        subtitle: 'Pull down to refresh or adjust your filters.',
        actionLabel: 'Refresh',
        onAction: () =>
            ref.read(loadBoardProvider.notifier).fetchLoads(refresh: true),
      );
    }

    return RefreshIndicator(
      onRefresh: () =>
          ref.read(loadBoardProvider.notifier).fetchLoads(refresh: true),
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 80),
        itemCount: state.loads.length + (state.hasMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == state.loads.length) {
            // Load more trigger
            ref.read(loadBoardProvider.notifier).fetchLoads();
            return const Padding(
              padding: EdgeInsets.all(16),
              child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
            );
          }

          final load = state.loads[index];
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: LoadCard(
              load: load,
              onTap: () => context.pushNamed('load-detail',
                  pathParameters: {'id': load.id}),
            ),
          );
        },
      ),
    );
  }

  Widget _filterChip(String label, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: Chip(
        label: Text(label),
        deleteIcon: const Icon(Icons.close, size: 14),
        onDeleted: () =>
            ref.read(loadBoardProvider.notifier).clearFilters(),
        backgroundColor: AppColors.brand50,
        side: const BorderSide(color: AppColors.brand200),
        labelStyle: const TextStyle(
          fontSize: 12,
          color: AppColors.brand700,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  bool _hasActiveFilters(LoadBoardState state) =>
      state.regionFilter != null ||
      state.cargoTypeFilter != null ||
      state.vehicleTypeFilter != null ||
      state.urgencyFilter != null;

  void _showFilters(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => LoadFilters(
        onApply: (filters) {
          ref.read(loadBoardProvider.notifier).applyFilters(
                region: filters['region'],
                cargoType: filters['cargo_type'],
                vehicleType: filters['vehicle_type'],
                urgency: filters['urgency'],
              );
          Navigator.pop(context);
        },
      ),
    );
  }
}
