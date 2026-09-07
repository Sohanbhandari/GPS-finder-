import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../../models/api_models.dart';

/// Pure Presentational Map View Component for displaying Google Maps,
/// ordered route stop polylines, and real-time vehicle telemetry markers.
///
/// Strictly isolated from network and auth logic. Uses ONLY backend telemetry data.

class VehicleMapView extends StatefulWidget {
  final List<RouteStop> stops;
  final VehicleLocation? location;
  final String status;
  final String vehicleCode;

  const VehicleMapView({
    Key? key,
    required this.stops,
    required this.location,
    required this.status,
    required this.vehicleCode,
  }) : super(key: key);

  @override
  State<VehicleMapView> createState() => _VehicleMapViewState();
}

class _VehicleMapViewState extends State<VehicleMapView> {
  GoogleMapController? _mapController;

  @override
  void didUpdateWidget(VehicleMapView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (_mapController != null && _hasValidLocation(widget.location)) {
      _mapController!.animateCamera(
        CameraUpdate.newLatLng(
          LatLng(widget.location!.latitude!, widget.location!.longitude!),
        ),
      );
    }
  }

  bool _hasValidLocation(VehicleLocation? loc) {
    return loc != null &&
        loc.latitude != null &&
        loc.longitude != null &&
        widget.status.toUpperCase() != 'UNKNOWN';
  }

  List<RouteStop> get _sortedStops {
    final list = List<RouteStop>.from(widget.stops);
    list.sort((a, b) => a.sequence.compareTo(b.sequence));
    return list;
  }

  Set<Polyline> _buildPolylines() {
    final sorted = _sortedStops;
    if (sorted.length < 2) return {};

    final points = sorted.map((s) => LatLng(s.latitude, s.longitude)).toList();

    return {
      Polyline(
        polylineId: const PolylineId('route_polyline'),
        points: points,
        color: const Color(0xFF2563EB),
        width: 5,
        geodesic: true,
      ),
    };
  }

  Set<Marker> _buildMarkers() {
    final markers = <Marker>{};
    final sorted = _sortedStops;

    // 1. Route Stop Markers
    for (final stop in sorted) {
      markers.add(
        Marker(
          markerId: MarkerId('stop_${stop.id}'),
          position: LatLng(stop.latitude, stop.longitude),
          infoWindow: InfoWindow(
            title: 'Stop ${stop.sequence}: ${stop.name}',
            snippet: 'Sequence Order ${stop.sequence}',
          ),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueAzure),
        ),
      );
    }

    // 2. Real-Time Vehicle Telemetry Marker (if coordinates present)
    if (_hasValidLocation(widget.location)) {
      final loc = widget.location!;
      double hue;
      switch (widget.status.toUpperCase()) {
        case 'ACTIVE':
          hue = BitmapDescriptor.hueGreen;
          break;
        case 'OFFLINE':
          hue = BitmapDescriptor.hueOrange;
          break;
        default:
          hue = BitmapDescriptor.hueViolet;
      }

      markers.add(
        Marker(
          markerId: MarkerId('vehicle_${widget.vehicleCode}'),
          position: LatLng(loc.latitude!, loc.longitude!),
          infoWindow: InfoWindow(
            title: 'Vehicle ${widget.vehicleCode}',
            snippet: 'Status: ${widget.status} | Speed: ${(loc.speed ?? 0).toStringAsFixed(1)} km/h',
          ),
          icon: BitmapDescriptor.defaultMarkerWithHue(hue),
          zIndex: 2.0,
        ),
      );
    }

    return markers;
  }

  LatLng _getInitialTarget() {
    if (_hasValidLocation(widget.location)) {
      return LatLng(widget.location!.latitude!, widget.location!.longitude!);
    }
    if (widget.stops.isNotEmpty) {
      return LatLng(widget.stops.first.latitude, widget.stops.first.longitude);
    }
    return const LatLng(27.7172, 85.3240); // Default fallback coordinates (Kathmandu)
  }

  @override
  Widget build(BuildContext context) {
    final initialTarget = _getInitialTarget();
    final hasLoc = _hasValidLocation(widget.location);

    return Container(
      height: 320,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Stack(
        children: [
          GoogleMap(
            initialCameraPosition: CameraPosition(
              target: initialTarget,
              zoom: 14.0,
            ),
            onMapCreated: (controller) => _mapController = controller,
            polylines: _buildPolylines(),
            markers: _buildMarkers(),
            myLocationEnabled: false, // Strict Rule: Never use phone/device GPS
            myLocationButtonEnabled: false,
            zoomControlsEnabled: true,
            mapToolbarEnabled: false,
          ),

          // Missing Location Overlay Banner
          if (!hasLoc)
            Positioned(
              top: 12,
              left: 12,
              right: 12,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFFBEB),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFFFDE68A)),
                  boxShadow: const [
                    BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2)),
                  ],
                ),
                child: Row(
                  children: [
                    const Icon(Icons.warning_amber_rounded, color: Color(0xFFD97706), size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        widget.status.toUpperCase() == 'UNKNOWN'
                            ? 'No Telemetry Received: Vehicle signal pending.'
                            : 'Location Pending: Vehicle position update required.',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF92400E)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
