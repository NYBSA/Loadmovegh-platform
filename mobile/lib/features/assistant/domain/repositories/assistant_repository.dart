import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/features/assistant/domain/entities/chat_entity.dart';

/// AI Assistant repository contract.

abstract class AssistantRepository {
  /// Create a new chat session.
  Future<Either<Failure, ChatSessionEntity>> createSession({String? title});

  /// List the user's chat sessions.
  Future<Either<Failure, List<ChatSessionEntity>>> getSessions({int page = 1});

  /// Get a session with all messages.
  Future<Either<Failure, List<ChatMessageEntity>>> getSessionMessages(String sessionId);

  /// Send a message and get the AI reply.
  Future<Either<Failure, ChatMessageEntity>> sendMessage({
    required String sessionId,
    required String content,
    String? contextListingId,
    String? contextTripId,
  });

  /// One-shot quick action (no session).
  Future<Either<Failure, Map<String, dynamic>>> quickAction({
    required String action,
    Map<String, dynamic> params = const {},
  });

  /// Get contextual prompt suggestions.
  Future<Either<Failure, List<SuggestedPromptEntity>>> getSuggestions();

  /// Delete / archive a session.
  Future<Either<Failure, void>> deleteSession(String sessionId);
}
