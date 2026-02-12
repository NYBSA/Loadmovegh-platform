import 'package:equatable/equatable.dart';

/// Domain entity for an active freight trip / shipment.

class TripEntity extends Equatable {
  final String id;
  final String listingId;
  final String courierId;
  final String shipperId;
  final String status; // pickup_pending | in_transit | delivered | cancelled | disputed

  // ── Real-time position ───────────────────────────────────
  final double? currentLat;
  final double? currentLng;
  final DateTime? lastLocationUpdate;

  // ── Route ────────────────────────────────────────────────
  final double originLat;
  final double originLng;
  final String originCity;
  final double destLat;
  final double destLng;
  final String destCity;
  final double distanceKm;

  // ── Timeline ─────────────────────────────────────────────
  final DateTime? pickedUpAt;
  final DateTime? deliveredAt;
  final DateTime? estimatedArrival;

  // ── Proof of delivery ────────────────────────────────────
  final String? podImageUrl;
  final String? podSignature;

  final DateTime createdAt;

  const TripEntity({
    required this.id,
    required this.listingId,
    required this.courierId,
    required this.shipperId,
    this.status = 'pickup_pending',
    this.currentLat,
    this.currentLng,
    this.lastLocationUpdate,
    required this.originLat,
    required this.originLng,
    required this.originCity,
    required this.destLat,
    required this.destLng,
    required this.destCity,
    required this.distanceKm,
    this.pickedUpAt,
    this.deliveredAt,
    this.estimatedArrival,
    this.podImageUrl,
    this.podSignature,
    required this.createdAt,
  });

  String get route => '$originCity → $destCity';
  bool get isActive => status == 'in_transit' || status == 'pickup_pending';

  @override
  List<Object?> get props => [id];
}
