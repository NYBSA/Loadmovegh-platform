import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/features/bids/domain/entities/bid_entity.dart';

/// Bid repository contract.

abstract class BidRepository {
  /// Get bids for a specific listing (shipper view).
  Future<Either<Failure, List<BidEntity>>> getBidsForListing(String listingId);

  /// Get my bids (courier view).
  Future<Either<Failure, List<BidEntity>>> getMyBids();

  /// Submit a new bid on a listing.
  Future<Either<Failure, BidEntity>> submitBid({
    required String listingId,
    required double amount,
    required DateTime estimatedPickup,
    required DateTime estimatedDelivery,
    String? note,
  });

  /// Accept a bid (shipper).
  Future<Either<Failure, BidEntity>> acceptBid(String bidId);

  /// Reject a bid (shipper).
  Future<Either<Failure, BidEntity>> rejectBid(String bidId);

  /// Withdraw a bid (courier).
  Future<Either<Failure, void>> withdrawBid(String bidId);
}
