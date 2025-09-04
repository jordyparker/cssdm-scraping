import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from services.email_service import EmailService

BASE_DIR = Path(__file__).resolve().parent

# Get the website page of the given program as html content and parse it using beautiful soup
def get_program_admission_page(school_id, program_id):
    response = requests.get(
        f"{os.getenv('BASE_URL')}?ecoleID={school_id}&programmeID={program_id}",
        verify=False
    )

    return BeautifulSoup(response.content, "html.parser")

# Find sessions open for registration for the given program
def get_program_open_sessions(school_id, program_id):
    result = {
        'school': school_id,
        'program': program_id,
        'sessions': []
    }

    soup = get_program_admission_page(school_id, program_id)

    # find all sessions/groups open for registration
    sessions = soup.find_all('div', class_='col-md-6 col-xl-4 d-flex flex-column')
    for session in sessions:
        status = session.find('span', class_='badge badge-pill badge-success')

        if status is None:
            continue

        status = status.text.lower()

        # check if the statu of the session is open and retrieve necessary related information
        if status in ['ouvert', 'open']:
            modal_target = session.find('div', attrs={'data-toggle': 'modal'})

            if modal_target is None:
                result['sessions'].append(session.find('h2', class_='custom_title').text)
            else:
                modal = session.parent.find('div', attrs={'id': modal_target.attrs.get('data-target').replace('#', '')})
                session_name = modal.find('h1', class_='modal-title').text
                modal_body = modal.find('div', class_='modal-body')
                children = modal_body.find_all(recursive=False)
                school = children[0]
                program = children[1]

                if (result['school'] == school_id) or (result['program'] == program_id):
                    result['school'] = school.find_all()[-1].text
                    result['program'] = program.find_all()[-1].text

                result['sessions'].append(session_name)

    return result

if __name__ == "__main__":
    load_dotenv(os.path.join(BASE_DIR, '.env'))

    school_id = os.getenv('SCHOOL_ID')
    program_ids = os.getenv('PROGRAM_IDS').split(',')

    email_service = EmailService(
        sender_email=os.getenv('MAIL_FROM')
    )

    for program_id in program_ids:
        program_result = get_program_open_sessions(school_id, program_id)

        # Construct the email to notify users when open sessions are available
        if len(program_result['sessions']) > 0:
            registration_url = f"{os.getenv('BASE_URL')}?ecoleID={school_id}&programmeID={program_id}"

            email_subject = f'Open sessions for "{program_result["program"]}" at "{program_result["school"]}"'

            email_body = """Hello,\n\nThis email is to inform you that the "{program}" at {school} has sessions open for registration.\n\n
            Open Sessions: {sessions}\n\n
            Click on the following link to open the program and register for the session that suits you: {url}\n\nRegards""".format(
                program = program_result["program"],
                school=program_result["school"],
                sessions=','.join(program_result["sessions"]),
                url=registration_url
            )

            email_service.send(
                subject=email_subject,
                body=email_body,
                recipients=os.getenv('MAIL_TO').split(',')
            )