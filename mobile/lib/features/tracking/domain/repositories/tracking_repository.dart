import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/features/tracking/domain/entities/trip_entity.dart';

/// Tracking repository contract.

abstract class TrackingRepository {
  /// Get active trips for the current user.
  Future<Either<Failure, List<TripEntity>>> getActiveTrips();

  /// Get trip by ID.
  Future<Either<Failure, TripEntity>> getTripById(String id);

  /// Update trip status (courier).
  Future<Either<Failure, TripEntity>> updateTripStatus(
      String tripId, String newStatus);

  /// Push GPS location update (courier).
  Future<Either<Failure, void>> sendLocationUpdate({
    required String tripId,
    required double latitude,
    required double longitude,
  });

  /// Submit proof of delivery (courier).
  Future<Either<Failure, TripEntity>> submitProofOfDelivery({
    required String tripId,
    String? imageUrl,
    String? signature,
  });
}
