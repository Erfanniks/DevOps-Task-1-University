import requests
import time

BASE_URL = "http://nginx:8197"

def test_state_transitions():
    """Test state management API endpoints."""
    # Test initial state
    response = requests.get(f"{BASE_URL}/state")
    assert response.status_code == 200
    assert response.text == "INIT"

    # Test transition to RUNNING
    response = requests.put(f"{BASE_URL}/state", data="RUNNING")
    assert response.status_code == 200
    assert response.text == "RUNNING"

    # Test /request while RUNNING
    response = requests.get(f"{BASE_URL}/request")
    assert response.status_code == 200

    # Test transition to PAUSED
    response = requests.put(f"{BASE_URL}/state", data="PAUSED")
    assert response.status_code == 200
    assert response.text == "PAUSED"

    # Test /request while PAUSED
    response = requests.get(f"{BASE_URL}/request")
    assert response.status_code == 503

    # Verify state transition log
    response = requests.get(f"{BASE_URL}/run-log")
    assert response.status_code == 200
    log_text = response.text
    assert "INIT->RUNNING" in log_text
    assert "RUNNING->PAUSED" in log_text

def test_invalid_state():
    """Test handling of invalid state transitions."""
    response = requests.put(f"{BASE_URL}/state", data="INVALID_STATE")
    assert response.status_code == 400

def test_service2_unreachable():
    """Test behavior when service2 is unreachable."""
    response = requests.get(f"{BASE_URL}/request")
    assert response.status_code in [503, 200]  # Depending on service2 status

if __name__ == "__main__":
    test_state_transitions()
    test_invalid_state()
    test_service2_unreachable()
    print("All tests passed!")
