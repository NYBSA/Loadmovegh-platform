/// Ghana-specific form validators matching the backend validation rules.

class Validators {
  const Validators._();

  static final _emailRegex = RegExp(r'^[\w\.\-]+@[\w\-]+\.\w{2,}$');
  static final _ghPhoneRegex = RegExp(r'^(\+233|0)(2[034-9]|5[045-9]|24)\d{7}$');

  static String? email(String? value) {
    if (value == null || value.trim().isEmpty) return 'Email is required';
    if (!_emailRegex.hasMatch(value.trim())) return 'Enter a valid email';
    return null;
  }

  static String? password(String? value) {
    if (value == null || value.isEmpty) return 'Password is required';
    if (value.length < 8) return 'At least 8 characters';
    if (!value.contains(RegExp(r'[A-Z]'))) return 'Include an uppercase letter';
    if (!value.contains(RegExp(r'[0-9]'))) return 'Include a number';
    return null;
  }

  static String? phone(String? value) {
    if (value == null || value.trim().isEmpty) return 'Phone number is required';
    if (!_ghPhoneRegex.hasMatch(value.trim())) {
      return 'Enter a valid Ghana number (e.g. 024XXXXXXX)';
    }
    return null;
  }

  static String? required(String? value, [String field = 'This field']) {
    if (value == null || value.trim().isEmpty) return '$field is required';
    return null;
  }

  static String? amount(String? value) {
    if (value == null || value.trim().isEmpty) return 'Amount is required';
    final parsed = double.tryParse(value);
    if (parsed == null || parsed <= 0) return 'Enter a valid amount';
    return null;
  }

  static String? otp(String? value) {
    if (value == null || value.trim().isEmpty) return 'OTP is required';
    if (value.trim().length != 6) return 'OTP must be 6 digits';
    if (!RegExp(r'^\d{6}$').hasMatch(value.trim())) return 'OTP must be digits only';
    return null;
  }
}
