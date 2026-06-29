"""Application entry point for the Task Management API."""

from config import Config
from db import init_db
from routes import route_request


class TestResponse:
    """Minimal response object compatible with Flask's test response API."""

    def __init__(self, body, status_code):
        """Store response body and status code."""
        self._body = body
        self.status_code = status_code

    def get_json(self):
        """Return the response JSON body."""
        return self._body


class TestClient:
    """Minimal test client for route-level API tests."""

    def open(self, path, method="GET", json=None, headers=None):
        """Dispatch a request through the route layer."""
        body, status_code = route_request(method, path, json, headers)
        return TestResponse(body, status_code)

    def get(self, path, headers=None):
        """Dispatch a GET request."""
        return self.open(path, "GET", headers=headers)

    def post(self, path, json=None, headers=None):
        """Dispatch a POST request."""
        return self.open(path, "POST", json=json, headers=headers)

    def put(self, path, json=None, headers=None):
        """Dispatch a PUT request."""
        return self.open(path, "PUT", json=json, headers=headers)

    def delete(self, path, headers=None):
        """Dispatch a DELETE request."""
        return self.open(path, "DELETE", headers=headers)


class Application:
    """Task Management API application container."""

    def __init__(self, config_object=Config):
        """Initialize application configuration."""
        self.config = config_object
        init_db(self)

    def test_client(self):
        """Return a local test client."""
        return TestClient()


def create_app(config_object=Config):
    """Create and configure an application instance."""
    return Application(config_object)


app = create_app()


if __name__ == "__main__":
    print("Task Management API is configured. Use a WSGI server with Flask installed for HTTP serving.")
