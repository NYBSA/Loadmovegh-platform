import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/features/auth/domain/entities/user_entity.dart';

/// Auth repository contract — implemented in the data layer.

abstract class AuthRepository {
  /// Email + password login → tokens + user
  Future<Either<Failure, UserEntity>> login({
    required String email,
    required String password,
  });

  /// Ghana phone OTP request
  Future<Either<Failure, void>> requestOtp({required String phone});

  /// Verify OTP → tokens + user
  Future<Either<Failure, UserEntity>> verifyOtp({
    required String phone,
    required String code,
  });

  /// Register new account
  Future<Either<Failure, UserEntity>> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String role,
    String? phone,
    String? orgName,
  });

  /// Request password reset email
  Future<Either<Failure, void>> forgotPassword({required String email});

  /// Reset password with token
  Future<Either<Failure, void>> resetPassword({
    required String token,
    required String newPassword,
  });

  /// Refresh JWT tokens silently
  Future<Either<Failure, void>> refreshTokens();

  /// Get current authenticated user from token
  Future<Either<Failure, UserEntity>> getCurrentUser();

  /// Sign out — clear tokens
  Future<void> logout();
}
