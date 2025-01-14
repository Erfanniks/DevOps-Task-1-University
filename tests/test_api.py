import requests
import time

BASE_URL = "http://nginx:80"

def wait_for_service():
    """Wait for the nginx service to be ready."""
    for _ in range(10):  # Retry 10 times
        try:
            response = requests.get(f"{BASE_URL}/state")
            if response.status_code == 200:
                print("Service is ready.")
                return
        except requests.ConnectionError:
            pass
        print("Waiting for service...")
        time.sleep(3)
    raise Exception("Service not ready after retries.")

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

if __name__ == "__main__":
    wait_for_service()
    test_state_transitions()
    print("All tests passed!")
