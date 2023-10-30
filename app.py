from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash
import os
import psycopg2
from dotenv import load_dotenv

# Create table
CREATE_ROOMS_TABLE = (
    "CREATE TABLE IF NOT EXISTS rooms (id SERIAL PRIMARY KEY, name TEXT);"
)

CREATE_TEMPS_TABLE = """CREATE TABLE IF NOT EXISTS temperatures (room_id INTEGER, temperature REAL, 
                        date TIMESTAMP, FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE);"""

# Insert Data
# Return id to send it back to cthe client of our API.
# Uses id in requests to insert temperatures related to the new room.
INSERT_ROOM_RETURN_ID = "INSERT INTO rooms (name) VALUES (%s) RETURNING id;"

# Insert Temperature
INSERT_TEMP = (
    "INSERT INTO temperatures (room_id, temperature, date) VALUES (%s, %s, %s)"
)

GLOBAL_NUMBER_OF_DAYS = "SELEECT COUNT(DISTINCT DATE(date) AS days FROM temperatures)"

GLOBAL_AVG = "SELECT AVG(temperature) as average FROM temperatures"

load_dotenv()  # load variabes from .env file into environment

app = Flask(__name__)
url = os.getenv("DATABASE_URL")
connection = psycopg2.connect(url)


# Post Method used to for client who wants to send data
# Then get the data that the client had sent us (.json file) or any other format.
# cursor is an object that allow us to
# insert data into the database or iterate over rows that
# the  database return if we make a query to select a data.
@app.post("/api/room")
def create_room():
    data = request.get_json()
    name = data["name"]
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_ROOMS_TABLE)
            cursor.execute(INSERT_ROOM_RETURN_ID, (name,))  # pass a tuple
            room_id = cursor.fetchone()[0]  # access first row, give us the only row
    return {"id": room_id, "message": f"Room {name} created."}, 201


@app.post("/api/temperature")
def add_temp():
    data = request.get_json()
    temperature = data["temperature"]
    room_id = data["room"]
    try:
        date = datetime.strptime(data["date"], "%m-%d-%Y")
    except KeyError:
        date = datetime.now(timezone.utc)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TEMPS_TABLE)
            cursor.execute(INSERT_TEMP, (room_id, temperature, date))
    return {"message": "Temperature added."}, 201


@app.get("/api/average")
def get_global_avg():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(GLOBAL_AVG)
            average = cursor.fetchone()[0]
            cursor.execute(GLOBAL_NUMBER_OF_DAYS)
            days = cursor.fetchone()[0]
    return {"average": round(average, 2), "days": days}
