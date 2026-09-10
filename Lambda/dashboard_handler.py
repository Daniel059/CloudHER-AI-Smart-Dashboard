import json
import os
from decimal import Decimal

import boto3

dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
table = dynamodb.Table(TABLE_NAME)

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
}


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError


def lambda_handler(event, context):
    print("Received event:")
    print(json.dumps(event))

    try:
        response = table.scan()
        items = response.get("Items", [])

        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        items.sort(key=lambda item: item.get("timestamp", 0), reverse=True)

        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "success": True,
                "count": len(items),
                "submissions": items,
            }, default=decimal_default),
        }

    except Exception as error:
        print("Error fetching submissions:", str(error))
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({
                "success": False,
                "message": "Unable to fetch submissions.",
            }),
        }