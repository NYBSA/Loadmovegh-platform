import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/features/loads/domain/entities/load_entity.dart';
import 'package:loadmovegh/features/loads/domain/repositories/load_repository.dart';

class GetLoadsUseCase {
  final LoadRepository repository;
  const GetLoadsUseCase(this.repository);

  Future<Either<Failure, List<LoadEntity>>> call({
    int page = 1,
    String? search,
    String? region,
    String? cargoType,
    String? vehicleType,
    String? urgency,
    double? nearLat,
    double? nearLng,
    double? radiusKm,
  }) {
    return repository.getLoads(
      page: page,
      search: search,
      region: region,
      cargoType: cargoType,
      vehicleType: vehicleType,
      urgency: urgency,
      nearLat: nearLat,
      nearLng: nearLng,
      radiusKm: radiusKm,
    );
  }
}

class GetLoadDetailUseCase {
  final LoadRepository repository;
  const GetLoadDetailUseCase(this.repository);

  Future<Either<Failure, LoadEntity>> call(String id) {
    return repository.getLoadById(id);
  }
}
