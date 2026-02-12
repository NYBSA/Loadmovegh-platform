import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';

/// Checks network connectivity before requests.
/// Throws a typed [NoConnectionException] when offline,
/// which the data layer catches to serve cached data.

class ConnectivityInterceptor extends Interceptor {
  @override
  void onRequest(
      RequestOptions options, RequestInterceptorHandler handler) async {
    final result = await Connectivity().checkConnectivity();

    if (result.contains(ConnectivityResult.none)) {
      return handler.reject(
        DioException(
          requestOptions: options,
          type: DioExceptionType.connectionError,
          error: const NoConnectionException(),
        ),
      );
    }

    handler.next(options);
  }
}

class NoConnectionException implements Exception {
  const NoConnectionException();

  @override
  String toString() => 'No internet connection';
}
