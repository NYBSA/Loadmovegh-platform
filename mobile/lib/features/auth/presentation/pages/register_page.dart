import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/utils/validators.dart';
import 'package:loadmovegh/core/widgets/loading_overlay.dart';
import 'package:loadmovegh/features/auth/presentation/providers/auth_provider.dart';

class RegisterPage extends ConsumerStatefulWidget {
  const RegisterPage({super.key});

  @override
  ConsumerState<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends ConsumerState<RegisterPage> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _orgNameCtrl = TextEditingController();
  String _selectedRole = 'courier';
  bool _obscurePassword = true;

  @override
  void dispose() {
    _firstNameCtrl.dispose();
    _lastNameCtrl.dispose();
    _emailCtrl.dispose();
    _phoneCtrl.dispose();
    _passwordCtrl.dispose();
    _orgNameCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Account'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: LoadingOverlay(
        isLoading: authState.isLoading,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Join LoadMoveGH',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                    color: AppColors.gray900,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Start shipping or delivering freight across Ghana',
                  style: TextStyle(fontSize: 14, color: AppColors.gray500),
                ),
                const SizedBox(height: 32),

                // ── Role selector ──────────────────────
                const Text(
                  'I am a:',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: AppColors.gray700,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _buildRoleChip('courier', 'Courier', Icons.local_shipping),
                    const SizedBox(width: 12),
                    _buildRoleChip('shipper', 'Shipper', Icons.inventory_2),
                  ],
                ),
                const SizedBox(height: 24),

                // ── Name fields ────────────────────────
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _firstNameCtrl,
                        decoration:
                            const InputDecoration(labelText: 'First Name'),
                        validator: (v) => Validators.required(v, 'First name'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextFormField(
                        controller: _lastNameCtrl,
                        decoration:
                            const InputDecoration(labelText: 'Last Name'),
                        validator: (v) => Validators.required(v, 'Last name'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // ── Email ──────────────────────────────
                TextFormField(
                  controller: _emailCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    prefixIcon: Icon(Icons.email_outlined, size: 20),
                  ),
                  keyboardType: TextInputType.emailAddress,
                  validator: Validators.email,
                ),
                const SizedBox(height: 16),

                // ── Phone ──────────────────────────────
                TextFormField(
                  controller: _phoneCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Phone (Optional)',
                    hintText: '024XXXXXXX',
                    prefixIcon: Icon(Icons.phone_outlined, size: 20),
                  ),
                  keyboardType: TextInputType.phone,
                ),
                const SizedBox(height: 16),

                // ── Org name ───────────────────────────
                TextFormField(
                  controller: _orgNameCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Company / Business Name (Optional)',
                    prefixIcon: Icon(Icons.business_outlined, size: 20),
                  ),
                ),
                const SizedBox(height: 16),

                // ── Password ───────────────────────────
                TextFormField(
                  controller: _passwordCtrl,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    prefixIcon: const Icon(Icons.lock_outline, size: 20),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePassword
                            ? Icons.visibility_off
                            : Icons.visibility,
                        size: 20,
                      ),
                      onPressed: () => setState(
                          () => _obscurePassword = !_obscurePassword),
                    ),
                  ),
                  obscureText: _obscurePassword,
                  validator: Validators.password,
                ),
                const SizedBox(height: 8),
                const Text(
                  'At least 8 characters, 1 uppercase, 1 number',
                  style: TextStyle(fontSize: 12, color: AppColors.gray400),
                ),
                const SizedBox(height: 32),

                // ── Submit ─────────────────────────────
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _submit,
                    child: const Text('Create Account'),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text(
                      'Already have an account? ',
                      style: TextStyle(color: AppColors.gray500),
                    ),
                    GestureDetector(
                      onTap: () => context.pop(),
                      child: const Text(
                        'Sign In',
                        style: TextStyle(
                          color: AppColors.brand600,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRoleChip(String value, String label, IconData icon) {
    final selected = _selectedRole == value;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _selectedRole = value),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: selected ? AppColors.brand50 : Colors.white,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: selected ? AppColors.brand500 : AppColors.gray300,
              width: selected ? 1.5 : 1,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon,
                  size: 20,
                  color: selected ? AppColors.brand600 : AppColors.gray500),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: selected ? AppColors.brand700 : AppColors.gray600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    ref.read(authStateProvider.notifier).register(
          email: _emailCtrl.text.trim(),
          password: _passwordCtrl.text,
          firstName: _firstNameCtrl.text.trim(),
          lastName: _lastNameCtrl.text.trim(),
          role: _selectedRole,
          phone: _phoneCtrl.text.trim().isEmpty ? null : _phoneCtrl.text.trim(),
          orgName:
              _orgNameCtrl.text.trim().isEmpty ? null : _orgNameCtrl.text.trim(),
        );
  }
}
