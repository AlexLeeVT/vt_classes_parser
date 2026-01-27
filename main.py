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

            return response.json()

        except httpx.HTTPError as exc:
            print(f"HTTP Exception for {exc.request.url} - {exc}")
            return None 

def parse_courses(data: list):
    courses = {} 
    for course in data:
        title = course["title"]
        crn = course["crn"]

        if title not in courses:
            courses[title] = {
                "code": course["code"],
                "crn":[crn]
            }
        else:
            courses[title]["crn"] += [crn]

    return courses

if __name__ == "__main__":
    fetched_data = fetch_courses(ProgramLevel.GRAD, Discipline.ECE, Availability.OPEN_OR_FULL)
    if not fetched_data:
        print(f"Error retrieving class data from classes.vt.edu")
        exit()

    results = fetched_data["results"]
    courses = parse_courses(results)
    for course in courses:
        print(f"{course}, {courses[course]["code"]}, crn: {courses[course]["crn"] if len(courses[course]["crn"]) < 30 else courses[course]["crn"][:5]}")
#    JSON_ECECourses = json.dumps(fetched_data, indent=2)
#    with Path("output.txt").open("w") as f:
#        f.write(JSON_ECECourses)
