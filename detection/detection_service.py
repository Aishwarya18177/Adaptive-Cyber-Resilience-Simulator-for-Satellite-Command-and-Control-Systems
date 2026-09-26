import time
import requests

from detector import JammingDetector


SATELLITE_API = "http://127.0.0.1:8001"

detector = JammingDetector()


def get_detection():

    try:

        response = requests.get(
            f"{SATELLITE_API}/telemetry",
            timeout=1
        )

        response.raise_for_status()

        telemetry = response.json()

        result = detector.analyze(telemetry)

        return result

    except requests.RequestException:

        return {
            "detected": False,
            "type": "UNKNOWN",
            "confidence": 0,
            "severity": "UNKNOWN",
            "reason": "Satellite unavailable"
        }


if __name__ == "__main__":

    print("Detection Engine started...")

    while True:

        result = get_detection()

        print(result)

        time.sleep(1)