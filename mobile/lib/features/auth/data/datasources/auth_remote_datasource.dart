import 'package:dio/dio.dart';
import 'package:loadmovegh/core/error/exceptions.dart';
import 'package:loadmovegh/features/auth/data/models/user_model.dart';

/// Remote data source for authentication API calls.

class AuthRemoteDataSource {
  final Dio dio;
  const AuthRemoteDataSource({required this.dio});

  /// POST /auth/login
  Future<({UserModel user, String accessToken, String refreshToken})> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await dio.post('/auth/login', data: {
        'email': email,
        'password': password,
      });
      final data = response.data as Map<String, dynamic>;
      return (
        user: UserModel.fromJson(data['user'] as Map<String, dynamic>),
        accessToken: data['access_token'] as String,
        refreshToken: data['refresh_token'] as String,
      );
    } on DioException catch (e) {
      throw ServerException(
        message: _extractMessage(e),
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// POST /auth/otp/request
  Future<void> requestOtp({required String phone}) async {
    try {
      await dio.post('/auth/otp/request', data: {'phone': phone});
    } on DioException catch (e) {
      throw ServerException(message: _extractMessage(e));
    }
  }

  /// POST /auth/otp/verify
  Future<({UserModel user, String accessToken, String refreshToken})> verifyOtp({
    required String phone,
    required String code,
  }) async {
    try {
      final response = await dio.post('/auth/otp/verify', data: {
        'phone': phone,
        'code': code,
      });
      final data = response.data as Map<String, dynamic>;
      return (
        user: UserModel.fromJson(data['user'] as Map<String, dynamic>),
        accessToken: data['access_token'] as String,
        refreshToken: data['refresh_token'] as String,
      );
    } on DioException catch (e) {
      throw ServerException(message: _extractMessage(e));
    }
  }

  /// POST /auth/register
  Future<({UserModel user, String accessToken, String refreshToken})> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String role,
    String? phone,
    String? orgName,
  }) async {
    try {
      final response = await dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'first_name': firstName,
        'last_name': lastName,
        'role': role,
        if (phone != null) 'phone': phone,
        if (orgName != null) 'org_name': orgName,
      });
      final data = response.data as Map<String, dynamic>;
      return (
        user: UserModel.fromJson(data['user'] as Map<String, dynamic>),
        accessToken: data['access_token'] as String,
        refreshToken: data['refresh_token'] as String,
      );
    } on DioException catch (e) {
      throw ServerException(message: _extractMessage(e));
    }
  }

  /// POST /auth/forgot-password
  Future<void> forgotPassword({required String email}) async {
    try {
      await dio.post('/auth/forgot-password', data: {'email': email});
    } on DioException catch (e) {
      throw ServerException(message: _extractMessage(e));
    }
  }

  /// POST /auth/reset-password
  Future<void> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    try {
      await dio.post('/auth/reset-password', data: {
        'token': token,
        'new_password': newPassword,
      });
    } on DioException catch (e) {
      throw ServerException(message: _extractMessage(e));
    }
  }

  /// GET /auth/me
  Future<UserModel> getCurrentUser() async {
    try {
      final response = await dio.get('/auth/me');
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ServerException(message: _extractMessage(e));
    }
  }

  String _extractMessage(DioException e) {
    final data = e.response?.data;
    if (data is Map) return data['detail']?.toString() ?? 'Unknown error';
    return e.message ?? 'Network error';
  }
}
