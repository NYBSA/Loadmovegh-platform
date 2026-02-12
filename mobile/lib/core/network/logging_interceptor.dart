import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

/// Logs every HTTP request and response in debug builds.

class LoggingInterceptor extends Interceptor {
  final _log = Logger(
    printer: PrettyPrinter(methodCount: 0, printTime: true),
  );

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    _log.d('→ ${options.method} ${options.uri}');
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    _log.d('← ${response.statusCode} ${response.requestOptions.uri}');
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _log.e('✗ ${err.response?.statusCode ?? "?"} ${err.requestOptions.uri}',
        error: err.message);
    handler.next(err);
  }
}
