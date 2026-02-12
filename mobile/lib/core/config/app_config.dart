/// LoadMoveGH — Application Configuration
///
/// Central config sourced from environment / build flavors.
/// Matches the FastAPI backend at [baseUrl]/api/v1.

class AppConfig {
  const AppConfig._();

  // ── API ──────────────────────────────────────────────────
  static const String appName = 'LoadMoveGH';
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000', // Android emulator → host
  );
  static const String apiPrefix = '/api/v1';
  static String get apiUrl => '$baseUrl$apiPrefix';

  // ── Auth ─────────────────────────────────────────────────
  static const int accessTokenExpiryMinutes = 30;
  static const int refreshTokenExpiryDays = 7;
  static const int otpLength = 6;
  static const int otpExpiryMinutes = 10;

  // ── Maps ─────────────────────────────────────────────────
  static const String googleMapsApiKey = String.fromEnvironment(
    'GOOGLE_MAPS_API_KEY',
    defaultValue: '',
  );

  // ── Ghana Bounds (for map camera) ────────────────────────
  static const double ghLatMin = 4.5;
  static const double ghLatMax = 11.5;
  static const double ghLngMin = -3.5;
  static const double ghLngMax = 1.5;
  static const double ghCenterLat = 7.9465;
  static const double ghCenterLng = -1.0232;

  // ── Offline ──────────────────────────────────────────────
  static const Duration offlineCacheDuration = Duration(hours: 24);
  static const int maxCachedLoads = 200;

  // ── Platform Fees (display) ──────────────────────────────
  static const double commissionRate = 0.05;
  static const String currency = 'GHS';
}
