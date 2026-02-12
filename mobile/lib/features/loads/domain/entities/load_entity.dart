import 'package:equatable/equatable.dart';

/// Domain entity for a freight load listing.

class LoadEntity extends Equatable {
  final String id;
  final String shipperId;
  final String shipperName;
  final String title;
  final String description;
  final String cargoType;   // general | perishable | hazardous | fragile | bulk | liquid | livestock
  final String vehicleType; // pickup | van | flatbed | box_truck | trailer | refrigerated | tanker
  final double weightKg;
  final String urgency;     // standard | express | urgent | scheduled
  final String status;      // open | bidding | assigned | in_transit | delivered | cancelled

  // ── Origin ───────────────────────────────────────────────
  final String originCity;
  final String originRegion;
  final double originLat;
  final double originLng;

  // ── Destination ──────────────────────────────────────────
  final String destCity;
  final String destRegion;
  final double destLat;
  final double destLng;

  // ── Pricing ──────────────────────────────────────────────
  final double? budgetMin;
  final double? budgetMax;
  final double? aiPriceMin;
  final double? aiPriceMax;

  // ── Meta ─────────────────────────────────────────────────
  final double distanceKm;
  final int bidCount;
  final DateTime pickupDate;
  final DateTime? deliveryDeadline;
  final DateTime createdAt;

  const LoadEntity({
    required this.id,
    required this.shipperId,
    required this.shipperName,
    required this.title,
    this.description = '',
    required this.cargoType,
    required this.vehicleType,
    required this.weightKg,
    this.urgency = 'standard',
    this.status = 'open',
    required this.originCity,
    required this.originRegion,
    required this.originLat,
    required this.originLng,
    required this.destCity,
    required this.destRegion,
    required this.destLat,
    required this.destLng,
    this.budgetMin,
    this.budgetMax,
    this.aiPriceMin,
    this.aiPriceMax,
    required this.distanceKm,
    this.bidCount = 0,
    required this.pickupDate,
    this.deliveryDeadline,
    required this.createdAt,
  });

  String get route => '$originCity → $destCity';

  @override
  List<Object?> get props => [id];
}
