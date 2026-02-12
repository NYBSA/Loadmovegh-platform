import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/config/app_config.dart';
import 'package:loadmovegh/core/network/auth_interceptor.dart';
import 'package:loadmovegh/core/network/connectivity_interceptor.dart';
import 'package:loadmovegh/core/network/logging_interceptor.dart';

/// Singleton Dio HTTP client configured for the LoadMoveGH API.
///
/// Interceptors handle:
///   1. JWT token injection + refresh
///   2. Connectivity check (offline → cache fallback)
///   3. Request/response logging in debug mode

final apiClientProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: AppConfig.apiUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ),
  );

  dio.interceptors.addAll([
    AuthInterceptor(dio: dio, ref: ref),
    ConnectivityInterceptor(),
    LoggingInterceptor(),
  ]);

  return dio;
});
