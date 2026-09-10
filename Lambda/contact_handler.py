import json
import os
import time
import uuid

import boto3

ses = boto3.client("ses")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
RECIPIENT_EMAIL = os.environ["RECIPIENT_EMAIL"]

table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
}


def lambda_handler(event, context):
    print("Received event:")
    print(json.dumps(event))

    try:
        body = json.loads(event.get("body", "{}"))

        name = body.get("name", "").strip()
        email = body.get("email", "").strip()
        subject = body.get("subject", "Contact Form Message").strip()
        message = body.get("message", "").strip()

        if not name or not email or not message:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({
                    "success": False,
                    "message": "Name, email and message are required.",
                }),
            }

        submission_id = str(uuid.uuid4())
        timestamp = int(time.time())

        # 1. Save to DynamoDB first so the dashboard reflects the submission
        #    even if the email send fails afterwards.
        table.put_item(Item={
            "submissionId": submission_id,
            "type": "CONTACT",
            "name": name,
            "email": email,
            "subject": subject,
            "message": message,
            "timestamp": timestamp,
        })

        # 2. Notify the site owner
        owner_email_body = (
            "You have received a new message through the CloudHER AI "
            f"Smart Dashboard contact form.\n\n"
            f"Name: {name}\nEmail: {email}\nSubject: {subject}\n\n"
            f"Message:\n{message}"
        )

        ses.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [RECIPIENT_EMAIL]},
            ReplyToAddresses=[email],
            Message={
                "Subject": {
                    "Data": f"CloudHER Contact Form: {subject}",
                    "Charset": "UTF-8",
                },
                "Body": {
                    "Text": {"Data": owner_email_body, "Charset": "UTF-8"},
                },
            },
        )

        # 3. Confirmation email back to the sender
        confirmation_body = (
            f"Hi {name},\n\n"
            "Thanks for reaching out through the CloudHER AI Smart "
            "Dashboard. Your message has been received and I'll get "
            "back to you soon.\n\n"
            f"Your message:\n{message}\n\n"
            "— CloudHER AI Smart Dashboard"
        )

        ses.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {
                    "Data": "We received your message",
                    "Charset": "UTF-8",
                },
                "Body": {
                    "Text": {"Data": confirmation_body, "Charset": "UTF-8"},
                },
            },
        )

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "success": True,
                "message": "Your message was sent successfully!",
                "submissionId": submission_id,
            }),
        }

    except Exception as error:
        print("Error processing contact submission:", str(error))
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "success": False,
                "message": "Unable to send your message. Please try again later.",
            }),
        }