import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/router/app_router.dart';
import 'package:loadmovegh/core/storage/local_cache.dart';
import 'package:loadmovegh/core/theme/app_theme.dart';

/// LoadMoveGH — Ghana Freight Marketplace
///
/// Entry point. Initialises:
///   1. Hive (offline cache)
///   2. Firebase (push notifications)
///   3. Riverpod (state management)
///   4. GoRouter (navigation)

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Lock orientation to portrait
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // System UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      systemNavigationBarColor: Colors.white,
      systemNavigationBarIconBrightness: Brightness.dark,
    ),
  );

  // Initialise offline cache (Hive)
  await LocalCache.init();

  // TODO: Initialise Firebase when ready
  // await Firebase.initializeApp();

  runApp(
    const ProviderScope(
      child: LoadMoveGHApp(),
    ),
  );
}

class LoadMoveGHApp extends ConsumerWidget {
  const LoadMoveGHApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'LoadMoveGH',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      routerConfig: router,
    );
  }
}
