import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:loadmovegh/features/auth/presentation/pages/login_page.dart';
import 'package:loadmovegh/features/auth/presentation/pages/register_page.dart';
import 'package:loadmovegh/features/auth/presentation/pages/otp_page.dart';
import 'package:loadmovegh/features/auth/presentation/providers/auth_provider.dart';
import 'package:loadmovegh/features/loads/presentation/pages/load_board_page.dart';
import 'package:loadmovegh/features/loads/presentation/pages/load_detail_page.dart';
import 'package:loadmovegh/features/tracking/presentation/pages/tracking_page.dart';
import 'package:loadmovegh/features/bids/presentation/pages/bid_page.dart';
import 'package:loadmovegh/features/wallet/presentation/pages/wallet_page.dart';
import 'package:loadmovegh/features/notifications/presentation/pages/notifications_page.dart';
import 'package:loadmovegh/features/assistant/presentation/pages/assistant_chat_page.dart';
import 'package:loadmovegh/features/shell/presentation/pages/app_shell.dart';

/// GoRouter configuration with auth-guarded routes.

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/loads',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isLoggedIn = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/auth');

      if (!isLoggedIn && !isAuthRoute) return '/auth/login';
      if (isLoggedIn && isAuthRoute) return '/loads';
      return null;
    },
    routes: [
      // ── Auth (no bottom nav) ───────────────────────────────
      GoRoute(
        path: '/auth/login',
        name: 'login',
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: '/auth/register',
        name: 'register',
        builder: (context, state) => const RegisterPage(),
      ),
      GoRoute(
        path: '/auth/otp',
        name: 'otp',
        builder: (context, state) => OtpPage(
          phone: state.uri.queryParameters['phone'] ?? '',
        ),
      ),

      // ── AI Assistant (full-screen, no bottom nav) ──────────
      GoRoute(
        path: '/assistant',
        name: 'assistant',
        builder: (context, state) => const AssistantChatPage(),
      ),

      // ── App Shell (with bottom nav) ────────────────────────
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(
            path: '/loads',
            name: 'loads',
            builder: (context, state) => const LoadBoardPage(),
            routes: [
              GoRoute(
                path: ':id',
                name: 'load-detail',
                builder: (context, state) => LoadDetailPage(
                  loadId: state.pathParameters['id']!,
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/tracking',
            name: 'tracking',
            builder: (context, state) => const TrackingPage(),
          ),
          GoRoute(
            path: '/bids',
            name: 'bids',
            builder: (context, state) => const BidPage(),
          ),
          GoRoute(
            path: '/wallet',
            name: 'wallet',
            builder: (context, state) => const WalletPage(),
          ),
          GoRoute(
            path: '/notifications',
            name: 'notifications',
            builder: (context, state) => const NotificationsPage(),
          ),
        ],
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Text(
          'Page not found: ${state.matchedLocation}',
          style: Theme.of(context).textTheme.bodyLarge,
        ),
      ),
    ),
  );
});
