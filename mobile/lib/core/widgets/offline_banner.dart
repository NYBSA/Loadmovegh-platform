import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';

/// A small banner that slides in when the device goes offline.

class OfflineBanner extends StatelessWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<List<ConnectivityResult>>(
      stream: Connectivity().onConnectivityChanged,
      builder: (context, snapshot) {
        final isOffline = snapshot.data?.contains(ConnectivityResult.none) ?? false;

        return AnimatedSlide(
          offset: isOffline ? Offset.zero : const Offset(0, -1),
          duration: const Duration(milliseconds: 300),
          child: isOffline
              ? Container(
                  width: double.infinity,
                  color: AppColors.accent500,
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: const Text(
                    'You are offline — showing cached data',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                )
              : const SizedBox.shrink(),
        );
      },
    );
  }
}
