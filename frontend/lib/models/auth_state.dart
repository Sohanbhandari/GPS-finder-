/// Authentication State Model representing Login Lifecycle.

enum AuthStatus {
  unauthenticated,
  authenticating,
  authenticated,
  failure,
}

class AuthState {
  final AuthStatus status;
  final String? token;
  final String? errorMessage;

  const AuthState({
    required this.status,
    this.token,
    this.errorMessage,
  });

  factory AuthState.unauthenticated() {
    return const AuthState(status: AuthStatus.unauthenticated);
  }

  factory AuthState.authenticating() {
    return const AuthState(status: AuthStatus.authenticating);
  }

  factory AuthState.authenticated(String token) {
    return AuthState(status: AuthStatus.authenticated, token: token);
  }

  factory AuthState.failure(String errorMessage) {
    return AuthState(status: AuthStatus.failure, errorMessage: errorMessage);
  }

  bool get isAuthenticated => status == AuthStatus.authenticated && token != null;
  bool get isAuthenticating => status == AuthStatus.authenticating;
}
