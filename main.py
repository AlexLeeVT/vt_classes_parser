from enum import StrEnum

import httpx
from urllib.parse import urlencode
import json

from pathlib import Path
from tomlkit import parse, document 
from tomlkit.toml_file import TOMLFile
import tomlkit

url = "https://classes.vt.edu/api/"

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
        code = course["code"]

        courses[crn] = {
            "code": code,
            "title": title,
        }

    return courses

def fetch_info(token: dict, code, crn):
    srcdb = 202601

    search_params = {
        "page": "fose",
        "route": Query.DETAILS,
    }
    url_params = urlencode(search_params)

    payload = {
        "group":f"code:{code}",
        "key":f"crn:{crn}",
        "srcdb":srcdb,
        "matched":"",#f"crn:{crn}"
    }
    payload = payload | token

    # create POST request
    with httpx.Client(timeout=10.0) as client:
        try:
            response = client.post(f"{url}?{url_params}",
                                   json=payload,)
            _ = response.raise_for_status()

            data = response.json()

            return data

        except httpx.HTTPError as exc:
            print(f"HTTP Exception for {exc.request.url} - {exc}")
            return None 

def is_valid_config(doc: tomlkit.TOMLDocument):
    """
    checks if config has all valid fields.
    Input
        - doc (TOMLFile): config file to validate
    return
        - True if config file is valid
        - False if config file 
    """
    if '_pers' not in doc:
        print("no pers field")
        return False
        
    if 'id' not in doc['_pers']:
        print("no id")
        return False

    if 'idProof' not in doc['_pers']:
        print("no idproof")
        return False
    return True

def generate_config(output: Path):
    id = input("id: ")
    idProof = input("idProof: ")

    token = parse(
f"""[_pers]
id="{id}"
idProof="{idProof}"
""")

    TOMLFile(output.as_posix()).write(token)
    return token

def get_personal_token():
    """
    Fetches file with token 
    return
        - dict: parsed personal token
    """

    token_file = Path("token_id")

    if not token_file.exists():
        return generate_config(token_file).unwrap()

    # read from file and ensure config is complete
    doc_file = TOMLFile(token_file.as_posix())
    doc = doc_file.read()
    if is_valid_config(doc):
        token_id = parse(
f"""[_pers]
id="{doc['_pers']['id']}"
idProof="{doc['_pers']['idProof']}"
"""
        )
    else:
        token_id = generate_config(token_file)

    doc_file.write(token_id)

    return token_id.unwrap()

# need clssnotes
if __name__ == "__main__":
    token = get_personal_token()
    fetched_data = fetch_courses(ProgramLevel.GRAD, Discipline.ECE, Availability.OPEN_OR_FULL)
    if not fetched_data:
        print(f"Error retrieving class data from classes.vt.edu")
        exit()

    results = fetched_data["results"]
    courses = parse_courses(results)
    for crn in courses:
        course = courses[crn]

        # change to fetch_details
        info = fetch_info(token, course['code'], crn)
        JSON_info = json.dumps(info, indent=2)
        with Path("output.txt").open("w") as f:
            f.write(JSON_info)

        break
