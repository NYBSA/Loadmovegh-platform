import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/features/wallet/domain/entities/wallet_entity.dart';

/// Wallet & payment repository contract.

abstract class WalletRepository {
  /// Get the current user's wallet.
  Future<Either<Failure, WalletEntity>> getWallet();

  /// Get transaction history.
  Future<Either<Failure, List<TransactionEntity>>> getTransactions({
    int page = 1,
    int limit = 20,
    String? type,
  });

  /// Deposit via MTN Mobile Money.
  Future<Either<Failure, TransactionEntity>> depositMoMo({
    required double amount,
    required String phone,
    required String provider, // mtn | vodafone | airteltigo
  });

  /// Withdraw to Mobile Money.
  Future<Either<Failure, TransactionEntity>> withdrawMoMo({
    required double amount,
    required String phone,
    required String provider,
  });
}
