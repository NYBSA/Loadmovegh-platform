import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:loadmovegh/core/network/api_client.dart';
import 'package:loadmovegh/core/storage/secure_storage.dart';
import 'package:loadmovegh/features/auth/data/datasources/auth_remote_datasource.dart';
import 'package:loadmovegh/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:loadmovegh/features/auth/domain/entities/user_entity.dart';
import 'package:loadmovegh/features/auth/domain/repositories/auth_repository.dart';

// ── Repository ─────────────────────────────────────────────

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepositoryImpl(
    remoteDataSource: AuthRemoteDataSource(dio: ref.read(apiClientProvider)),
    secureStorage: ref.read(secureStorageProvider),
  );
});

// ── Auth State ─────────────────────────────────────────────

class AuthState {
  final UserEntity? user;
  final bool isLoading;
  final String? error;

  const AuthState({this.user, this.isLoading = false, this.error});

  bool get isAuthenticated => user != null;

  AuthState copyWith({UserEntity? user, bool? isLoading, String? error}) =>
      AuthState(
        user: user ?? this.user,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

// ── Auth Notifier ──────────────────────────────────────────

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;

  AuthNotifier(this._repository) : super(const AuthState());

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await _repository.login(email: email, password: password);
    result.fold(
      (failure) => state = state.copyWith(isLoading: false, error: failure.message),
      (user) => state = AuthState(user: user),
    );
  }

  Future<void> requestOtp(String phone) async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await _repository.requestOtp(phone: phone);
    result.fold(
      (failure) => state = state.copyWith(isLoading: false, error: failure.message),
      (_) => state = state.copyWith(isLoading: false),
    );
  }

  Future<void> verifyOtp(String phone, String code) async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await _repository.verifyOtp(phone: phone, code: code);
    result.fold(
      (failure) => state = state.copyWith(isLoading: false, error: failure.message),
      (user) => state = AuthState(user: user),
    );
  }

  Future<void> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String role,
    String? phone,
    String? orgName,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await _repository.register(
      email: email,
      password: password,
      firstName: firstName,
      lastName: lastName,
      role: role,
      phone: phone,
      orgName: orgName,
    );
    result.fold(
      (failure) => state = state.copyWith(isLoading: false, error: failure.message),
      (user) => state = AuthState(user: user),
    );
  }

  Future<void> checkAuth() async {
    final result = await _repository.getCurrentUser();
    result.fold(
      (_) => state = const AuthState(),
      (user) => state = AuthState(user: user),
    );
  }

  Future<void> logout() async {
    await _repository.logout();
    state = const AuthState();
  }
}

final authStateProvider =
    StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.read(authRepositoryProvider));
});
