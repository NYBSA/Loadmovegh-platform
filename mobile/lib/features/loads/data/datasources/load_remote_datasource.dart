import 'package:dio/dio.dart';
import 'package:loadmovegh/core/error/exceptions.dart';
import 'package:loadmovegh/features/loads/data/models/load_model.dart';

/// Remote data source for freight load API calls.

class LoadRemoteDataSource {
  final Dio dio;
  const LoadRemoteDataSource({required this.dio});

  /// GET /listings
  Future<List<LoadModel>> getLoads({
    int page = 1,
    int limit = 20,
    Map<String, dynamic>? filters,
  }) async {
    try {
      final response = await dio.get('/listings', queryParameters: {
        'page': page,
        'limit': limit,
        ...?filters,
      });

      final items = response.data['items'] as List? ?? response.data as List? ?? [];
      return items
          .map((e) => LoadModel.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ServerException(
        message: e.response?.data?['detail']?.toString() ?? 'Failed to fetch loads',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// GET /listings/:id
  Future<LoadModel> getLoadById(String id) async {
    try {
      final response = await dio.get('/listings/$id');
      return LoadModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ServerException(
        message: e.response?.data?['detail']?.toString() ?? 'Load not found',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// POST /listings
  Future<LoadModel> createLoad(Map<String, dynamic> data) async {
    try {
      final response = await dio.post('/listings', data: data);
      return LoadModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ServerException(
        message: e.response?.data?['detail']?.toString() ?? 'Failed to create load',
      );
    }
  }

  /// PATCH /listings/:id/status
  Future<LoadModel> updateStatus(String id, String newStatus) async {
    try {
      final response =
          await dio.patch('/listings/$id/status', data: {'status': newStatus});
      return LoadModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ServerException(
        message: e.response?.data?['detail']?.toString() ?? 'Failed to update status',
      );
    }
  }
}
