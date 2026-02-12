import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Encrypted key-value storage for JWT tokens and sensitive data.

final secureStorageProvider = Provider<SecureStorageService>(
  (_) => SecureStorageService(),
);

class SecureStorageService {
  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';
  static const _userIdKey = 'user_id';
  static const _roleKey = 'role';

  final FlutterSecureStorage _storage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  // ── Tokens ───────────────────────────────────────────────
  Future<String?> getAccessToken() => _storage.read(key: _accessTokenKey);
  Future<void> setAccessToken(String token) =>
      _storage.write(key: _accessTokenKey, value: token);

  Future<String?> getRefreshToken() => _storage.read(key: _refreshTokenKey);
  Future<void> setRefreshToken(String token) =>
      _storage.write(key: _refreshTokenKey, value: token);

  // ── User ─────────────────────────────────────────────────
  Future<String?> getUserId() => _storage.read(key: _userIdKey);
  Future<void> setUserId(String id) =>
      _storage.write(key: _userIdKey, value: id);

  Future<String?> getRole() => _storage.read(key: _roleKey);
  Future<void> setRole(String role) =>
      _storage.write(key: _roleKey, value: role);

  // ── Clear ────────────────────────────────────────────────
  Future<void> clearAll() => _storage.deleteAll();
}
