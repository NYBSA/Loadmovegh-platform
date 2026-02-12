import 'package:equatable/equatable.dart';

/// Base failure class following clean-architecture error handling.
/// All domain-layer errors are typed Failures — never raw exceptions.

abstract class Failure extends Equatable {
  final String message;
  final int? statusCode;

  const Failure({required this.message, this.statusCode});

  @override
  List<Object?> get props => [message, statusCode];
}

// ── Concrete failures ──────────────────────────────────────

class ServerFailure extends Failure {
  const ServerFailure({super.message = 'Server error', super.statusCode});
}

class NetworkFailure extends Failure {
  const NetworkFailure({super.message = 'No internet connection'});
}

class CacheFailure extends Failure {
  const CacheFailure({super.message = 'Cache read/write error'});
}

class AuthFailure extends Failure {
  const AuthFailure({super.message = 'Authentication failed'});
}

class ValidationFailure extends Failure {
  final Map<String, List<String>> fieldErrors;

  const ValidationFailure({
    super.message = 'Validation error',
    this.fieldErrors = const {},
  });

  @override
  List<Object?> get props => [message, fieldErrors];
}

class PermissionFailure extends Failure {
  const PermissionFailure({super.message = 'Permission denied'});
}

class NotFoundFailure extends Failure {
  const NotFoundFailure({super.message = 'Resource not found', super.statusCode = 404});
}
