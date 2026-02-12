import 'package:dartz/dartz.dart';
import 'package:loadmovegh/core/error/failures.dart';
import 'package:loadmovegh/features/auth/domain/entities/user_entity.dart';
import 'package:loadmovegh/features/auth/domain/repositories/auth_repository.dart';

class LoginUseCase {
  final AuthRepository repository;
  const LoginUseCase(this.repository);

  Future<Either<Failure, UserEntity>> call({
    required String email,
    required String password,
  }) {
    return repository.login(email: email, password: password);
  }
}

class PhoneLoginUseCase {
  final AuthRepository repository;
  const PhoneLoginUseCase(this.repository);

  Future<Either<Failure, void>> requestOtp({required String phone}) {
    return repository.requestOtp(phone: phone);
  }

  Future<Either<Failure, UserEntity>> verifyOtp({
    required String phone,
    required String code,
  }) {
    return repository.verifyOtp(phone: phone, code: code);
  }
}

class RegisterUseCase {
  final AuthRepository repository;
  const RegisterUseCase(this.repository);

  Future<Either<Failure, UserEntity>> call({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String role,
    String? phone,
    String? orgName,
  }) {
    return repository.register(
      email: email,
      password: password,
      firstName: firstName,
      lastName: lastName,
      role: role,
      phone: phone,
      orgName: orgName,
    );
  }
}
