import httpx
from urllib.parse import urlencode
import json
from pathlib import Path

from enum import StrEnum, IntEnum

class CourseType(StrEnum):
    undergraduate='coursetype_undergraduate',
    graduate='coursetype_graduate',

class SubjectType(StrEnum):
    ECE='ECE',
    CS='CS',

class CourseAvailability(StrEnum):
    OPEN_ONLY="A",
    OPEN_OR_FULL="A%2CF%2CW",

url = "https://classes.vt.edu/api/"
params = {
    "page": "fose",
    "route": "search",
    "stat": CourseAvailability.OPEN_OR_FULL,
    CourseType.graduate: "Y",
    "subject": SubjectType.ECE,
}
url_params = urlencode(params)

payload = {
    "other": {
        "srcdb": "202601"
    },
    "criteria": [
        {"field": "stat", "value": "A"},
        {"field": "coursetype_graduate", "value": "Y"},
        {"field": "subject", "value": "ECE"},
    ],
}

with httpx.Client(timeout=10.0) as client:
    response = client.post(f"{url}?{url_params}",
                           json=payload,)

    response.raise_for_status()
    json = json.dumps(response.json(), indent=2)

outputfile = Path("output.txt")
with outputfile.open("w") as f:
    f.write(json)
