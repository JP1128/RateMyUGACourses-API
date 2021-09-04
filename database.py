import logging
import os
import uuid
from typing import Optional

import psycopg2 as pg
from dotenv import load_dotenv

import login
from course import scrape_courses
from semester import FALL, Semester

load_dotenv()

dbname = os.environ.get('db_name')
host = os.environ.get('db_host')
user = os.environ.get('db_user')
password = os.environ.get('db_password')


def _connectdb():
    return pg.connect(dbname=dbname, host=host,
                      user=user, password=password)


# Database connection
conn = _connectdb()


def check_connection():
    global conn
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM user_info")
    except:
        conn = _connectdb()


def register(username, password) -> Optional[str]:
    check_connection()
    with conn.cursor() as cur:
        query = "SELECT username FROM user_info WHERE username = %s;"
        cur.execute(query, (username,))

        if cur.rowcount == 0:
            key, salt = login.hash(password)
            token = uuid.uuid4().hex
            query = """\
                INSERT INTO user_info (username, token, password, salt) 
                VALUES (%s, %s, %s, %s);"""
            cur.execute(query, (username, token, key, salt))
            conn.commit()
            return token

    return None


def token(username, password) -> Optional[str]:
    check_connection()
    with conn.cursor() as cur:
        query = "SELECT token, password, salt FROM user_info WHERE username = %s;"
        cur.execute(query, (username,))
        if cur.rowcount != 0:
            token, correct_password, salt = cur.fetchone()
            attempted_password, salt = login.hash(password, salt)
            print(attempted_password, correct_password, salt)
            if attempted_password == correct_password:
                return token

        return None


def valid_token(token_str: str) -> Optional[int]:
    check_connection()
    with conn.cursor() as cur:
        query = "SELECT id FROM user_info WHERE token=%s;"
        cur.execute(query, (token_str,))
        if cur.rowcount != 0:
            return cur.fetchone()[0]
        return None


def update(year, semester: Semester):
    check_connection()
    sections = scrape_courses(year, semester)

    if not sections:
        return

    courses_d = dict()
    instructors_d = dict()
    teaching = set()

    # courses & instructors
    for subject, number, title, email, first, middle, last in sections:
        courses_d.setdefault((subject, number), title)
        instructors_d.setdefault(email, (first, middle, last))
        teaching.add((year, semester.enum(), email, subject, number))

    courses = []
    for key, value in courses_d.items():
        courses.append((*key, value))

    instructors = []
    for key, value in instructors_d.items():
        instructors.append((key, *value))

    with conn.cursor() as cur:
        # insert courses
        query = """\
            INSERT INTO course (subject, course_no, title)
            VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;"""
        cur.executemany(query, courses)

        # insert instructors
        query = """\
            INSERT INTO instructor (email, first_name, middle_name, last_name) 
            VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;"""
        cur.executemany(query, instructors)

        # insert teachings
        query = """\
            INSERT INTO teaching (instructor_id, course_id, year, semester)
            SELECT i.id, c.id, %s, %s
            FROM    (SELECT id FROM instructor WHERE email=%s) i,
                    (SELECT id FROM course WHERE subject=%s AND course_no=%s) c
            ON CONFLICT DO NOTHING;"""
        cur.executemany(query, list(teaching))
        conn.commit()
    logging.debug('Update complete')


if __name__ == '__main__':
    update('2021', FALL)
