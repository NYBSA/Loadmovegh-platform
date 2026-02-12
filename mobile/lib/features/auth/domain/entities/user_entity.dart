import 'package:equatable/equatable.dart';

/// Domain entity — framework-agnostic representation of a user.

class UserEntity extends Equatable {
  final String id;
  final String email;
  final String? phone;
  final String firstName;
  final String lastName;
  final String role; // shipper | courier | admin
  final String? orgName;
  final String? orgType; // individual | company
  final String kycStatus; // pending | verified | rejected
  final bool isEmailVerified;
  final bool isPhoneVerified;
  final DateTime createdAt;

  const UserEntity({
    required this.id,
    required this.email,
    this.phone,
    required this.firstName,
    required this.lastName,
    required this.role,
    this.orgName,
    this.orgType,
    this.kycStatus = 'pending',
    this.isEmailVerified = false,
    this.isPhoneVerified = false,
    required this.createdAt,
  });

  String get fullName => '$firstName $lastName';

  bool get isVerified => kycStatus == 'verified';

  @override
  List<Object?> get props => [id, email, phone, role, kycStatus];
}
