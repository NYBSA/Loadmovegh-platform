import 'package:loadmovegh/features/loads/domain/entities/load_entity.dart';

/// JSON-serializable load model.

class LoadModel extends LoadEntity {
  const LoadModel({
    required super.id,
    required super.shipperId,
    required super.shipperName,
    required super.title,
    super.description,
    required super.cargoType,
    required super.vehicleType,
    required super.weightKg,
    super.urgency,
    super.status,
    required super.originCity,
    required super.originRegion,
    required super.originLat,
    required super.originLng,
    required super.destCity,
    required super.destRegion,
    required super.destLat,
    required super.destLng,
    super.budgetMin,
    super.budgetMax,
    super.aiPriceMin,
    super.aiPriceMax,
    required super.distanceKm,
    super.bidCount,
    required super.pickupDate,
    super.deliveryDeadline,
    required super.createdAt,
  });

  factory LoadModel.fromJson(Map<String, dynamic> json) {
    final origin = json['origin'] as Map<String, dynamic>? ?? {};
    final dest = json['destination'] as Map<String, dynamic>? ?? {};

    return LoadModel(
      id: json['id'] as String,
      shipperId: json['shipper_id'] as String? ?? '',
      shipperName: json['shipper_name'] as String? ?? 'Unknown',
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      cargoType: json['cargo_type'] as String? ?? 'general',
      vehicleType: json['vehicle_type'] as String? ?? 'pickup',
      weightKg: (json['weight_kg'] as num?)?.toDouble() ?? 0,
      urgency: json['urgency'] as String? ?? 'standard',
      status: json['status'] as String? ?? 'open',
      originCity: origin['city'] as String? ?? json['origin_city'] as String? ?? '',
      originRegion: origin['region'] as String? ?? json['origin_region'] as String? ?? '',
      originLat: (origin['latitude'] as num?)?.toDouble() ?? (json['origin_lat'] as num?)?.toDouble() ?? 0,
      originLng: (origin['longitude'] as num?)?.toDouble() ?? (json['origin_lng'] as num?)?.toDouble() ?? 0,
      destCity: dest['city'] as String? ?? json['dest_city'] as String? ?? '',
      destRegion: dest['region'] as String? ?? json['dest_region'] as String? ?? '',
      destLat: (dest['latitude'] as num?)?.toDouble() ?? (json['dest_lat'] as num?)?.toDouble() ?? 0,
      destLng: (dest['longitude'] as num?)?.toDouble() ?? (json['dest_lng'] as num?)?.toDouble() ?? 0,
      budgetMin: (json['budget_min'] as num?)?.toDouble(),
      budgetMax: (json['budget_max'] as num?)?.toDouble(),
      aiPriceMin: (json['ai_price_min'] as num?)?.toDouble(),
      aiPriceMax: (json['ai_price_max'] as num?)?.toDouble(),
      distanceKm: (json['distance_km'] as num?)?.toDouble() ?? 0,
      bidCount: json['bid_count'] as int? ?? 0,
      pickupDate: DateTime.parse(json['pickup_date'] as String? ?? DateTime.now().toIso8601String()),
      deliveryDeadline: json['delivery_deadline'] != null
          ? DateTime.parse(json['delivery_deadline'] as String)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String? ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'shipper_id': shipperId,
        'title': title,
        'description': description,
        'cargo_type': cargoType,
        'vehicle_type': vehicleType,
        'weight_kg': weightKg,
        'urgency': urgency,
        'status': status,
        'origin_city': originCity,
        'origin_region': originRegion,
        'origin_lat': originLat,
        'origin_lng': originLng,
        'dest_city': destCity,
        'dest_region': destRegion,
        'dest_lat': destLat,
        'dest_lng': destLng,
        'budget_min': budgetMin,
        'budget_max': budgetMax,
        'distance_km': distanceKm,
        'pickup_date': pickupDate.toIso8601String(),
        'delivery_deadline': deliveryDeadline?.toIso8601String(),
        'created_at': createdAt.toIso8601String(),
      };
}
