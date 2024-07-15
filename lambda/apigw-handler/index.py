import os
import json
import logging
import boto3
from datetime import date

logger = logging.getLogger()
logger.setLevel(logging.INFO)


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME"))


def handler(event, context):
    username = event["pathParameters"]["username"]
    route_key = event["routeKey"]
    today = date.today()
    body = {}
    try:
        if route_key == "GET /hello/{username}":
            body = table.get_item(Key={"username": username})
            dateofbirth_str = body["Item"]["dateofbirth"]
            dateofbirth = date.fromisoformat(dateofbirth_str)
            birthday_date = date(today.year, dateofbirth.month, dateofbirth.day)
            if birthday_date == today:
                body = {"message": f"Hello, {username}! Happy birthday!"}
                logger.info(
                    f"Queried user {username} has date of birth {dateofbirth_str}. That is today."
                )
            else:
                if birthday_date < today:
                    birthday_date = birthday_date.replace(year=today.year + 1)
                days_to_dateofbirth = abs(birthday_date - today).days
                body = {
                    "message": f"Hello, {username}! Your birthday is in {days_to_dateofbirth} day(s)"
                }
                logger.info(
                    f"Queried user {username} has date of birth {dateofbirth_str}. That is in {days_to_dateofbirth} day(s)."
                )
            statusCode = 200
        elif route_key == "PUT /hello/{username}":
            requestJSON = json.loads(event["body"])
            dateofbirth = requestJSON["dateOfBirth"]
            if not username.isalpha() or date.fromisoformat(dateofbirth) > today:
                raise ValueError
            table.put_item(Item={"dateofbirth": dateofbirth, "username": username})
            logger.info(
                f"User {username} has submitted date of birth {dateofbirth}. Records successfully added to database."
            )
            statusCode = 204
    except KeyError:
        statusCode = 400
        body = {"message": "Error. Requested incorrect resource."}
        logger.error("Requested incorrect resource.")
    except ValueError:
        statusCode = 400
        body = {"message": "Error. Incorrect input."}
        logger.error(
            f"Submitted not valid format of user {username} and/or date of birth {dateofbirth}. Records were not added to database."
        )
    body = json.dumps(body)
    res = {
        "statusCode": statusCode,
        "headers": {"Content-Type": "application/json"},
        "body": body,
    }
    return res
