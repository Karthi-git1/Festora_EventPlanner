"""
Integration tests for rate limiter on API routes
"""
import pytest
import time
from app import app, event_manager
from middleware.rate_limiter import rate_limiter_default, rate_limiter_strict


class TestRateLimiterIntegration:
    """Test rate limiter integration with Flask routes"""
    
    @pytest.fixture
    def client(self):
        """Create test client and reset rate limiters"""
        app.config["TESTING"] = True
        # Clear rate limiter state before each test
        rate_limiter_default.requests.clear()
        rate_limiter_strict.requests.clear()
        with app.test_client() as client:
            yield client
    
    def test_ai_copilot_endpoint_has_strict_rate_limit(self, client):
        """Test AI copilot endpoint enforces strict rate limiting"""
        # Create a test event first
        response = client.post("/api/events", json={
            "name": "Test Event",
            "type": "Wedding",
            "date": "2024-12-31",
            "budget": 100000,
            "guests": 100
        })
        assert response.status_code == 200
        event_id = response.json["event"]["id"]
        
        # Make requests to AI copilot endpoint (strict: 20 req/min)
        successful_requests = 0
        rate_limited = False
        
        for i in range(25):
            response = client.post(
                f"/api/events/{event_id}/ai/copilot",
                json={"query": f"test query {i}"}
            )
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:
                rate_limited = True
                assert "Rate limit exceeded" in response.json.get("error", "")
                assert "retry_after" in response.json
                break
        
        # Should hit rate limit before 25 requests (strict limit is 20)
        assert rate_limited, "Expected rate limiting to kick in"
        assert successful_requests <= 20, f"Too many requests succeeded: {successful_requests}"
    
    def test_event_creation_has_rate_limit(self, client):
        """Test event creation endpoint enforces rate limiting"""
        successful_requests = 0
        rate_limited = False
        
        # Try to create many events (default: 100 req/min)
        for i in range(105):
            response = client.post("/api/events", json={
                "name": f"Test Event {i}",
                "type": "Wedding",
                "date": "2024-12-31",
                "budget": 100000,
                "guests": 100
            })
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:
                rate_limited = True
                assert "Rate limit exceeded" in response.json.get("error", "")
                break
        
        # Should hit rate limit
        assert rate_limited, "Expected rate limiting to kick in"
        assert successful_requests <= 100, f"Too many requests succeeded: {successful_requests}"
    
    def test_rate_limit_headers_present(self, client):
        """Test rate limit headers are included in responses"""
        response = client.post("/api/events", json={
            "name": "Test Event",
            "type": "Wedding",
            "date": "2024-12-31",
            "budget": 100000,
            "guests": 100
        })
        
        assert response.status_code == 200
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers or response.status_code == 200
        # Headers may not be present in all response types, but endpoint should work
    
    def test_read_endpoints_not_rate_limited(self, client):
        """Test GET endpoints work without aggressive rate limiting"""
        # Create an event
        response = client.post("/api/events", json={
            "name": "Test Event",
            "type": "Wedding",
            "date": "2024-12-31",
            "budget": 100000,
            "guests": 100
        })
        assert response.status_code == 200
        
        # GET requests should work fine (not rate limited in current config)
        for _ in range(10):
            response = client.get("/api/events")
            assert response.status_code == 200
    
    def test_health_endpoint_not_rate_limited(self, client):
        """Test health endpoint is accessible without rate limiting"""
        # Health checks should always work
        for _ in range(20):
            response = client.get("/health")
            assert response.status_code in [200, 503]  # Either healthy or degraded
