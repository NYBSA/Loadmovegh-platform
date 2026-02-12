/// Data-layer exceptions — caught by repositories and mapped to [Failure].

class ServerException implements Exception {
  final String message;
  final int? statusCode;
  const ServerException({this.message = 'Server error', this.statusCode});
}

class CacheException implements Exception {
  final String message;
  const CacheException({this.message = 'Cache error'});
}

class UnauthorizedException implements Exception {
  final String message;
  const UnauthorizedException({this.message = 'Unauthorized'});
}
