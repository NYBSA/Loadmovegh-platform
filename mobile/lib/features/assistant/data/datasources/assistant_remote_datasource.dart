import 'package:dio/dio.dart';
import 'package:loadmovegh/core/error/exceptions.dart';
import 'package:loadmovegh/features/assistant/domain/entities/chat_entity.dart';

/// Remote data source for AI Assistant API calls.

class AssistantRemoteDataSource {
  final Dio dio;
  const AssistantRemoteDataSource({required this.dio});

  /// POST /assistant/sessions
  Future<ChatSessionEntity> createSession({String? title}) async {
    try {
      final response = await dio.post('/assistant/sessions', data: {
        if (title != null) 'title': title,
      });
      return _parseSession(response.data);
    } on DioException catch (e) {
      throw ServerException(message: _msg(e));
    }
  }

  /// GET /assistant/sessions
  Future<List<ChatSessionEntity>> getSessions({int page = 1}) async {
    try {
      final response = await dio.get('/assistant/sessions', queryParameters: {
        'page': page,
        'limit': 20,
      });
      final list = response.data['sessions'] as List? ?? [];
      return list.map((e) => _parseSession(e)).toList();
    } on DioException catch (e) {
      throw ServerException(message: _msg(e));
    }
  }

  /// GET /assistant/sessions/:id
  Future<List<ChatMessageEntity>> getSessionMessages(String sessionId) async {
    try {
      final response = await dio.get('/assistant/sessions/$sessionId');
      final msgs = response.data['messages'] as List? ?? [];
      return msgs.map((e) => _parseMessage(e)).toList();
    } on DioException catch (e) {
      throw ServerException(message: _msg(e));
    }
  }

  /// POST /assistant/sessions/:id/messages
  Future<ChatMessageEntity> sendMessage({
    required String sessionId,
    required String content,
    String? contextListingId,
    String? contextTripId,
  }) async {
    try {
      final response = await dio.post(
        '/assistant/sessions/$sessionId/messages',
        data: {
          'content': content,
          if (contextListingId != null) 'context_listing_id': contextListingId,
          if (contextTripId != null) 'context_trip_id': contextTripId,
        },
      );
      return _parseMessage(response.data['reply']);
    } on DioException catch (e) {
      throw ServerException(message: _msg(e));
    }
  }

  /// POST /assistant/quick
  Future<Map<String, dynamic>> quickAction({
    required String action,
    Map<String, dynamic> params = const {},
  }) async {
    try {
      final response = await dio.post('/assistant/quick', data: {
        'action': action,
        'params': params,
      });
      return Map<String, dynamic>.from(response.data);
    } on DioException catch (e) {
      throw ServerException(message: _msg(e));
    }
  }

  /// GET /assistant/suggestions
  Future<List<SuggestedPromptEntity>> getSuggestions() async {
    try {
      final response = await dio.get('/assistant/suggestions');
      final list = response.data['prompts'] as List? ?? [];
      return list
          .map((e) => SuggestedPromptEntity(
                icon: e['icon'] ?? '',
                label: e['label'] ?? '',
                message: e['message'] ?? '',
                category: e['category'] ?? 'general',
              ))
          .toList();
    } on DioException catch (e) {
      throw ServerException(message: _msg(e));
    }
  }

  /// DELETE /assistant/sessions/:id
  Future<void> deleteSession(String sessionId) async {
    try {
      await dio.delete('/assistant/sessions/$sessionId');
    } on DioException catch (e) {
      throw ServerException(message: _msg(e));
    }
  }

  // ── Parsers ──────────────────────────────────────────────

  ChatSessionEntity _parseSession(Map<String, dynamic> json) {
    return ChatSessionEntity(
      id: json['id'] as String,
      title: json['title'] as String? ?? 'Conversation',
      status: json['status'] as String? ?? 'active',
      messageCount: json['message_count'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  ChatMessageEntity _parseMessage(Map<String, dynamic> json) {
    final toolCalls = (json['tool_calls'] as List? ?? [])
        .map((tc) => ToolCallEntity(
              toolName: tc['tool_name'] as String? ?? '',
              arguments: Map<String, dynamic>.from(tc['arguments'] ?? {}),
              result: Map<String, dynamic>.from(tc['result'] ?? {}),
            ))
        .toList();

    return ChatMessageEntity(
      id: json['id'] as String,
      role: json['role'] as String? ?? 'assistant',
      content: json['content'] as String?,
      toolCalls: toolCalls,
      modelUsed: json['model_used'] as String?,
      latencyMs: json['latency_ms'] as int? ?? 0,
      createdAt: DateTime.parse(
        json['created_at'] as String? ?? DateTime.now().toIso8601String(),
      ),
    );
  }

  String _msg(DioException e) {
    final data = e.response?.data;
    if (data is Map) return data['detail']?.toString() ?? 'Unknown error';
    return e.message ?? 'Network error';
  }
}
