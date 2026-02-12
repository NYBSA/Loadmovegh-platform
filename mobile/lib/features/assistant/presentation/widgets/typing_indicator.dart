import 'package:flutter/material.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';

/// Animated typing indicator shown while waiting for the AI reply.

class TypingIndicator extends StatefulWidget {
  const TypingIndicator({super.key});

  @override
  State<TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(18),
            topRight: Radius.circular(18),
            bottomRight: Radius.circular(18),
            bottomLeft: Radius.circular(4),
          ),
          border: Border.all(color: AppColors.gray100),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(3),
              decoration: BoxDecoration(
                color: AppColors.brand50,
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Icon(
                Icons.auto_awesome,
                size: 12,
                color: AppColors.brand600,
              ),
            ),
            const SizedBox(width: 10),
            AnimatedBuilder(
              animation: _controller,
              builder: (context, _) {
                return Row(
                  children: List.generate(3, (i) {
                    final delay = i * 0.2;
                    final t = (_controller.value - delay).clamp(0.0, 1.0);
                    final bounce = (1 - (2 * t - 1).abs());

                    return Container(
                      margin: const EdgeInsets.symmetric(horizontal: 2),
                      width: 7,
                      height: 7,
                      decoration: BoxDecoration(
                        color: AppColors.brand400.withOpacity(0.4 + bounce * 0.6),
                        shape: BoxShape.circle,
                      ),
                    );
                  }),
                );
              },
            ),
            const SizedBox(width: 6),
            const Text(
              'Thinking…',
              style: TextStyle(
                fontSize: 12,
                color: AppColors.gray400,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
