# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(from_email, to_email, subject, html_content):
    # message = Mail(
    #     from_email=from_email,
    #     to_emails=to_email,
    #     subject=subject,
    #     html_content=html_content
    # )
    # try:
    #     sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    #     response = sg.send(message)
    #     print(response.status_code)
    #     print(response.body)
    #     print(response.headers)
    # except Exception as e:
    #     print(e.message)
    return "Email sent successfully"

# message = Mail(
#     from_email='jiadaouyang@gmail.com',
#     to_emails='jiadaouyang@gmail.com',
#     subject='Sending with Twilio SendGrid is Fun',
#     html_content='<strong>and easy to do anywhere, even with Python</strong>')
# try:
#     sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
#     # sg.set_sendgrid_data_residency("eu")
#     # uncomment the above line if you are sending mail using a regional EU subuser
#     response = sg.send(message)
#     print(response.status_code)
#     print(response.body)
#     print(response.headers)
# except Exception as e:
#     print(e.message)