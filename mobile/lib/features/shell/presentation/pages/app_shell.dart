import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';

/// App shell with persistent bottom navigation bar.
///
/// Wraps all authenticated routes via GoRouter ShellRoute.

class AppShell extends StatelessWidget {
  final Widget child;
  const AppShell({super.key, required this.child});

  static const _tabs = [
    _Tab('/loads', Icons.inventory_2_outlined, Icons.inventory_2, 'Loads'),
    _Tab('/tracking', Icons.map_outlined, Icons.map, 'Tracking'),
    _Tab('/bids', Icons.gavel_outlined, Icons.gavel, 'Bids'),
    _Tab('/wallet', Icons.account_balance_wallet_outlined,
        Icons.account_balance_wallet, 'Wallet'),
    _Tab('/notifications', Icons.notifications_none_rounded,
        Icons.notifications, 'Alerts'),
  ];

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    final currentIndex = _tabs.indexWhere((t) => location.startsWith(t.path));

    return Scaffold(
      body: child,
      // ── AI Assistant FAB ──────────────────────────────────
      floatingActionButton: FloatingActionButton(
        heroTag: 'ai_assistant_fab',
        onPressed: () => context.push('/assistant'),
        backgroundColor: AppColors.brand600,
        elevation: 4,
        child: const Icon(Icons.auto_awesome, color: Colors.white, size: 22),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.06),
              blurRadius: 10,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: List.generate(_tabs.length, (index) {
                final tab = _tabs[index];
                final isActive = index == currentIndex;

                return _NavItem(
                  icon: isActive ? tab.activeIcon : tab.icon,
                  label: tab.label,
                  isActive: isActive,
                  onTap: () {
                    if (index != currentIndex) {
                      context.go(tab.path);
                    }
                  },
                  // Show unread badge on Alerts tab
                  badgeCount: index == 4 ? 2 : 0,
                );
              }),
            ),
          ),
        ),
      ),
    );
  }
}

class _Tab {
  final String path;
  final IconData icon;
  final IconData activeIcon;
  final String label;
  const _Tab(this.path, this.icon, this.activeIcon, this.label);
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isActive;
  final VoidCallback onTap;
  final int badgeCount;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.isActive,
    required this.onTap,
    this.badgeCount = 0,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: SizedBox(
        width: 64,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 4),
            Stack(
              clipBehavior: Clip.none,
              children: [
                AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                  decoration: BoxDecoration(
                    color: isActive ? AppColors.brand50 : Colors.transparent,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Icon(
                    icon,
                    size: 22,
                    color: isActive ? AppColors.brand600 : AppColors.gray400,
                  ),
                ),
                if (badgeCount > 0)
                  Positioned(
                    right: 6,
                    top: -2,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 5, vertical: 1),
                      decoration: BoxDecoration(
                        color: AppColors.error,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        '$badgeCount',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: isActive ? FontWeight.w600 : FontWeight.w500,
                color: isActive ? AppColors.brand600 : AppColors.gray400,
              ),
            ),
            const SizedBox(height: 4),
          ],
        ),
      ),
    );
  }
}
