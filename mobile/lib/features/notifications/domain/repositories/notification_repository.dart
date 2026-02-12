import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/features/notifications/domain/entities/notification_entity.dart';

/// Notification repository contract.

abstract class NotificationRepository {
  /// Get paginated notifications.
  Future<Either<Failure, List<NotificationEntity>>> getNotifications({
    int page = 1,
    int limit = 30,
  });

  /// Mark a notification as read.
  Future<Either<Failure, void>> markAsRead(String id);

  /// Mark all notifications as read.
  Future<Either<Failure, void>> markAllAsRead();

  /// Get unread count.
  Future<Either<Failure, int>> getUnreadCount();

  /// Register FCM token with the backend.
  Future<Either<Failure, void>> registerPushToken(String fcmToken);
}
