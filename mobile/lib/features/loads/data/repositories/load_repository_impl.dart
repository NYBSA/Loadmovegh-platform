import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/exceptions.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/core/network/connectivity_interceptor.dart';
import 'package:loadmovegh/features/loads/data/datasources/load_local_datasource.dart';
import 'package:loadmovegh/features/loads/data/datasources/load_remote_datasource.dart';
import 'package:loadmovegh/features/loads/domain/entities/load_entity.dart';
import 'package:loadmovegh/features/loads/domain/repositories/load_repository.dart';

/// Concrete implementation with offline-first strategy:
///   1. Try remote
///   2. Cache results
///   3. On failure → serve from cache

class LoadRepositoryImpl implements LoadRepository {
  final LoadRemoteDataSource remoteDataSource;
  final LoadLocalDataSource localDataSource;

  const LoadRepositoryImpl({
    required this.remoteDataSource,
    required this.localDataSource,
  });

  @override
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
  }) async {
    try {
      final filters = <String, dynamic>{
        if (search != null) 'search': search,
        if (region != null) 'region': region,
        if (cargoType != null) 'cargo_type': cargoType,
        if (vehicleType != null) 'vehicle_type': vehicleType,
        if (urgency != null) 'urgency': urgency,
        if (nearLat != null) 'near_lat': nearLat,
        if (nearLng != null) 'near_lng': nearLng,
        if (radiusKm != null) 'radius_km': radiusKm,
      };

      final loads = await remoteDataSource.getLoads(
        page: page,
        limit: limit,
        filters: filters,
      );

      // Cache for offline use
      await localDataSource.cacheLoads(loads);
      return Right(loads);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    } on NoConnectionException {
      // Serve cached data when offline
      final cached = localDataSource.getCachedLoads();
      if (cached.isNotEmpty) return Right(cached);
      return const Left(NetworkFailure());
    }
  }

  @override
  Future<Either<Failure, LoadEntity>> getLoadById(String id) async {
    try {
      final load = await remoteDataSource.getLoadById(id);
      return Right(load);
    } on ServerException catch (e) {
      // Fallback to cache
      final cached = localDataSource.getCachedLoad(id);
      if (cached != null) return Right(cached);
      return Left(ServerFailure(message: e.message));
    } on NoConnectionException {
      final cached = localDataSource.getCachedLoad(id);
      if (cached != null) return Right(cached);
      return const Left(NetworkFailure());
    }
  }

  @override
  Future<Either<Failure, LoadEntity>> createLoad(LoadEntity load) async {
    try {
      final model = await remoteDataSource.createLoad({
        'title': load.title,
        'description': load.description,
        'cargo_type': load.cargoType,
        'vehicle_type': load.vehicleType,
        'weight_kg': load.weightKg,
        'urgency': load.urgency,
        'origin_city': load.originCity,
        'origin_region': load.originRegion,
        'origin_lat': load.originLat,
        'origin_lng': load.originLng,
        'dest_city': load.destCity,
        'dest_region': load.destRegion,
        'dest_lat': load.destLat,
        'dest_lng': load.destLng,
        'budget_min': load.budgetMin,
        'budget_max': load.budgetMax,
        'pickup_date': load.pickupDate.toIso8601String(),
        'delivery_deadline': load.deliveryDeadline?.toIso8601String(),
      });
      return Right(model);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, LoadEntity>> updateStatus(
      String id, String newStatus) async {
    try {
      final model = await remoteDataSource.updateStatus(id, newStatus);
      return Right(model);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }
}
