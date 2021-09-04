-- PostgresSQL schema for CSCI4370 RateMyUGACourseAPI Project
-- author: Jp
-- author: Freddy Lim
-- author: Albert You


CREATE TYPE SEMESTER AS ENUM ('S', 'F', 'X');


CREATE DOMAIN RATING INT CHECK (VALUE BETWEEN 1 AND 5);


CREATE TABLE IF NOT EXISTS user_info (
  	id INT GENERATED ALWAYS AS IDENTITY,
    username VARCHAR(255) UNIQUE,
    token CHAR(32) UNIQUE,
    password CHAR(64),
    salt CHAR(64),
  	PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS course (
	id INT GENERATED ALWAYS AS IDENTITY,
  	subject CHAR(4),
  	course_no CHAR(5),
  	title VARCHAR(255),
  	UNIQUE (subject, course_no),
  	PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS instructor (
  	id INT GENERATED ALWAYS AS IDENTITY,
	email VARCHAR(255) UNIQUE,
  	first_name VARCHAR(255),
  	middle_name VARCHAR(255),
  	last_name VARCHAR(255),
  	PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS teaching (
	id INT GENERATED ALWAYS AS IDENTITY,
  	instructor_id INT,
  	course_id INT,
  	year CHAR(4),
  	semester SEMESTER,
  	UNIQUE (instructor_id, course_id, year, semester),
  	PRIMARY KEY (id),
  	CONSTRAINT fk_instructor
  		FOREIGN KEY (instructor_id)
  			REFERENCES instructor (id)
  			ON DELETE CASCADE,
  	CONSTRAINT fk_course
  		FOREIGN KEY (course_id)
  			REFERENCES course (id)
  			ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS review (
  	id INT GENERATED ALWAYS AS IDENTITY,
    user_id INT,
    teaching_id INT,
    instructor_rating RATING,
    difficulty_rating RATING,
    comment TEXT,
    PRIMARY KEY (id),
  	UNIQUE (user_id, teaching_id),
  	CONSTRAINT fk_user
  		FOREIGN KEY (user_id)
  			REFERENCES user_info (id)
  			ON DELETE CASCADE,
  	CONSTRAINT fk_teach	
  		FOREIGN KEY (teaching_id)
  			REFERENCES teaching (id)
  			ON DELETE CASCADE
);
