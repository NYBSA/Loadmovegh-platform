import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:logger/logger.dart';

/// Push notification service — Firebase Cloud Messaging + local notifications.
///
/// Handles:
///   - FCM token registration
///   - Foreground notification display
///   - Background/terminated message handling
///   - Deep link navigation on tap

class PushNotificationService {
  static final _log = Logger(printer: PrettyPrinter(methodCount: 0));

  static final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  static const _androidChannel = AndroidNotificationChannel(
    'loadmovegh_default',
    'LoadMoveGH Notifications',
    description: 'Default notification channel for LoadMoveGH',
    importance: Importance.high,
  );

  /// Call once in main() after Firebase.initializeApp().
  static Future<void> init() async {
    // Local notifications setup
    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestSoundPermission: true,
      requestBadgePermission: true,
      requestAlertPermission: true,
    );
    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    // Create Android notification channel
    await _localNotifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(_androidChannel);

    _log.i('Push notification service initialised');

    // TODO: Uncomment when Firebase is configured
    // final fcmToken = await FirebaseMessaging.instance.getToken();
    // _log.d('FCM Token: $fcmToken');
    //
    // FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    // FirebaseMessaging.onMessageOpenedApp.listen(_handleBackgroundMessage);
  }

  static void _onNotificationTapped(NotificationResponse response) {
    final payload = response.payload;
    if (payload != null) {
      _log.d('Notification tapped with payload: $payload');
      // TODO: Parse payload and navigate via GoRouter
    }
  }

  /// Display a local notification (used when a push arrives in foreground).
  static Future<void> showLocal({
    required String title,
    required String body,
    String? payload,
  }) async {
    await _localNotifications.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _androidChannel.id,
          _androidChannel.name,
          channelDescription: _androidChannel.description,
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
        iOS: const DarwinNotificationDetails(),
      ),
      payload: payload,
    );
  }
}
