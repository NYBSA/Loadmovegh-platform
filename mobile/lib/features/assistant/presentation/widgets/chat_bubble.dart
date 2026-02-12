import 'package:flutter/material.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/utils/extensions.dart';
import 'package:loadmovegh/features/assistant/domain/entities/chat_entity.dart';

/// A single chat message bubble — user messages right, assistant left.

class ChatBubble extends StatelessWidget {
  final ChatMessageEntity message;
  const ChatBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.isUser;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.80,
        ),
        child: Column(
          crossAxisAlignment:
              isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isUser ? AppColors.brand600 : Colors.white,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(18),
                  topRight: const Radius.circular(18),
                  bottomLeft:
                      isUser ? const Radius.circular(18) : const Radius.circular(4),
                  bottomRight:
                      isUser ? const Radius.circular(4) : const Radius.circular(18),
                ),
                border: isUser ? null : Border.all(color: AppColors.gray100),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.04),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Assistant avatar/label
                  if (!isUser) ...[
                    Row(
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
                        const SizedBox(width: 6),
                        const Text(
                          'LoadMove AI',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: AppColors.brand600,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                  ],

                  // Message content
                  if (message.content != null && message.content!.isNotEmpty)
                    Text(
                      message.content!,
                      style: TextStyle(
                        fontSize: 14,
                        color: isUser ? Colors.white : AppColors.gray800,
                        height: 1.5,
                      ),
                    ),
                ],
              ),
            ),

            // Timestamp and metadata
            Padding(
              padding: const EdgeInsets.only(top: 4, left: 4, right: 4),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    message.createdAt.formattedWithTime,
                    style: const TextStyle(fontSize: 10, color: AppColors.gray400),
                  ),
                  if (!isUser && message.latencyMs > 0) ...[
                    const SizedBox(width: 6),
                    Text(
                      '${(message.latencyMs / 1000).toStringAsFixed(1)}s',
                      style: const TextStyle(fontSize: 10, color: AppColors.gray400),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
