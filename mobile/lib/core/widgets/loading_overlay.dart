import 'package:flutter/material.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';

/// Full-screen semi-transparent loading overlay.

class LoadingOverlay extends StatelessWidget {
  final bool isLoading;
  final Widget child;

  const LoadingOverlay({
    super.key,
    required this.isLoading,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        child,
        if (isLoading)
          Container(
            color: Colors.black26,
            child: const Center(
              child: CircularProgressIndicator(
                color: AppColors.brand600,
                strokeWidth: 3,
              ),
            ),
          ),
      ],
    );
  }
}
