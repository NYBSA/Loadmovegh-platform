import 'package:equatable/equatable.dart';

/// Domain entity for a freight bid.

class BidEntity extends Equatable {
  final String id;
  final String listingId;
  final String courierId;
  final String courierName;
  final double amount;
  final String currency;
  final String? note;
  final String status; // pending | accepted | rejected | withdrawn
  final double? aiRecommendedMin;
  final double? aiRecommendedMax;
  final DateTime estimatedPickup;
  final DateTime estimatedDelivery;
  final DateTime createdAt;

  const BidEntity({
    required this.id,
    required this.listingId,
    required this.courierId,
    required this.courierName,
    required this.amount,
    this.currency = 'GHS',
    this.note,
    this.status = 'pending',
    this.aiRecommendedMin,
    this.aiRecommendedMax,
    required this.estimatedPickup,
    required this.estimatedDelivery,
    required this.createdAt,
  });

  @override
  List<Object?> get props => [id];
}
