import 'package:flutter/material.dart';
import '../controllers/auth_controller.dart';
import '../controllers/tracking_controller.dart';
import '../models/api_models.dart';
import '../models/tracking_state.dart';
import 'widgets/vehicle_map_view.dart';

/// Interview-Focused Tracking Screen displaying real-time assignment, vehicle status, and location history.

class TrackingScreen extends StatefulWidget {
  final AuthController authController;
  final TrackingController trackingController;

  const TrackingScreen({
    Key? key,
    required this.authController,
    required this.trackingController,
  }) : super(key: key);

  @override
  State<TrackingScreen> createState() => _TrackingScreenState();
}

class _TrackingScreenState extends State<TrackingScreen> {
  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  @override
  void dispose() {
    widget.trackingController.stopPolling();
    super.dispose();
  }

  void _fetchData() {
    final token = widget.authController.state.token;
    if (token != null) {
      widget.trackingController.loadTrackingData(token).then((_) {
        if (mounted) {
          widget.trackingController.startPolling(token);
        }
      });
    }
  }

  Color _getStatusColor(String status) {
    switch (status.toUpperCase()) {
      case 'ACTIVE':
        return const Color(0xFF16A34A); // Green
      case 'OFFLINE':
        return const Color(0xFFD97706); // Amber
      default:
        return const Color(0xFF64748B); // Slate/Grey
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text('Live Tracking Dashboard', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF2563EB),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Data',
            onPressed: _fetchData,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Log Out',
            onPressed: () => widget.authController.logout(),
          ),
        ],
      ),
      body: AnimatedBuilder(
        animation: widget.trackingController,
        builder: (context, _) {
          final state = widget.trackingController.state;

          if (state.isLoading) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Loading telemetry and assignment details...', style: TextStyle(color: Color(0xFF64748B))),
                ],
              ),
            );
          }

          if (state.hasNoAssignment) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.assignment_late_outlined, size: 64, color: Color(0xFF94A3B8)),
                    const SizedBox(height: 16),
                    const Text(
                      'No Active Vehicle Assignment',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'You currently do not have an active route or vehicle assigned to your account.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Color(0xFF64748B)),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: _fetchData,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Check Again'),
                    ),
                  ],
                ),
              ),
            );
          }

          if (state.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.cloud_off, size: 64, color: Color(0xFFEF4444)),
                    const SizedBox(height: 16),
                    const Text(
                      'Connection / API Failure',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      state.errorMessage ?? 'An error occurred while communicating with backend.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Color(0xFF64748B)),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: _fetchData,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Retry Connection'),
                    ),
                  ],
                ),
              ),
            );
          }

          if (state.isLoaded) {
            final assignment = state.assignment!;
            final vehicle = state.vehicle!;
            final location = state.location!;
            final history = state.history;

            return RefreshIndicator(
              onRefresh: () async => _fetchData(),
              child: ListView(
                padding: const EdgeInsets.all(16.0),
                children: [
                  // 0. Live Google Maps Visualization Layer
                  VehicleMapView(
                    stops: assignment.route.stops,
                    location: location,
                    status: location.status,
                    vehicleCode: location.vehicleCode,
                  ),
                  const SizedBox(height: 16),

                  // 1. Vehicle Telemetry Location Card
                  Card(
                    elevation: 2,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Vehicle ${location.vehicleCode}',
                                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: _getStatusColor(location.status).withOpacity(0.12),
                                  borderRadius: BorderRadius.circular(20),
                                  border: Border.all(color: _getStatusColor(location.status)),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Container(
                                      width: 8,
                                      height: 8,
                                      decoration: BoxDecoration(
                                        color: _getStatusColor(location.status),
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      location.status,
                                      style: TextStyle(
                                        color: _getStatusColor(location.status),
                                        fontWeight: FontWeight.bold,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          const Divider(height: 24),
                          Row(
                            children: [
                              Expanded(
                                child: _buildMetricTile(
                                  icon: Icons.my_location,
                                  label: 'Latitude',
                                  value: location.latitude != null ? location.latitude!.toStringAsFixed(6) : 'N/A',
                                ),
                              ),
                              Expanded(
                                child: _buildMetricTile(
                                  icon: Icons.location_on_outlined,
                                  label: 'Longitude',
                                  value: location.longitude != null ? location.longitude!.toStringAsFixed(6) : 'N/A',
                                ),
                              ),
                              Expanded(
                                child: _buildMetricTile(
                                  icon: Icons.speed,
                                  label: 'Speed',
                                  value: location.speed != null ? '${location.speed!.toStringAsFixed(1)} km/h' : '0.0 km/h',
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // 2. Active Route & Sequence Stops Card
                  Card(
                    elevation: 2,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAlignment.start,
                        children: [
                          Text(
                            'Route: ${assignment.route.name} (${assignment.route.code})',
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            assignment.route.description,
                            style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                          ),
                          const Divider(height: 24),
                          const Text('Sequence Stops:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                          const SizedBox(height: 8),
                          ...assignment.route.stops.map((stop) {
                            return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 4.0),
                              child: Row(
                                children: [
                                  CircleAvatar(
                                    radius: 12,
                                    backgroundColor: const Color(0xFFEFF6FF),
                                    child: Text(
                                      '${stop.sequence}',
                                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF2563EB)),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Text(stop.name, style: const TextStyle(fontWeight: FontWeight.w500)),
                                  ),
                                  Text(
                                    '${stop.latitude.toStringAsFixed(4)}, ${stop.longitude.toStringAsFixed(4)}',
                                    style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8)),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // 3. Historical Telemetry Log List
                  Card(
                    elevation: 2,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text('Historical Telemetry Log', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                              Text('${history.length} points', style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                            ],
                          ),
                          const Divider(height: 24),
                          if (history.isEmpty)
                            const Padding(
                              padding: EdgeInsets.all(16.0),
                              child: Text('No historical GPS points recorded yet.', style: TextStyle(color: Color(0xFF94A3B8))),
                            )
                          else
                            ListView.separated(
                              shrinkWrap: true,
                              physics: const NeverScrollableScrollPhysics(),
                              itemCount: history.length > 10 ? 10 : history.length,
                              separatorBuilder: (_, __) => const Divider(height: 12),
                              itemBuilder: (context, index) {
                                final point = history[index];
                                return Row(
                                  children: [
                                    const Icon(Icons.history, size: 16, color: Color(0xFF64748B)),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAlignment.start,
                                        children: [
                                          Text(
                                            '${point.latitude.toStringAsFixed(6)}, ${point.longitude.toStringAsFixed(6)}',
                                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                                          ),
                                          Text(
                                            'Recorded: ${point.recordedAt}',
                                            style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8)),
                                          ),
                                        ],
                                      ),
                                    ),
                                    Text(
                                      '${point.speed.toStringAsFixed(1)} km/h',
                                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF2563EB)),
                                    ),
                                  ],
                                );
                              },
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            );
          }

          return const SizedBox.shrink();
        },
      ),
    );
  }

  Widget _buildMetricTile({required IconData icon, required String label, required String value}) {
    return Column(
      children: [
        Icon(icon, size: 20, color: const Color(0xFF2563EB)),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
        const SizedBox(height: 2),
        Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
      ],
    );
  }
}
