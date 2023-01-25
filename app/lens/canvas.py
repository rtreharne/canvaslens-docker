from canvasapi import Canvas
import requests
from datetime import datetime
import csv
from io import StringIO


def get_period(canvas_dt):
    dt = datetime.strptime(canvas_dt, "%Y-%m-%dT%H:%M:%SZ")
    month = dt.month

    if 1 < month <= 7:
        return "SEMESTER_2"
    elif 7 < month <= 9:
        return "RESIT"
    
    return "SEMESTER_1"

def get_real_assignments(course):
    return [x for x in course.get_assignments() if
            x.due_at is not None and not x.omit_from_final_grade and x.workflow_state == 'published' and x.has_submitted_submissions]


def extract_submission_info(sub, course):
    try:
        user = sub.user
        sis_user_id = user["sis_user_id"]
        info = get_user_id_and_username_from_login(sis_user_id)
    except AttributeError:
        print("Couldn't find a user", sub.__dict__)
        info = None

    if info is not None:

        # Try and get the marker
        author = ""
        submission_comments = sub.submission_comments
        if len(submission_comments) > 0:
            for comment in submission_comments:
                if comment["author_id"] != info["user_id"]:
                    author = comment["author_name"]

        # Get period (i.e. S1, S1, Resit (R))
        sub_info = {"student_id": info["user_id"],
                    "username": info["username"],
                    "name": user["sortable_name"],
                    "email": user["login_id"],
                    "course": course.sis_course_id,
                    "assignment_name": sub.assignment["name"],
                    "assignment_type": sub.submission_type,
                    "period": get_period(sub.assignment["due_at"]),
                    "marker_name": author,
                    "anonymous": sub.assignment["anonymous_grading"],
                    "score_as_percentage": get_score(sub),
                    "status": sub.workflow_state,
                    "days_late": seconds_to_days(sub.seconds_late),
                    "due_at": sub.assignment["due_at"],
                    "submitted_at": sub.submitted_at
                    }
        return sub_info


def seconds_to_days(seconds):
    return seconds / (3600 * 24)


def get_user_id_and_username_from_login(login):
    try:
        int(login[:9])
        return {"user_id": login[:9], "username": login[9:]}
    except:
        return {"user_id": "test", "username": "test"}


def get_score(sub, deduction=False):
    try:
        score = sub.score * 100 / (sub.assignment["points_possible"])
        return round(score, 2)
    except:
        if deduction:
            return 0
        if sub.workflow_state == "submitted":
            return "Needs Grading"
        return "A"

def generate_data(courses):
    rows = []
    for course in courses:
        assignments = get_real_assignments(course)
        for a in assignments:
            print(a.name)
            if a.has_submitted_submissions:
                submissions = [x for x in a.get_submissions(include=["user", "assignment", "submission_comments"])]

                for sub in submissions:
                    sub_info = extract_submission_info(sub, course)
                    if sub_info is not None:
                        rows.append(sub_info)
            else:
                print(a.name, "has no submissions yet")

    return rows

def get_courses_from_prefix(prefix, term, canvas):
    courses = []
    for i in range(100, 1000):
        print(i)
        try:
            course = canvas.get_course("{}{}-{}".format(prefix.upper(), str(i), str(term)), use_sis_id=True)
            courses.append(course)
        except:
            continue
    return courses

def create_file(rows, user_id):
    fname = datetime.strftime(datetime.now(), "%Y%m%dT%H%M%S") + "_{}_canvas_lens.csv".format(user_id)
    #fpath = "lens/reports/{}".format(fname)

    keys = rows[0].keys()

    output = StringIO()
    writer = csv.DictWriter(output, keys)
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    return fname, output


def maybe_make_int(s):
    try:
        return(int(s))
    except:
        return(s.upper())

def get_courses_from_course_codes(course_codes_string, canvas):
    
    # Remove whitespace from string
    course_codes_string = ''.join(course_codes_string.split())

    # Split by ',' and make integers int
    course_codes = [maybe_make_int(x) for x in course_codes_string.split(",")]

    courses = []

    for course in course_codes:
        if isinstance(course, int):
            try:
                courses.append(canvas.get_course(course))
            except:
                continue
        else:
            try:
                courses.append(canvas.get_course(course, use_sis_id=True))
            except:
                continue
    
    return courses


def send_message(canvas, recipients=[], subject=None, body=None, attachment_ids=[]):
    canvas.create_conversation(
        recipients=recipients,
        subject=subject,
        body=body,
        attachment_ids=attachment_ids,
        force_new=True,
        scope="unread",
    )

def get_conversation_attachments_folder_id(user_id, API_URL, API_TOKEN):
    url = API_URL + "/api/v1/users/{}/folders".format(str(user_id))
    headers = {'Authorization': 'Bearer ' + API_TOKEN}

    r = requests.get(url, headers=headers)

    for item in r.json():
        if "conversation attachments" in item["full_name"]:
            return item["id"]

def upload_file(folder_id, fname, file, dname, API_URL, API_TOKEN):

    url = API_URL + "/api/v1/folders/{}/files".format(str(folder_id))
    headers = {'Authorization': 'Bearer ' + API_TOKEN}
    data = {
        'name': fname,
        'content_type': 'text/plain',
        'parent_folder': dname,
    }

    create = requests.post(url, headers=headers, data=data)
    confirm_url = create.json()["upload_url"]
    file.name=fname
    files = {
        'file': file,
    }

    confirm = requests.post(confirm_url, files=files)

    return confirm

if __name__ == "__main__":
    API_URL = "https://canvas.liverpool.ac.uk"
    API_TOKEN = "15502~GM7R7XvK6OA5n0toGFYNWmpxgeYnK7jOulLg4rNAWvjkNeRnYngv1x40u6oFAci5"

    canvas = Canvas(API_URL, API_TOKEN)

    user_id = canvas.get_current_user().id

    course_codes_string = "LIFE211-202223"
    #courses = get_courses_from_prefix("LIFE", "202223", canvas) + get_courses_from_course_codes(course_codes_string, canvas)
    courses = get_courses_from_course_codes(course_codes_string, canvas)

    data = generate_data(courses)
    
    create_file(data, user_id)


    
    
