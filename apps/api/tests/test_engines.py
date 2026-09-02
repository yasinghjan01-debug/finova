import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "FINOVA"
    assert len(data["engines"]) == 5

def test_dashboard_metrics():
    response = client.get("/api/v1/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "system_health" in data
    assert data["summary"]["to_receive"] >= 0

def test_find_my_money_search():
    response = client.post("/api/v1/memory/find-my-money", json={"query": "Rahul ₹20,000"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] >= 1
    assert data["matches"][0]["amount"] == 20000.0

def test_relationships_list():
    response = client.get("/api/v1/people")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    names = [p["canonical_name"] for p in data]
    assert "Rahul Sharma" in names

def test_relationship_card():
    response = client.get("/api/v1/people/person_rahul_001")
    assert response.status_code == 200
    data = response.json()
    assert data["canonical_name"] == "Rahul Sharma"
    assert "identities" in data
    assert len(data["timeline"]) >= 1

def test_honest_exceptions():
    response = client.get("/api/v1/reconciliation/honest-exceptions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_receivables_at_risk():
    response = client.get("/api/v1/recovery/at-risk")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_assistant_query_evidence():
    response = client.post("/api/v1/assistant/query", json={"message": "How much money does Rahul owe me?"})
    assert response.status_code == 200
    data = response.json()
    assert "Rahul Sharma" in data["answer"]
    assert len(data["evidence"]) >= 1
