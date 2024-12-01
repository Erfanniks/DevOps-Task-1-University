# tests/test_api.py
import requests
import time

def test_state_transitions():
    base_url = "http://localhost:8197"
    
    # Test initial state
    response = requests.get(f"{base_url}/state")
    assert response.status_code == 200
    assert response.text == "INIT"
    
    # Test state transition to RUNNING
    response = requests.put(f"{base_url}/state", data="RUNNING")
    assert response.status_code == 200
    assert response.text == "RUNNING"
    
    # Test request when running
    response = requests.get(f"{base_url}/request")
    assert response.status_code == 200
    
    # Test state transition to PAUSED
    response = requests.put(f"{base_url}/state", data="PAUSED")
    assert response.status_code == 200
    assert response.text == "PAUSED"
    
    # Verify run-log contains transitions
    response = requests.get(f"{base_url}/run-log")
    assert response.status_code == 200
    assert "INIT->RUNNING" in response.text
    assert "RUNNING->PAUSED" in response.text

if __name__ == "__main__":
    test_state_transitions()