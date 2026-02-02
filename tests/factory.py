

def test_client(client):
    response = client.get("healthz")
    assert response.json == {"status": "healthy", "service": "api-server"}