import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';
import 'package:loadmovegh/core/widgets/loading_overlay.dart';
import 'package:loadmovegh/features/auth/presentation/providers/auth_provider.dart';

class OtpPage extends ConsumerStatefulWidget {
  final String phone;
  const OtpPage({super.key, required this.phone});

  @override
  ConsumerState<OtpPage> createState() => _OtpPageState();
}

class _OtpPageState extends ConsumerState<OtpPage> {
  final List<TextEditingController> _controllers =
      List.generate(6, (_) => TextEditingController());
  final List<FocusNode> _focusNodes = List.generate(6, (_) => FocusNode());

  @override
  void dispose() {
    for (final c in _controllers) {
      c.dispose();
    }
    for (final f in _focusNodes) {
      f.dispose();
    }
    super.dispose();
  }

  String get _otp => _controllers.map((c) => c.text).join();

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Verify Phone')),
      body: LoadingOverlay(
        isLoading: authState.isLoading,
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const SizedBox(height: 32),
              const Icon(Icons.sms_outlined, size: 56, color: AppColors.brand500),
              const SizedBox(height: 16),
              const Text(
                'Enter verification code',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                  color: AppColors.gray900,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'A 6-digit code was sent to ${widget.phone}',
                style: const TextStyle(fontSize: 14, color: AppColors.gray500),
              ),
              const SizedBox(height: 40),

              // ── OTP input boxes ──────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(6, (i) {
                  return Container(
                    width: 48,
                    height: 56,
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    child: TextFormField(
                      controller: _controllers[i],
                      focusNode: _focusNodes[i],
                      textAlign: TextAlign.center,
                      keyboardType: TextInputType.number,
                      inputFormatters: [
                        FilteringTextInputFormatter.digitsOnly,
                        LengthLimitingTextInputFormatter(1),
                      ],
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                      ),
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(vertical: 14),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                      onChanged: (value) {
                        if (value.isNotEmpty && i < 5) {
                          _focusNodes[i + 1].requestFocus();
                        }
                        if (_otp.length == 6) _verify();
                      },
                    ),
                  );
                }),
              ),
              const SizedBox(height: 32),

              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _otp.length == 6 ? _verify : null,
                  child: const Text('Verify'),
                ),
              ),
              const SizedBox(height: 16),
              TextButton(
                onPressed: () {
                  ref.read(authStateProvider.notifier).requestOtp(widget.phone);
                },
                child: const Text(
                  'Resend Code',
                  style: TextStyle(color: AppColors.brand600),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _verify() {
    ref.read(authStateProvider.notifier).verifyOtp(widget.phone, _otp);
  }
}
