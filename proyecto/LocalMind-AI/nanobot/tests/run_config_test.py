import asyncio
from unittest.mock import MagicMock
from aiohttp.test_utils import TestClient, TestServer
from nanobot.api.server import create_app

async def main():
    print("Running Configuration API Endpoint Test inside Container...")
    agent = MagicMock()
    app = create_app(agent, model_name="test-model", request_timeout=10.0)
    
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    
    try:
        # Test 1: GET /localmind/config
        print("Testing GET /localmind/config...")
        resp = await client.get("/localmind/config")
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = await resp.json()
        assert "backend_type" in data
        assert "selected_model" in data
        assert "apiKey" in data
        assert "enable_engram" in data
        assert "ollama" in data
        assert "mlx" in data
        print("GET test passed!")

        # Test 2: POST /localmind/config (validation error)
        print("Testing POST /localmind/config (validation)...")
        resp = await client.post("/localmind/config", json={
            "backend_type": "mlx",
            "apiKey": "test-key"
        })
        assert resp.status == 400, f"Expected 400, got {resp.status}"
        data = await resp.json()
        assert "error" in data
        print("POST validation test passed!")
        
        print("All API tests passed successfully!")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
