import 'package:equatable/equatable.dart';

/// Domain entity for a user's wallet.

class WalletEntity extends Equatable {
  final String id;
  final String userId;
  final double balance;
  final double escrowHeld;
  final double totalEarnings;
  final double totalSpent;
  final String currency;
  final String status; // active | frozen | suspended

  const WalletEntity({
    required this.id,
    required this.userId,
    required this.balance,
    this.escrowHeld = 0,
    this.totalEarnings = 0,
    this.totalSpent = 0,
    this.currency = 'GHS',
    this.status = 'active',
  });

  double get available => balance - escrowHeld;

  @override
  List<Object?> get props => [id];
}

/// A single wallet transaction.

class TransactionEntity extends Equatable {
  final String id;
  final String type; // deposit | withdrawal | escrow_hold | escrow_release | commission | payout
  final double amount;
  final String currency;
  final String status; // pending | completed | failed | reversed
  final String? description;
  final String? referenceId;
  final DateTime createdAt;

  const TransactionEntity({
    required this.id,
    required this.type,
    required this.amount,
    this.currency = 'GHS',
    required this.status,
    this.description,
    this.referenceId,
    required this.createdAt,
  });

  @override
  List<Object?> get props => [id];
}
