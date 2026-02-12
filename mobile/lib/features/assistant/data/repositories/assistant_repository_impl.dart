import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/exceptions.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/features/assistant/data/datasources/assistant_remote_datasource.dart';
import 'package:loadmovegh/features/assistant/domain/entities/chat_entity.dart';
import 'package:loadmovegh/features/assistant/domain/repositories/assistant_repository.dart';

class AssistantRepositoryImpl implements AssistantRepository {
  final AssistantRemoteDataSource remoteDataSource;
  const AssistantRepositoryImpl({required this.remoteDataSource});

  @override
  Future<Either<Failure, ChatSessionEntity>> createSession({String? title}) async {
    try {
      final session = await remoteDataSource.createSession(title: title);
      return Right(session);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, List<ChatSessionEntity>>> getSessions({int page = 1}) async {
    try {
      final sessions = await remoteDataSource.getSessions(page: page);
      return Right(sessions);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, List<ChatMessageEntity>>> getSessionMessages(String sessionId) async {
    try {
      final messages = await remoteDataSource.getSessionMessages(sessionId);
      return Right(messages);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, ChatMessageEntity>> sendMessage({
    required String sessionId,
    required String content,
    String? contextListingId,
    String? contextTripId,
  }) async {
    try {
      final reply = await remoteDataSource.sendMessage(
        sessionId: sessionId,
        content: content,
        contextListingId: contextListingId,
        contextTripId: contextTripId,
      );
      return Right(reply);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, Map<String, dynamic>>> quickAction({
    required String action,
    Map<String, dynamic> params = const {},
  }) async {
    try {
      final result = await remoteDataSource.quickAction(action: action, params: params);
      return Right(result);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, List<SuggestedPromptEntity>>> getSuggestions() async {
    try {
      final suggestions = await remoteDataSource.getSuggestions();
      return Right(suggestions);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }

  @override
  Future<Either<Failure, void>> deleteSession(String sessionId) async {
    try {
      await remoteDataSource.deleteSession(sessionId);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(message: e.message));
    }
  }
}
