import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/utils/extensions.dart';

/// Notifications page with push/in-app notification list.

class NotificationsPage extends ConsumerWidget {
  const NotificationsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Mock notifications
    final notifications = [
      _NotifData(
        'New Bid Received',
        'KwameExpress placed a GHS 850 bid on "Accra → Kumasi Electronics"',
        'bid_received',
        false,
        DateTime.now().subtract(const Duration(minutes: 12)),
      ),
      _NotifData(
        'Bid Accepted!',
        'Your bid on "Tema → Takoradi Textiles" has been accepted. Prepare for pickup.',
        'bid_accepted',
        false,
        DateTime.now().subtract(const Duration(hours: 2)),
      ),
      _NotifData(
        'Shipment Delivered',
        'Trip #TRP-042 has been marked as delivered. Payment released.',
        'trip_update',
        true,
        DateTime.now().subtract(const Duration(days: 1)),
      ),
      _NotifData(
        'Deposit Successful',
        'GHS 500.00 deposited via MTN MoMo. New balance: GHS 3,450.00',
        'payment',
        true,
        DateTime.now().subtract(const Duration(days: 1)),
      ),
      _NotifData(
        'New Loads in Your Area',
        '5 new loads posted within 50 km of your location. Check the load board!',
        'system',
        true,
        DateTime.now().subtract(const Duration(days: 2)),
      ),
    ];

    final unread = notifications.where((n) => !n.isRead).length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          if (unread > 0)
            TextButton(
              onPressed: () {
                // Mark all as read
              },
              child: const Text('Mark all read'),
            ),
        ],
      ),
      body: notifications.isEmpty
          ? Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.notifications_none_rounded,
                      size: 56, color: AppColors.gray300),
                  const SizedBox(height: 12),
                  const Text(
                    'No notifications',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppColors.gray500,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'You\'re all caught up!',
                    style: TextStyle(color: AppColors.gray400, fontSize: 13),
                  ),
                ],
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.only(top: 8, bottom: 80),
              itemCount: notifications.length,
              separatorBuilder: (_, __) =>
                  const Divider(height: 1, indent: 72),
              itemBuilder: (context, index) {
                final notif = notifications[index];
                return _notifTile(context, notif);
              },
            ),
    );
  }

  Widget _notifTile(BuildContext context, _NotifData notif) {
    return Container(
      color: notif.isRead ? null : AppColors.brand50.withOpacity(0.5),
      child: ListTile(
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: _iconBgColor(notif.type),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(
            _notifIcon(notif.type),
            size: 20,
            color: _iconFgColor(notif.type),
          ),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                notif.title,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: notif.isRead ? FontWeight.w500 : FontWeight.w700,
                  color: AppColors.gray800,
                ),
              ),
            ),
            if (!notif.isRead)
              Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: AppColors.brand500,
                  shape: BoxShape.circle,
                ),
              ),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              notif.body,
              style: const TextStyle(
                fontSize: 13,
                color: AppColors.gray600,
                height: 1.4,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Text(
              notif.date.timeAgo,
              style: const TextStyle(fontSize: 11, color: AppColors.gray400),
            ),
          ],
        ),
        onTap: () {
          // Navigate to relevant page based on type
        },
      ),
    );
  }

  IconData _notifIcon(String type) {
    return switch (type) {
      'bid_received' => Icons.gavel_rounded,
      'bid_accepted' => Icons.check_circle_outline,
      'trip_update' => Icons.local_shipping_rounded,
      'payment' => Icons.payments_outlined,
      _ => Icons.campaign_outlined,
    };
  }

  Color _iconBgColor(String type) {
    return switch (type) {
      'bid_received' => AppColors.badgeBlueBg,
      'bid_accepted' => AppColors.badgeGreenBg,
      'trip_update' => AppColors.accent50,
      'payment' => AppColors.brand50,
      _ => AppColors.gray100,
    };
  }

  Color _iconFgColor(String type) {
    return switch (type) {
      'bid_received' => AppColors.badgeBlueFg,
      'bid_accepted' => AppColors.badgeGreenFg,
      'trip_update' => AppColors.accent600,
      'payment' => AppColors.brand700,
      _ => AppColors.gray600,
    };
  }
}

class _NotifData {
  final String title;
  final String body;
  final String type;
  final bool isRead;
  final DateTime date;
  _NotifData(this.title, this.body, this.type, this.isRead, this.date);
}
