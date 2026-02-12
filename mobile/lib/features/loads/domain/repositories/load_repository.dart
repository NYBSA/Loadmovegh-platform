import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/features/loads/domain/entities/load_entity.dart';

/// Load repository contract.

abstract class LoadRepository {
  /// Fetch paginated loads with optional filters.
  Future<Either<Failure, List<LoadEntity>>> getLoads({
    int page = 1,
    int limit = 20,
    String? search,
    String? region,
    String? cargoType,
    String? vehicleType,
    String? urgency,
    double? maxDistanceKm,
    double? minPrice,
    double? maxPrice,
    double? nearLat,
    double? nearLng,
    double? radiusKm,
  });

  /// Get single load by ID.
  Future<Either<Failure, LoadEntity>> getLoadById(String id);

  /// Post a new load (shipper).
  Future<Either<Failure, LoadEntity>> createLoad(LoadEntity load);

  /// Update load status.
  Future<Either<Failure, LoadEntity>> updateStatus(
      String id, String newStatus);
}
