import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/utils/extensions.dart';
import 'package:loadmovegh/features/assistant/domain/entities/chat_entity.dart';
import 'package:loadmovegh/features/assistant/presentation/providers/assistant_provider.dart';
import 'package:loadmovegh/features/assistant/presentation/widgets/chat_bubble.dart';
import 'package:loadmovegh/features/assistant/presentation/widgets/tool_result_card.dart';
import 'package:loadmovegh/features/assistant/presentation/widgets/typing_indicator.dart';

/// Main AI assistant chat page — accessible via FAB or bottom nav.

class AssistantChatPage extends ConsumerStatefulWidget {
  const AssistantChatPage({super.key});

  @override
  ConsumerState<AssistantChatPage> createState() => _AssistantChatPageState();
}

class _AssistantChatPageState extends ConsumerState<AssistantChatPage> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final _focusNode = FocusNode();

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      Future.delayed(const Duration(milliseconds: 100), () {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(assistantChatProvider);

    ref.listen<AssistantChatState>(assistantChatProvider, (prev, next) {
      if (next.messages.length > (prev?.messages.length ?? 0)) {
        _scrollToBottom();
      }
      if (next.error != null) {
        context.showSnack(next.error!, isError: true);
      }
    });

    return Scaffold(
      appBar: _buildAppBar(context),
      body: Column(
        children: [
          // ── Messages list ─────────────────────────────
          Expanded(
            child: chatState.messages.isEmpty && !chatState.isLoading
                ? _buildEmptyState(chatState)
                : _buildMessageList(chatState),
          ),

          // ── Input area ────────────────────────────────
          _buildInputArea(chatState),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      title: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: AppColors.brand100,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.auto_awesome,
              size: 18,
              color: AppColors.brand600,
            ),
          ),
          const SizedBox(width: 10),
          const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'LoadMove AI',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
              ),
              Text(
                'Your freight advisor',
                style: TextStyle(fontSize: 11, color: AppColors.gray500),
              ),
            ],
          ),
        ],
      ),
      actions: [
        PopupMenuButton<String>(
          onSelected: (value) {
            if (value == 'clear') {
              ref.read(assistantChatProvider.notifier).clearChat();
            }
          },
          itemBuilder: (_) => [
            const PopupMenuItem(
              value: 'clear',
              child: Row(
                children: [
                  Icon(Icons.refresh, size: 18, color: AppColors.gray600),
                  SizedBox(width: 8),
                  Text('New conversation'),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  /// Empty state with greeting and suggestion chips.
  Widget _buildEmptyState(AssistantChatState chatState) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const SizedBox(height: 40),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppColors.brand50,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.auto_awesome,
              size: 40,
              color: AppColors.brand600,
            ),
          ),
          const SizedBox(height: 20),
          const Text(
            'Hi! I\'m LoadMove AI',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: AppColors.gray900,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Your smart freight advisor. I can help you find loads,\nrecommend pricing, forecast profits, and more.',
            style: TextStyle(fontSize: 14, color: AppColors.gray500, height: 1.5),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),

          // Suggestion chips
          if (chatState.suggestions.isNotEmpty) ...[
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Try asking:',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppColors.gray600,
                ),
              ),
            ),
            const SizedBox(height: 12),
            ...chatState.suggestions.map((s) => _buildSuggestionTile(s)),
          ],
        ],
      ),
    );
  }

  Widget _buildSuggestionTile(SuggestedPromptEntity suggestion) {
    final iconData = _categoryIcon(suggestion.category);

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: () {
          _controller.text = suggestion.message;
          _sendMessage();
        },
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.gray100),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: _categoryColor(suggestion.category).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  iconData,
                  size: 18,
                  color: _categoryColor(suggestion.category),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      suggestion.label,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AppColors.gray800,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      suggestion.message,
                      style: const TextStyle(fontSize: 12, color: AppColors.gray500),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios, size: 14, color: AppColors.gray400),
            ],
          ),
        ),
      ),
    );
  }

  /// Message list.
  Widget _buildMessageList(AssistantChatState chatState) {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      itemCount: chatState.messages.length + (chatState.isSending ? 1 : 0),
      itemBuilder: (context, index) {
        // Show typing indicator as last item while sending
        if (index == chatState.messages.length && chatState.isSending) {
          return const Padding(
            padding: EdgeInsets.only(top: 8),
            child: TypingIndicator(),
          );
        }

        final message = chatState.messages[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Column(
            children: [
              ChatBubble(message: message),
              // Show tool result cards for assistant messages
              if (message.isAssistant && message.hasToolCalls)
                ...message.toolCalls.map(
                  (tc) => Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: ToolResultCard(toolCall: tc),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  /// Input bar.
  Widget _buildInputArea(AssistantChatState chatState) {
    return Container(
      padding: EdgeInsets.fromLTRB(
        16, 12, 16,
        MediaQuery.of(context).viewPadding.bottom + 12,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: AppColors.gray50,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: AppColors.gray200),
              ),
              child: Row(
                children: [
                  const SizedBox(width: 16),
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      focusNode: _focusNode,
                      decoration: const InputDecoration(
                        hintText: 'Ask LoadMove AI...',
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(vertical: 12),
                        hintStyle: TextStyle(color: AppColors.gray400),
                      ),
                      maxLines: 3,
                      minLines: 1,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  const SizedBox(width: 4),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: chatState.isSending ? null : _sendMessage,
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: chatState.isSending
                    ? AppColors.gray300
                    : AppColors.brand600,
                shape: BoxShape.circle,
              ),
              child: Icon(
                chatState.isSending ? Icons.hourglass_top : Icons.send_rounded,
                size: 20,
                color: Colors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    ref.read(assistantChatProvider.notifier).sendMessage(text);
  }

  IconData _categoryIcon(String category) {
    return switch (category) {
      'loads' => Icons.inventory_2_outlined,
      'pricing' => Icons.attach_money,
      'profit' => Icons.trending_up,
      'route' => Icons.map_outlined,
      'help' => Icons.help_outline,
      _ => Icons.auto_awesome,
    };
  }

  Color _categoryColor(String category) {
    return switch (category) {
      'loads' => AppColors.brand600,
      'pricing' => AppColors.accent600,
      'profit' => AppColors.success,
      'route' => AppColors.info,
      'help' => AppColors.gray600,
      _ => AppColors.brand600,
    };
  }
}
