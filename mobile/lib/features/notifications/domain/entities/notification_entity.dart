import 'package:equatable/equatable.dart';

/// Domain entity for an in-app notification.

class NotificationEntity extends Equatable {
  final String id;
  final String title;
  final String body;
  final String type; // bid_received | bid_accepted | trip_update | payment | system
  final String? referenceId; // load / bid / trip id
  final bool isRead;
  final DateTime createdAt;

  const NotificationEntity({
    required this.id,
    required this.title,
    required this.body,
    required this.type,
    this.referenceId,
    this.isRead = false,
    required this.createdAt,
  });

  @override
  List<Object?> get props => [id];
}
