/// Local Storage Service Abstraction for persisting security access token.

abstract class StorageService {
  Future<void> saveToken(String token);
  Future<String?> getToken();
  Future<void> clearToken();
}

class InMemoryStorageService implements StorageService {
  String? _token;

  @override
  Future<void> saveToken(String token) async {
    _token = token;
  }

  @override
  Future<String?> getToken() async {
    return _token;
  }

  @override
  Future<void> clearToken() async {
    _token = null;
  }
}
