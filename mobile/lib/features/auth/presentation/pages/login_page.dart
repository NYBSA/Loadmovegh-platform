import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/utils/validators.dart';
import 'package:loadmovegh/core/widgets/loading_overlay.dart';
import 'package:loadmovegh/features/auth/presentation/providers/auth_provider.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _emailFormKey = GlobalKey<FormState>();
  final _phoneFormKey = GlobalKey<FormState>();

  // Email login
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _obscurePassword = true;

  // Phone login
  final _phoneCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);

    ref.listen<AuthState>(authStateProvider, (prev, next) {
      if (next.error != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.error!),
            backgroundColor: AppColors.error,
          ),
        );
      }
    });

    return Scaffold(
      body: LoadingOverlay(
        isLoading: authState.isLoading,
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              children: [
                const SizedBox(height: 60),

                // ── Logo ──────────────────────────────
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    color: AppColors.brand600,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Icon(
                    Icons.local_shipping_rounded,
                    color: Colors.white,
                    size: 36,
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'LoadMoveGH',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.w800,
                    color: AppColors.gray900,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Ghana\'s Freight Marketplace',
                  style: TextStyle(fontSize: 14, color: AppColors.gray500),
                ),
                const SizedBox(height: 40),

                // ── Tab bar ───────────────────────────
                Container(
                  decoration: BoxDecoration(
                    color: AppColors.gray100,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    indicator: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(8),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.05),
                          blurRadius: 4,
                          offset: const Offset(0, 1),
                        ),
                      ],
                    ),
                    indicatorPadding: const EdgeInsets.all(3),
                    labelColor: AppColors.gray900,
                    unselectedLabelColor: AppColors.gray500,
                    labelStyle: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                    dividerHeight: 0,
                    tabs: const [
                      Tab(text: 'Email'),
                      Tab(text: 'Phone'),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // ── Tab content ───────────────────────
                SizedBox(
                  height: 280,
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      _buildEmailForm(),
                      _buildPhoneForm(),
                    ],
                  ),
                ),

                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text(
                      'Don\'t have an account? ',
                      style: TextStyle(color: AppColors.gray500),
                    ),
                    GestureDetector(
                      onTap: () => context.pushNamed('register'),
                      child: const Text(
                        'Register',
                        style: TextStyle(
                          color: AppColors.brand600,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmailForm() {
    return Form(
      key: _emailFormKey,
      child: Column(
        children: [
          TextFormField(
            controller: _emailCtrl,
            decoration: const InputDecoration(
              labelText: 'Email',
              hintText: 'you@example.com',
              prefixIcon: Icon(Icons.email_outlined, size: 20),
            ),
            keyboardType: TextInputType.emailAddress,
            validator: Validators.email,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _passwordCtrl,
            decoration: InputDecoration(
              labelText: 'Password',
              prefixIcon: const Icon(Icons.lock_outline, size: 20),
              suffixIcon: IconButton(
                icon: Icon(
                  _obscurePassword ? Icons.visibility_off : Icons.visibility,
                  size: 20,
                ),
                onPressed: () =>
                    setState(() => _obscurePassword = !_obscurePassword),
              ),
            ),
            obscureText: _obscurePassword,
            validator: Validators.password,
          ),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: () {
                // TODO: Navigate to forgot password page
              },
              child: const Text(
                'Forgot password?',
                style: TextStyle(fontSize: 13, color: AppColors.brand600),
              ),
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                if (_emailFormKey.currentState!.validate()) {
                  ref.read(authStateProvider.notifier).login(
                        _emailCtrl.text.trim(),
                        _passwordCtrl.text,
                      );
                }
              },
              child: const Text('Sign In'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPhoneForm() {
    return Form(
      key: _phoneFormKey,
      child: Column(
        children: [
          TextFormField(
            controller: _phoneCtrl,
            decoration: const InputDecoration(
              labelText: 'Phone Number',
              hintText: '024XXXXXXX',
              prefixIcon: Icon(Icons.phone_outlined, size: 20),
              prefixText: '+233 ',
            ),
            keyboardType: TextInputType.phone,
            validator: Validators.phone,
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                if (_phoneFormKey.currentState!.validate()) {
                  ref
                      .read(authStateProvider.notifier)
                      .requestOtp(_phoneCtrl.text.trim());
                  context.pushNamed('otp',
                      queryParameters: {'phone': _phoneCtrl.text.trim()});
                }
              },
              child: const Text('Send OTP'),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'We\'ll send a 6-digit code to your phone via SMS.',
            style: TextStyle(fontSize: 13, color: AppColors.gray400),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
