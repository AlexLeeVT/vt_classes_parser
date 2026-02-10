from enum import StrEnum

import httpx
from urllib.parse import urlencode
import json
from pandas import DataFrame

from pathlib import Path
from tomlkit import parse 
from tomlkit.toml_file import TOMLFile

from bs4 import BeautifulSoup
from rich.progress import (
        Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
)

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

blacklisted_courses = ['ECE 5904', 'ECE 5974', 'ECE 5994', 'ECE 7994']
def parse_courses(data: list):
    courses = []
    for course in data:
        title = course["title"]
        crn = course["crn"]
        code = course["code"]

        if code in blacklisted_courses:
            continue

        courses.append({ "crn": crn,
            "code": code,
            "title": title,
        })

    return courses

def fetch_info(crn, code, token: dict,):
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
            return {} 

def is_valid_config(id_data: dict):
    """
    checks if config has all valid fields.
    Input
        - doc (TOMLFile): config file to validate
    return
        - True if config file is valid
        - False if config file 
    """
    if '_pers' not in id_data:
        print("no pers field")
        return False
        
    if 'id' not in id_data['_pers']:
        print("no id")
        return False

    if 'idProof' not in id_data['_pers']:
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
"""
    )

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
    doc = doc_file.read().unwrap()

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

def get_schedule(meeting_times: str):
    """
    html parse to schedule
    Input
      - meeting_times (str): meeting time as html
    Output
      - list: meeting times as string list
    """
    soup = BeautifulSoup(meeting_times, 'html.parser')

    times = []
    for th in soup.select("div.meet"):
        meeting_text = str(th.find(string=True, recursive=False))
        times.append(meeting_text)

    room_html = soup.select_one("span[class^='meet-room']")
    room = "N/A"
    if room_html:
        room = room_html.get_text(strip=True).removeprefix("in ").strip()

    return times, room 

def get_comment(comment: str):
    soup = BeautifulSoup(comment, 'html.parser')
    for p in soup.find_all("p"):
        p.unwrap()

    return str(soup)

def parse_info(crn, code):
    # change to fetch_details
    info = fetch_info(crn, code, token)
    JSON_info = json.dumps(info, indent=2)
    with Path("output.txt").open("w") as f:
        f.write(JSON_info)

    modality = info['modality']
    meeting_times, room = get_schedule(info['meeting_html'])
    comments = get_comment(info['clssnotes'])
    campus = info['camp_html']

    return (modality, meeting_times, room, comments, campus)

# need clssnotes
if __name__ == "__main__":
    with Progress (
        TextColumn("[bold yellow]{task.fields[stage]}", justify="left"),
        BarColumn(bar_width=40),
        TaskProgressColumn(show_speed=True),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task(stage="Getting Courses...", total = 0, description="")
        token = get_personal_token()
        fetched_data = fetch_courses(
            ProgramLevel.GRAD, 
            Discipline.ECE, 
            Availability.OPEN_OR_FULL
        )

        if not fetched_data:
            print(f"Error retrieving class data from classes.vt.edu")
            exit()

        results = fetched_data["results"]
        courses = parse_courses(results)
        progress.update(task, total=len(courses))

        # multithread process, only allow 5 at a time to do work to reduce load on vt server
        for course in courses:
            crn = course['crn']
            code = course['code']

            progress.update(task, stage=f"[bold cyan]Fetching course: {code}")
            modality, meeting_times, room, comments, campus = parse_info(crn,code)

            # add details to course
            course['campus'] = campus
            course['modality'] = modality
            course['room'] = room
            course['meeting_times'] = meeting_times
            course['comment'] = comments

            progress.update(task, advance=1)

        progress.update(task, stage="Output to \"courses.csv\"")

        data = DataFrame(courses).sort_values(by=['crn'])
        try:
            data.to_csv("courses.csv", index=False)
        except:
            print("error occured while attempting to write courses to \"courses.csv\"")

        progress.update(task, stage="[bold green]Complete")
