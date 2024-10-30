CREATE DATABASE blah;
USE blah;

CREATE TABLE Textbook (
    textbook_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL
);

CREATE TABLE User (
    user_id VARCHAR(8) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'faculty', 'student', 'ta') NOT NULL
);

CREATE TABLE Course (
    course_id INT PRIMARY KEY AUTO_INCREMENT,
    course_title VARCHAR(255) NOT NULL,
    faculty_id VARCHAR(8) NOT NULL, -- Updated to match User.user_id type
    start_dt DATE NOT NULL,
    end_dt DATE NOT NULL,
    course_token VARCHAR(7) NOT NULL,
    capacity INT NOT NULL,
    course_type ENUM('active', 'evaluation') NOT NULL,
    textbook_id INT NOT NULL,
    FOREIGN KEY (textbook_id) REFERENCES Textbook(textbook_id),
    FOREIGN KEY (faculty_id) REFERENCES User(user_id)
);

CREATE TABLE Chapter (
    chapter_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    chapter_num VARCHAR(5) NOT NULL,
    textbook_id INT NOT NULL,
    FOREIGN KEY (textbook_id) REFERENCES Textbook(textbook_id),
    UNIQUE (textbook_id, chapter_num)
);

CREATE TABLE Section (
    section_id INT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    section_num VARCHAR(5) NOT NULL,
    chapter_id INT NOT NULL,
    FOREIGN KEY (chapter_id) REFERENCES Chapter(chapter_id),
    UNIQUE (chapter_id, section_num)
);

CREATE TABLE ContentBlock (
    contentblock_id INT PRIMARY KEY,
    content_type ENUM('text', 'image') NOT NULL,
    content TEXT NOT NULL,
    section_id INT NOT NULL,
    hidden TINYINT,
    FOREIGN KEY (section_id) REFERENCES Section(section_id)
);

CREATE TABLE Activity (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    question TEXT NOT NULL,
    correct_ans VARCHAR(255) NOT NULL,
    incorrect_ans1 TEXT NOT NULL,
    incorrect_ans2 TEXT NOT NULL,
    incorrect_ans3 TEXT NOT NULL,
    explanation TEXT NOT NULL,
    contentblock_id INT NOT NULL,
    FOREIGN KEY (contentblock_id) REFERENCES ContentBlock(contentblock_id)
);

CREATE TABLE Faculty(
faculty_id VARCHAR(8) PRIMARY KEY,
course_id INT,
FOREIGN KEY (course_id) REFERENCES Course(course_id)
);



CREATE TABLE TAAssignment (
    course_id INT NOT NULL,
    user_id INT NOT NULL,
    PRIMARY KEY (course_id, user_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
); 

CREATE TABLE Enrollment (
    enrollment_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(8) NOT NULL,
    course_id INT NOT NULL,
    status ENUM('pending', 'approved') NOT NULL,
    FOREIGN KEY (student_id) REFERENCES User(user_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id)
);

CREATE TABLE Notification (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(8) NOT NULL,
    notif_message TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    read_flag TINYINT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

CREATE TABLE StudentActivity (
    studentuser_id VARCHAR(8) NOT NULL,
    activity_id INT NOT NULL,
    score INT NOT NULL,
    timestamp DATETIME NOT NULL,
    PRIMARY KEY (studentuser_id, activity_id),
    FOREIGN KEY (studentuser_id) REFERENCES User(user_id),
    FOREIGN KEY (activity_id) REFERENCES Activity(activity_id)
);

-- Insert admin user
INSERT INTO User (user_id, first_name, last_name, email, password, role)
VALUES ('1', 'blah', 'blah2', 'blah@example.com', 'blah', 'admin');

USE blah;
SELECT* FROM Section;


