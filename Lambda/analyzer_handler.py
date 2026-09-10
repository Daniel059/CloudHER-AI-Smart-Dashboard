import json
import os
import time
import uuid
import urllib.request
import urllib.error

import boto3

dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Updated Groq model
GROQ_MODEL = "openai/gpt-oss-20b"

table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
}


def call_groq(document_text: str) -> str:
    """Send the document text to Groq AI and return a short summary."""

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a concise document summarizer. Summarize the "
                    "document the user provides in 3-5 sentences, focusing "
                    "on the key points."
                ),
            },
            {
                "role": "user",
                "content": document_text[:12000],
            },
        ],
        "temperature": 0.3,
        "max_tokens": 300,
    }

    request = urllib.request.Request(
        GROQ_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "CloudHER-Dashboard/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            result = json.loads(response.read().decode("utf-8"))

        return result["choices"][0]["message"]["content"].strip()

    except urllib.error.HTTPError as error:
        # Log detailed information to CloudWatch for troubleshooting
        error_body = error.read().decode("utf-8", errors="replace")

        print("========== GROQ API ERROR ==========")
        print(f"HTTP Status: {error.code}")
        print(f"Reason: {error.reason}")
        print(f"Response: {error_body}")
        print("====================================")

        raise

    except urllib.error.URLError as error:
        print("========== GROQ CONNECTION ERROR ==========")
        print(f"Reason: {error.reason}")
        print("===========================================")

        raise


def lambda_handler(event, context):
    print("Received event:")
    print(json.dumps(event))

    try:
        body = json.loads(event.get("body", "{}"))

        file_name = body.get("fileName", "untitled").strip()
        document_text = body.get("documentText", "").strip()

        if not document_text:
            return {
                "statusCode": 400,
                "headers": CORS_HEADERS,
                "body": json.dumps({
                    "success": False,
                    "message": "No document text was provided.",
                }),
            }

        print(f"Analyzing file: {file_name}")
        print(f"Document length: {len(document_text)} characters")
        print(f"Using Groq model: {GROQ_MODEL}")

        summary = call_groq(document_text)

        submission_id = str(uuid.uuid4())
        timestamp = int(time.time())

        table.put_item(
            Item={
                "submissionId": submission_id,
                "type": "ANALYSIS",
                "fileName": file_name,
                "summary": summary,
                "timestamp": timestamp,
            }
        )

        print("Analysis completed successfully.")
        print(f"Submission ID: {submission_id}")

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "success": True,
                "summary": summary,
                "submissionId": submission_id,
            }),
        }

    except urllib.error.HTTPError:
        return {
            "statusCode": 502,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "success": False,
                "message": "The AI analysis service returned an error.",
            }),
        }

    except urllib.error.URLError:
        return {
            "statusCode": 502,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "success": False,
                "message": "Unable to connect to the AI analysis service.",
            }),
        }

    except Exception as error:
        print("Error analyzing document:", str(error))

        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "success": False,
                "message": (
                    "Unable to analyze the document. "
                    "Please try again later."
                ),
            }),
        }