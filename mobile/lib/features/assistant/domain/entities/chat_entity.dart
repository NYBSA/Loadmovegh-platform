import 'package:equatable/equatable.dart';

/// Domain entity for a chat session.

class ChatSessionEntity extends Equatable {
  final String id;
  final String title;
  final String status;
  final int messageCount;
  final DateTime createdAt;
  final DateTime updatedAt;

  const ChatSessionEntity({
    required this.id,
    required this.title,
    this.status = 'active',
    this.messageCount = 0,
    required this.createdAt,
    required this.updatedAt,
  });

  @override
  List<Object?> get props => [id];
}

/// Domain entity for a single chat message.

class ChatMessageEntity extends Equatable {
  final String id;
  final String role; // user | assistant | tool
  final String? content;
  final List<ToolCallEntity> toolCalls;
  final String? modelUsed;
  final int latencyMs;
  final DateTime createdAt;

  const ChatMessageEntity({
    required this.id,
    required this.role,
    this.content,
    this.toolCalls = const [],
    this.modelUsed,
    this.latencyMs = 0,
    required this.createdAt,
  });

  bool get isUser => role == 'user';
  bool get isAssistant => role == 'assistant';
  bool get hasToolCalls => toolCalls.isNotEmpty;

  @override
  List<Object?> get props => [id];
}

/// A tool call made by the assistant.

class ToolCallEntity extends Equatable {
  final String toolName;
  final Map<String, dynamic> arguments;
  final Map<String, dynamic> result;

  const ToolCallEntity({
    required this.toolName,
    this.arguments = const {},
    this.result = const {},
  });

  @override
  List<Object?> get props => [toolName, arguments];
}

/// A suggested prompt chip.

class SuggestedPromptEntity {
  final String icon;
  final String label;
  final String message;
  final String category;

  const SuggestedPromptEntity({
    required this.icon,
    required this.label,
    required this.message,
    required this.category,
  });
}
