import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/storage/secure_storage.dart';

/// Injects JWT access token into every request.
/// On 401 → refreshes token, retries once.

class AuthInterceptor extends Interceptor {
  final Dio dio;
  final Ref ref;
  bool _isRefreshing = false;

  AuthInterceptor({required this.dio, required this.ref});

  @override
  void onRequest(
      RequestOptions options, RequestInterceptorHandler handler) async {
    final storage = ref.read(secureStorageProvider);
    final token = await storage.getAccessToken();

    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode != 401 || _isRefreshing) {
      return handler.next(err);
    }

    _isRefreshing = true;

    try {
      final storage = ref.read(secureStorageProvider);
      final refreshToken = await storage.getRefreshToken();

      if (refreshToken == null) {
        await storage.clearAll();
        return handler.next(err);
      }

      final response = await Dio().post(
        '${dio.options.baseUrl}/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

      final newAccess = response.data['access_token'] as String;
      final newRefresh = response.data['refresh_token'] as String;

      await storage.setAccessToken(newAccess);
      await storage.setRefreshToken(newRefresh);

      // Retry the original request with new token
      final retryOptions = err.requestOptions;
      retryOptions.headers['Authorization'] = 'Bearer $newAccess';

      final retryResponse = await dio.fetch(retryOptions);
      return handler.resolve(retryResponse);
    } catch (_) {
      final storage = ref.read(secureStorageProvider);
      await storage.clearAll();
      return handler.next(err);
    } finally {
      _isRefreshing = false;
    }
  }
}
