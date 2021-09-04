import threading

from flask import Flask, redirect, request
from flask_cors import CORS, cross_origin

from database import *
from semester import get_semester

app = Flask(__name__)
cors = CORS(app)

app.config['CORS_HEADER'] = 'Content-Type'

@app.route('/')
@cross_origin()
def redirect_to_api():
    return redirect('https://grasscode.net/api', code=302)


@app.route('/register', methods=['POST'])
@cross_origin()
def register_user():
    data = request.get_json(force=True)
    username = data['username']
    password = data['password']

    if username is None or password is None:
        return 'Missing username or password', 401

    t = register(username, password)
    if not t:
        return 'Username is already in use', 401
    return {"token": t}


@app.route('/token', methods=['POST'])
@cross_origin()
def get_token():
    data = request.get_json(force=True)
    username = data['username']
    password = data['password']

    if username is None or password is None:
        return 'Missing username or password', 401

    t = token(username, password)
    if not t:
        return 'Username or password is incorrect', 401
    return {"token": t}


@app.route('/instructor', methods=['GET'])
@cross_origin()
def find_instructor():
    email = request.args.get('email', default='%', type=str)
    first_name = request.args.get('first_name', default='%', type=str)
    middle_name = request.args.get('middle_name', default='%', type=str)
    last_name = request.args.get('last_name', default='%', type=str)

    check_connection()
    with conn.cursor() as cur:
        query = """\
            SELECT * FROM instructor 
            WHERE email ILIKE %s
            AND first_name ILIKE %s
            AND middle_name ILIKE %s
            AND last_name ILIKE %s;"""
        cur.execute(query, (email, first_name, middle_name, last_name))
        if cur.rowcount != 0:
            results = cur.fetchall()
            l = []
            for result in results:
                l.append({
                    "id": result[0],
                    "email": result[1],
                    "first_name": result[2],
                    "middle_name": result[3],
                    "last_name": result[4]
                })
            return {
                "count": len(l),
                "instructors": l
            }
        return 'No instructor was found with the given parameters', 204


@app.route('/course', methods=['GET'])
@cross_origin()
def find_course():
    subject = request.args.get('subject', default='%', type=str)
    course_no = request.args.get('course_no', default='%')
    if len(course_no) == 4:
        course_no = course_no + " "

    check_connection()
    with conn.cursor() as cur:
        query = """\
            SELECT * FROM course 
            WHERE subject ILIKE %s
            AND course_no ILIKE %s;"""
        cur.execute(query, (subject, course_no))
        if cur.rowcount != 0:
            results = cur.fetchall()
            l = []
            for result in results:
                l.append({
                    "id": result[0],
                    "subject": result[1],
                    "course_no": result[2],
                    "title": result[3]
                })
            return {
                "count": len(l),
                "courses": l
            }
        return 'No course was found with the given parameters', 204


@app.route('/teaching', methods=['GET'])
@cross_origin()
def find_teaching():
    instructor_id = request.args.get('instructor_id', default=None, type=int)
    course_id = request.args.get('course_id', default=None, type=int)
    year = request.args.get('year', default='%', type=str)
    semester_raw = request.args.get('semester', default=None, type=str)

    semester = None
    if semester_raw:
        semester = get_semester(semester_raw)
        if semester is None:
            return 'Provided semester is not valid', 400

    check_connection()
    with conn.cursor() as cur:
        l = []

        subquery = "SELECT * FROM teaching WHERE year LIKE %s"
        t = []
        t.append(year)

        if semester:
            subquery += " AND semester=%s"
            t.append(semester.enum())

        if instructor_id:
            subquery += " AND instructor_id=%s"
            t.append(instructor_id)

        if course_id:
            subquery += " AND course_id=%s"
            t.append(course_id)

        query = """\
            SELECT  t.id,
                    instructor_id, email, first_name, middle_name, last_name,
                    course_id, subject, course_no, title,
                    year, semester
            FROM (""" + subquery + """) t
            INNER JOIN instructor i ON t.instructor_id = i.id
            INNER JOIN course c ON t.course_id = c.id;"""

        cur.execute(query, tuple(t))
        if cur.rowcount != 0:
            results = cur.fetchall()
            l = []
            for result in results:
                l.append({
                    "id": result[0],
                    "instructor": {
                        "id": result[1],
                        "email": result[2],
                        "first_name": result[3],
                        "middle_name": result[4],
                        "last_name": result[5]
                    },
                    "course": {
                        "id": result[6],
                        "subject": result[7],
                        "course_no": result[8],
                        "title": result[9]
                    },
                    "year": result[10],
                    "semester": result[11]
                })
            return {
                "count": len(l),
                "teachings": l
            }
        return 'No teaching was found with the given parameters', 204


