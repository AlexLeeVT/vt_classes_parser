from enum import StrEnum

import httpx
from urllib.parse import urlencode
import json

from pathlib import Path

class ProgramLevel(StrEnum):
    UNDERGRAD='coursetype_undergraduate'
    GRAD='coursetype_graduate'

class Discipline(StrEnum):
    ECE="ECE"
    CS="CS"

class Availability(StrEnum):
    OPEN="A"
    OPEN_OR_FULL="A,F,W"

class Query(StrEnum):
    SEARCH="search"
    DETAILS="details"

def fetch_courses(program_level: ProgramLevel, discipline: Discipline, availability: Availability):
    search_params = {
        "page": "fose",
        "route": Query.SEARCH,
        "stat": availability,
        program_level: "Y",
        "subject": discipline,
    }
    payload = {
        "other": {
            "srcdb": "202601"
        },
        "criteria": [
            {"field": "stat", "value": availability},
            {"field": program_level, "value": "Y"},
            {"field": "subject", "value": discipline},
        ],
    }
    url = "https://classes.vt.edu/api/"
    url_params = urlencode(search_params)

    with httpx.Client(timeout=10.0) as client:
        try:
            response = client.post(f"{url}?{url_params}",
                                   json=payload,)
            _ = response.raise_for_status()

            return json.dumps(response.json(), indent=2)

        except httpx.HTTPError as exc:
            print(f"HTTP Exception for {exc.request.url} - {exc}")
            return None




# outputfile = Path("output.txt")
# with outputfile.open("w") as f:
#     f.write(json)
# 
# courses = data["results"]
