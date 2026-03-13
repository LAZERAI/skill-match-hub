import json
import os
from datetime import datetime

STATUS_FILE = "resume_status.json"


def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_status(status_data):
    with open(STATUS_FILE, "w") as f:
        json.dump(status_data, f, indent=2)

def mark_as_hired(filename):
    status_data = load_status()

    status_data[filename.strip()] = {
        "status": "hired",
        "hired_date": datetime.now().strftime("%Y-%m-%d")
    }

    save_status(status_data)


def is_hired(filename):
    status_data = load_status()
    return filename in status_data and status_data[filename]["status"] == "hired"