@app.route('/review', methods=['POST'])
@cross_origin()
def leave_review():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return 'Authorization token required', 401

    auth_token = auth_header.split(" ")[1]
    user_id = valid_token(auth_token)

    if user_id is None:
        return 'Provide token is not valid', 401

    data = request.get_json(force=True)
    if 'teaching_id' not in data:
        return 'teaching_id is required', 400

    if 'instructor_rating' not in data:
        return 'instructor_rating is required', 400

    if 'difficulty_rating' not in data:
        return 'difficulty_rating is required', 400

    teaching_id = data['teaching_id']
    instructor_rating = data['instructor_rating']
    difficulty_rating = data['difficulty_rating']

    if 'comment' in data:
        comment = data['comment']
    else:
        comment = ''

    check_connection()
    with conn.cursor() as cur:
        query = "SELECT id FROM teaching WHERE id=%s;"
        cur.execute(query, (teaching_id,))

        if cur.rowcount != 0:
            query = """\
                INSERT INTO review (user_id, teaching_id, instructor_rating, difficulty_rating, comment)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;"""

            try:
                cur.execute(query, (user_id, teaching_id,
                                    instructor_rating, difficulty_rating, comment))
            except pg.Error as e:
                conn.rollback()
                error_code = e.pgcode
                if error_code == "23505":
                    return 'You have already posted the review on this teaching', 400
                
                if error_code == "23514":
                    return 'Ratings should be between 1 to 5', 400
                
                return "Unknown Error", 400

            review_id = cur.fetchone()[0]
            conn.commit()
            return {"review_id": review_id}
        return 'Provided teaching_id is invalid', 400


@app.route('/review', methods=['GET'])
@cross_origin()
def get_review():
    instructor_id = request.args.get('instructor_id', default=None, type=int)
    course_id = request.args.get('course_id', default=None, type=int)
    year = request.args.get('year', default='%', type=str)
    semester_raw = request.args.get('semester', default=None, type=str)

    semester = None
    if semester_raw:
        semester = get_semester(semester_raw)
        if semester is None:
            return 'Provided semester is not valid', 400

    check_connection()
    with conn.cursor() as cur:
        l = []

        query = """\
            SELECT
	            e.id, 
                i.id, i.email, i.first_name, i.middle_name, i.last_name,
                c.id, c.subject, c.course_no, c.title,
                e.year, e.semester,
                e.instructor_rating, e.difficulty_rating, e.comment
            FROM 
                (
                    SELECT
                        t.instructor_id, t.course_id, t.year, t.semester,
                        r.id, r.instructor_rating, r.difficulty_rating, r.comment
                    FROM
                        (SELECT * FROM review) r
                        INNER JOIN teaching t ON t.id = r.teaching_id
                ) e
                INNER JOIN instructor i ON e.instructor_id = i.id
                INNER JOIN course c ON e.course_id = c.id
            WHERE
                e.year LIKE %s"""

        t = []
        t.append(year)

        if semester:
            query += " AND semester=%s"
            t.append(semester.enum())

        if instructor_id:
            query += " AND instructor_id=%s"
            t.append(instructor_id)

        if course_id:
            query += " AND course_id=%s"
            t.append(course_id)

        cur.execute(query, tuple(t))
        if cur.rowcount != 0:
            results = cur.fetchall()
            l = []
            for result in results:
                l.append({
                    "id": result[0],
                    "teaching": {
                        "instructor": {
                            "id": result[1],
                            "email": result[2],
                            "first_name": result[3],
                            "middle_name": result[4],
                            "last_name": result[5]
                        },
                        "course": {
                            "id": result[6],
                            "subject": result[7],
                            "course_no": result[8],
                            "title": result[9]
                        },
                        "year": result[10],
                        "semester": result[11]
                    },
                    "instructor_rating": result[12],
                    "difficulty_rating": result[13],
                    "comment": result[14]
                })
            return {
                "count": len(l),
                "reviews": l
            }
        return 'No review was found with the given parameters', 204


@app.route('/update/<string:year>/<string:semester_raw>')
@cross_origin()
def update_courses(year, semester_raw):
    semester = get_semester(semester_raw)
    if semester is None:
        return 'Provided semester is not valid', 400

    t = threading.Thread(target=update, args=(year, semester))
    t.start()

    return f'Database update requested', 200
