import 'package:loadmovegh/features/auth/domain/entities/user_entity.dart';

/// JSON-serializable user model — maps API responses to domain entities.

class UserModel extends UserEntity {
  const UserModel({
    required super.id,
    required super.email,
    super.phone,
    required super.firstName,
    required super.lastName,
    required super.role,
    super.orgName,
    super.orgType,
    super.kycStatus,
    super.isEmailVerified,
    super.isPhoneVerified,
    required super.createdAt,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      email: json['email'] as String,
      phone: json['phone'] as String?,
      firstName: json['first_name'] as String? ?? '',
      lastName: json['last_name'] as String? ?? '',
      role: json['role'] as String? ?? 'courier',
      orgName: json['org_name'] as String?,
      orgType: json['org_type'] as String?,
      kycStatus: json['kyc_status'] as String? ?? 'pending',
      isEmailVerified: json['is_email_verified'] as bool? ?? false,
      isPhoneVerified: json['is_phone_verified'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'phone': phone,
        'first_name': firstName,
        'last_name': lastName,
        'role': role,
        'org_name': orgName,
        'org_type': orgType,
        'kyc_status': kycStatus,
        'is_email_verified': isEmailVerified,
        'is_phone_verified': isPhoneVerified,
        'created_at': createdAt.toIso8601String(),
      };
}
