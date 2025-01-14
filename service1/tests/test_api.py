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
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.text == "INIT", f"Expected 'INIT', got '{response.text}'"

    # Transition to RUNNING
    response = requests.put(f"{BASE_URL}/state", data="RUNNING", headers={"Content-Type": "text/plain"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.text == "RUNNING", f"Expected 'RUNNING', got '{response.text}'"

    # Test /request while RUNNING
    response = requests.get(f"{BASE_URL}/request")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    # Transition to PAUSED
    response = requests.put(f"{BASE_URL}/state", data="PAUSED", headers={"Content-Type": "text/plain"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.text == "PAUSED", f"Expected 'PAUSED', got '{response.text}'"

    # Test /request while PAUSED
    response = requests.get(f"{BASE_URL}/request")
    assert response.status_code == 503, f"Expected 503, got {response.status_code}"

    # Verify log contents
    response = requests.get(f"{BASE_URL}/run-log")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    log_text = response.text
    assert "INIT->RUNNING" in log_text, f"'INIT->RUNNING' not in log: {log_text}"
    assert "RUNNING->PAUSED" in log_text, f"'RUNNING->PAUSED' not in log: {log_text}"

if __name__ == "__main__":
    wait_for_service()
    time.sleep(5)  # Wait briefly to ensure services stabilize
    test_state_transitions()
    print("All tests passed!")
