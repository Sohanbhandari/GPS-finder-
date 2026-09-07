import 'package:flutter/foundation.dart';
import '../models/api_models.dart';
import '../models/auth_state.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';

/// Flutter State Controller managing Authentication State.
/// Business logic is strictly kept outside Flutter widgets.

class AuthController extends ChangeNotifier {
  final ApiService _apiService;
  final StorageService _storageService;

  AuthState _state = AuthState.unauthenticated();
  AuthState get state => _state;

  AuthController({
    required ApiService apiService,
    required StorageService storageService,
  })  : _apiService = apiService,
        _storageService = storageService;

  /// Check if user has an existing saved token on startup
  Future<void> checkInitialAuth() async {
    final savedToken = await _storageService.getToken();
    if (savedToken != null && savedToken.isNotEmpty) {
      _state = AuthState.authenticated(savedToken);
      notifyListeners();
    }
  }

  /// Perform secure login with email and password
  Future<bool> login(String email, String password) async {
    final cleanEmail = email.trim();
    if (cleanEmail.isEmpty || password.isEmpty) {
      _state = AuthState.failure('Email and password cannot be empty.');
      notifyListeners();
      return false;
    }

    _state = AuthState.authenticating();
    notifyListeners();

    try {
      final token = await _apiService.login(cleanEmail, password);
      await _storageService.saveToken(token);
      _state = AuthState.authenticated(token);
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _state = AuthState.failure(e.error.message);
      notifyListeners();
      return false;
    } catch (e) {
      _state = AuthState.failure('Unexpected authentication error occurred.');
      notifyListeners();
      return false;
    }
  }

  /// Handle 401 Unauthorized or manual logout: clear local token & return to login
  Future<void> logout() async {
    await _storageService.clearToken();
    _state = AuthState.unauthenticated();
    notifyListeners();
  }
}
