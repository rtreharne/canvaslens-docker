from __future__ import absolute_import, unicode_literals
from canvasapi import Canvas
from celery import shared_task
from .canvas import *
import logging
log = logging.getLogger('lens')
from .models import Term, TaskDetail


@shared_task()
def report(
        API_URL, 
        API_TOKEN,
        subject,
        term_code,
        course_codes,
        additional_recipients
    ):
    print(API_URL, 
        API_TOKEN,
        subject,
        term_code,
        course_codes,
        additional_recipients)
    
    # Create canvasapi instance
    canvas = Canvas(API_URL, API_TOKEN)

    # User ID
    user_id = canvas.get_current_user().id

    # Get courses from subject and course_codes
    courses = []

    print(subject, course_codes)

    if subject != "":
        courses += get_courses_from_prefix(subject, term_code, canvas)

    if course_codes != "":
        courses += get_courses_from_course_codes(course_codes, canvas)

    if len(courses) == 0:
        return "No courses. I'm done."

    # Generate report
    data = generate_data(courses)

    # Save data
    fname, fpath = create_file(data, user_id)

    # Send report
    folder_id = get_conversation_attachments_folder_id(user_id, API_URL, API_TOKEN)
    response = upload_file(folder_id, fname, fpath, "conversation_attachments", API_URL, API_TOKEN)

    body = """Attached is your Canvas Lens report! 
        Please do not reply to this email.      
    """

    if response:
        send_message(
            canvas,
            recipients=[canvas.get_current_user().id],
            subject="Canvas Lens Report {}".format(fname),
            body=body,
            attachment_ids=[response.json()["id"],]
        )

    return "Done."
