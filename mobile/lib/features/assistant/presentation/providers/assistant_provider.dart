import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/network/api_client.dart';
import 'package:loadmovegh/features/assistant/data/datasources/assistant_remote_datasource.dart';
import 'package:loadmovegh/features/assistant/data/repositories/assistant_repository_impl.dart';
import 'package:loadmovegh/features/assistant/domain/entities/chat_entity.dart';
import 'package:loadmovegh/features/assistant/domain/repositories/assistant_repository.dart';

// ── Repository ─────────────────────────────────────────────

final assistantRepositoryProvider = Provider<AssistantRepository>((ref) {
  return AssistantRepositoryImpl(
    remoteDataSource: AssistantRemoteDataSource(dio: ref.read(apiClientProvider)),
  );
});

// ── Chat State ─────────────────────────────────────────────

class AssistantChatState {
  final String? sessionId;
  final List<ChatMessageEntity> messages;
  final List<SuggestedPromptEntity> suggestions;
  final bool isLoading;
  final bool isSending;
  final String? error;

  const AssistantChatState({
    this.sessionId,
    this.messages = const [],
    this.suggestions = const [],
    this.isLoading = false,
    this.isSending = false,
    this.error,
  });

  AssistantChatState copyWith({
    String? sessionId,
    List<ChatMessageEntity>? messages,
    List<SuggestedPromptEntity>? suggestions,
    bool? isLoading,
    bool? isSending,
    String? error,
  }) =>
      AssistantChatState(
        sessionId: sessionId ?? this.sessionId,
        messages: messages ?? this.messages,
        suggestions: suggestions ?? this.suggestions,
        isLoading: isLoading ?? this.isLoading,
        isSending: isSending ?? this.isSending,
        error: error,
      );
}

// ── Notifier ───────────────────────────────────────────────

class AssistantChatNotifier extends StateNotifier<AssistantChatState> {
  final AssistantRepository _repository;

  AssistantChatNotifier(this._repository) : super(const AssistantChatState()) {
    _loadSuggestions();
  }

  /// Load suggested prompts for the empty chat state.
  Future<void> _loadSuggestions() async {
    final result = await _repository.getSuggestions();
    result.fold(
      (_) {},
      (suggestions) => state = state.copyWith(suggestions: suggestions),
    );
  }

  /// Start a new chat session.
  Future<void> startSession({String? title}) async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await _repository.createSession(title: title);
    result.fold(
      (failure) => state = state.copyWith(isLoading: false, error: failure.message),
      (session) => state = state.copyWith(
        sessionId: session.id,
        messages: [],
        isLoading: false,
      ),
    );
  }

  /// Load an existing session's messages.
  Future<void> loadSession(String sessionId) async {
    state = state.copyWith(isLoading: true, sessionId: sessionId, error: null);
    final result = await _repository.getSessionMessages(sessionId);
    result.fold(
      (failure) => state = state.copyWith(isLoading: false, error: failure.message),
      (messages) => state = state.copyWith(messages: messages, isLoading: false),
    );
  }

  /// Send a message and get the AI reply.
  Future<void> sendMessage(String content, {String? contextListingId}) async {
    if (state.isSending) return;

    // Ensure we have a session
    if (state.sessionId == null) {
      await startSession(title: content.length > 60 ? '${content.substring(0, 60)}...' : content);
      if (state.sessionId == null) return; // Failed
    }

    // Optimistically add user message
    final userMsg = ChatMessageEntity(
      id: 'temp_${DateTime.now().millisecondsSinceEpoch}',
      role: 'user',
      content: content,
      createdAt: DateTime.now(),
    );

    state = state.copyWith(
      messages: [...state.messages, userMsg],
      isSending: true,
      error: null,
    );

    final result = await _repository.sendMessage(
      sessionId: state.sessionId!,
      content: content,
      contextListingId: contextListingId,
    );

    result.fold(
      (failure) => state = state.copyWith(
        isSending: false,
        error: failure.message,
      ),
      (reply) => state = state.copyWith(
        messages: [...state.messages, reply],
        isSending: false,
      ),
    );
  }

  /// Clear the current session for a fresh start.
  void clearChat() {
    state = const AssistantChatState();
    _loadSuggestions();
  }
}

final assistantChatProvider =
    StateNotifierProvider<AssistantChatNotifier, AssistantChatState>((ref) {
  return AssistantChatNotifier(ref.read(assistantRepositoryProvider));
});
