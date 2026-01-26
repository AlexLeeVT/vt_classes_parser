from enum import StrEnum

import httpx
from urllib.parse import urlencode
import json

from pathlib import Path

class CourseType(StrEnum):
    undergraduate='coursetype_undergraduate',
    graduate='coursetype_graduate',

class SubjectType(StrEnum):
    ECE="ECE",
    CS="CS",

class CourseAvailability(StrEnum):
    OPEN_ONLY="A",
    OPEN_OR_FULL="A,F,W",

class RouteType(StrEnum):
    SEARCH="search",
    DETAILS="details",

url = "https://classes.vt.edu/api/"
search_params = {
    "page": "fose",
    "route": "search",
    "stat": CourseAvailability.OPEN_OR_FULL,
    CourseType.graduate: "Y",
    "subject": SubjectType.ECE,
}
url_params = urlencode(search_params)

payload = {
    "other": {
        "srcdb": "202601"
    },
    "criteria": [
        {"field": "stat", "value": CourseAvailability.OPEN_OR_FULL},
        {"field": CourseType.graduate, "value": "Y"},
        {"field": "subject", "value": "ECE"},
    ],
}

with httpx.Client(timeout=10.0) as client:
    response = client.post(f"{url}?{url_params}",
                           json=payload,)

    response.raise_for_status()
    data = response.json()
    json = json.dumps(data, indent=2)

outputfile = Path("output.txt")
with outputfile.open("w") as f:
    f.write(json)

courses = data["results"]
