import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/exceptions.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/core/network/connectivity_interceptor.dart';
import 'package:loadmovegh/core/storage/secure_storage.dart';
import 'package:loadmovegh/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:loadmovegh/features/auth/domain/entities/user_entity.dart';
import 'package:loadmovegh/features/auth/domain/repositories/auth_repository.dart';

/// Concrete implementation of [AuthRepository].

class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource remoteDataSource;
  final SecureStorageService secureStorage;

  const AuthRepositoryImpl({
    required this.remoteDataSource,
    required this.secureStorage,
  });

  @override
  Future<Either<Failure, UserEntity>> login({
    required String email,
    required String password,
  }) async {
    try {
      final result =
          await remoteDataSource.login(email: email, password: password);
      await _persistTokens(result.accessToken, result.refreshToken, result.user);
      return Right(result.user);
    } on ServerException catch (e) {
      return Left(AuthFailure(message: e.message));
    } on NoConnectionException {
      return const Left(NetworkFailure());
    }
  }

  @override
  Future<Either<Failure, void>> requestOtp({required String phone}) async {
    try {
      await remoteDataSource.requestOtp(phone: phone);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, UserEntity>> verifyOtp({
    required String phone,
    required String code,
  }) async {
    try {
      final result =
          await remoteDataSource.verifyOtp(phone: phone, code: code);
      await _persistTokens(result.accessToken, result.refreshToken, result.user);
      return Right(result.user);
    } on ServerException catch (e) {
      return Left(AuthFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, UserEntity>> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String role,
    String? phone,
    String? orgName,
  }) async {
    try {
      final result = await remoteDataSource.register(
        email: email,
        password: password,
        firstName: firstName,
        lastName: lastName,
        role: role,
        phone: phone,
        orgName: orgName,
      );
      await _persistTokens(result.accessToken, result.refreshToken, result.user);
      return Right(result.user);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, void>> forgotPassword({required String email}) async {
    try {
      await remoteDataSource.forgotPassword(email: email);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, void>> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    try {
      await remoteDataSource.resetPassword(
          token: token, newPassword: newPassword);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, void>> refreshTokens() async {
    // Handled automatically by AuthInterceptor
    return const Right(null);
  }

  @override
  Future<Either<Failure, UserEntity>> getCurrentUser() async {
    try {
      final user = await remoteDataSource.getCurrentUser();
      return Right(user);
    } on ServerException catch (e) {
      return Left(AuthFailure(message: e.message));
    }
  }

  @override
  Future<void> logout() async {
    await secureStorage.clearAll();
  }

  Future<void> _persistTokens(
      String access, String refresh, UserEntity user) async {
    await Future.wait([
      secureStorage.setAccessToken(access),
      secureStorage.setRefreshToken(refresh),
      secureStorage.setUserId(user.id),
      secureStorage.setRole(user.role),
    ]);
  }
}
