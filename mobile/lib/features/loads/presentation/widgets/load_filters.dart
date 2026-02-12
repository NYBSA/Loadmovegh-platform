import 'package:flutter/material.dart';
import 'package:loadmovegh/core/theme/app_colors.dart';

/// Bottom sheet filter panel for the load board.

class LoadFilters extends StatefulWidget {
  final void Function(Map<String, String?>) onApply;

  const LoadFilters({super.key, required this.onApply});

  @override
  State<LoadFilters> createState() => _LoadFiltersState();
}

class _LoadFiltersState extends State<LoadFilters> {
  String? _region;
  String? _cargoType;
  String? _vehicleType;
  String? _urgency;

  static const _regions = [
    'Greater Accra',
    'Ashanti',
    'Western',
    'Central',
    'Eastern',
    'Northern',
    'Volta',
    'Upper East',
    'Upper West',
    'Bono',
    'Bono East',
    'Ahafo',
    'Savannah',
    'North East',
    'Oti',
    'Western North',
  ];

  static const _cargoTypes = [
    'general',
    'perishable',
    'hazardous',
    'fragile',
    'bulk',
    'liquid',
    'livestock',
  ];

  static const _vehicleTypes = [
    'pickup',
    'van',
    'flatbed',
    'box_truck',
    'trailer',
    'refrigerated',
    'tanker',
  ];

  static const _urgencies = ['standard', 'express', 'urgent', 'scheduled'];

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.65,
      maxChildSize: 0.9,
      minChildSize: 0.4,
      expand: false,
      builder: (_, controller) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 24),
          child: ListView(
            controller: controller,
            children: [
              // ── Handle ──────────────────────────────
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.gray300,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                'Filter Loads',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: AppColors.gray900,
                ),
              ),
              const SizedBox(height: 24),

              // ── Region ──────────────────────────────
              _buildDropdown('Region', _regions, _region, (v) {
                setState(() => _region = v);
              }),
              const SizedBox(height: 16),

              // ── Cargo Type ──────────────────────────
              _buildDropdown('Cargo Type', _cargoTypes, _cargoType, (v) {
                setState(() => _cargoType = v);
              }),
              const SizedBox(height: 16),

              // ── Vehicle Type ────────────────────────
              _buildDropdown('Vehicle Type', _vehicleTypes, _vehicleType, (v) {
                setState(() => _vehicleType = v);
              }),
              const SizedBox(height: 16),

              // ── Urgency ─────────────────────────────
              _buildDropdown('Urgency', _urgencies, _urgency, (v) {
                setState(() => _urgency = v);
              }),
              const SizedBox(height: 32),

              // ── Actions ─────────────────────────────
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        setState(() {
                          _region = _cargoType = _vehicleType = _urgency = null;
                        });
                      },
                      child: const Text('Clear All'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () {
                        widget.onApply({
                          'region': _region,
                          'cargo_type': _cargoType,
                          'vehicle_type': _vehicleType,
                          'urgency': _urgency,
                        });
                      },
                      child: const Text('Apply'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildDropdown(
    String label,
    List<String> items,
    String? value,
    ValueChanged<String?> onChanged,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: AppColors.gray700,
          ),
        ),
        const SizedBox(height: 6),
        DropdownButtonFormField<String>(
          value: value,
          hint: Text('All ${label}s'),
          items: items
              .map((e) => DropdownMenuItem(value: e, child: Text(e)))
              .toList(),
          onChanged: onChanged,
          decoration: const InputDecoration(isDense: true),
        ),
      ],
    );
  }
}
