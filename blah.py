from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure random key

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",  # Replace with your username
        password="blah",  # Replace with your password
        database="blah"  # Replace with your database name
    )

@app.route('/')
def home():
    return redirect(url_for('start_menu'))

# Start Menu Route
@app.route('/start_menu')
def start_menu():
    return render_template('start_menu.html')

# Exit route (this can just end the session)
@app.route('/exit')
def exit_app():
    session.clear()  # Clear the session
    return "Goodbye! The application has been terminated."

@app.route('/login/<user_type>', methods=['GET', 'POST'])
def login(user_type):
    if request.method == 'POST':
        # Check the action: Sign-In or Go Back
        action = request.form['action']

        # If user clicks Go Back, discard input and return to start menu
        if action == 'go_back':
            return redirect(url_for('start_menu'))

        # If user clicks Sign-In, validate credentials
        if action == 'sign_in':
            user_id = request.form['user_id']
            password = request.form['password']

            # Connect to database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to check login credentials based on role
            cursor.execute("SELECT * FROM User WHERE user_id=%s AND password=%s AND role=%s", (user_id, password, user_type))
            user = cursor.fetchone()

            if user:
                # Store user details in session
                session['user_id'] = user[0]
                session['role'] = user[5]  # Assuming 'role' is the 6th column in the User table

                # Redirect based on user role
                if user[5] == 'admin':
                    return redirect(url_for('admin_home'))
                elif user[5] == 'faculty':
                    return redirect(url_for('faculty_home'))
                elif user[5] == 'ta':
                    return redirect(url_for('ta_home'))
                elif user[5] == 'student':
                    return redirect(url_for('student_home'))
            else:
                # If login credentials are incorrect
                return "Login Incorrect. Please try again."

            # Cleanup
            cursor.close()
            conn.close()

    # Render the login page on GET request or form submission failure
    return render_template('login.html', user_type=user_type)



# Admin Home Route
@app.route('/admin')
def admin_home():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_home.html')
    else:
        return redirect(url_for('login', user_type='admin'))




# Student Home Route
@app.route('/student')
def student_home():
    if 'role' in session and session['role'] == 'student':
        return "Welcome Student!"
    else:
        return redirect(url_for('login', user_type='student'))

@app.route('/create_faculty', methods=['GET', 'POST'])
def create_faculty():
    if 'role' in session and session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    if request.method == 'POST':
        action = request.form['action']  # Determine which button was clicked

        if action == 'go_back':
            return redirect(url_for('admin_home'))

        if action == 'add_user':
            user_id = request.form['user_id']  # Capture user_id from form
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            password = request.form['password']

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the email or user_id already exists
            cursor.execute("SELECT * FROM User WHERE user_id = %s", (user_id,))
            existing_user_id = cursor.fetchone()
            
            cursor.execute("SELECT * FROM User WHERE email = %s", (email,))
            existing_email = cursor.fetchone()

            if existing_user_id:
                cursor.close()
                conn.close()
                return "This user ID already exists. Please try again with a different user ID."

            if existing_email:
                cursor.close()
                conn.close()
                return "A user with this email already exists. Please try again with a different email."

            try:
                # Insert the new faculty record into the database
                cursor.execute("""
                    INSERT INTO User (user_id, first_name, last_name, email, password, role) 
                    VALUES (%s, %s, %s, %s, %s, 'faculty')
                """, (user_id, first_name, last_name, email, password))
                conn.commit()

                return "Faculty account created successfully!"
            except mysql.connector.Error as err:
                if err.errno == 1062:  # Error code for duplicate entry
                    return "This user ID already exists. Please try again with a different user ID."
                else:
                    return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    return render_template('create_faculty.html')





# Route for creating an e-textbook
@app.route('/create_textbook', methods=['GET', 'POST'])
def create_textbook():
    if 'role' in session and session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    if request.method == 'POST':
        action = request.form['action']  # Determine which button was clicked

        # If Go Back is clicked, discard input and redirect to Admin Landing Page
        if action == 'go_back':
            return redirect(url_for('admin_home'))

        # If Add New Chapter is clicked, first save the E-textbook details, then redirect to Add New Chapter
        if action == 'add_chapter':
            title = request.form['title']
            textbook_id = request.form['textbook_id']

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the textbook ID already exists
            cursor.execute("SELECT * FROM Textbook WHERE textbook_id=%s", (textbook_id,))
            existing_textbook = cursor.fetchone()

            if existing_textbook:
                return "A textbook with this ID already exists. Please try again with a different ID."

            try:
                # Insert the new textbook record into the database
                cursor.execute("""
                    INSERT INTO Textbook (textbook_id, title)
                    VALUES (%s, %s)
                """, (textbook_id, title))
                conn.commit()

                # Redirect to the Add New Chapter page after successfully creating the textbook
                return redirect(url_for('add_new_chapter', textbook_id=textbook_id))

            except mysql.connector.Error as err:
                return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    return render_template('create_textbook.html')

@app.route('/add_new_chapter/<textbook_id>', methods=['GET', 'POST'])
def add_new_chapter(textbook_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    # Store the textbook_id in session
    session['textbook_id'] = textbook_id

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the textbook_id exists in the Textbook table
    cursor.execute("SELECT * FROM Textbook WHERE textbook_id = %s", (textbook_id,))
    existing_textbook = cursor.fetchone()
    
    if not existing_textbook:
        # If the textbook_id does not exist, return an error message
        cursor.close()
        conn.close()
        return "The specified textbook ID does not exist. Please create the textbook first."

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" and "Landing Page" actions
        if action == 'go_back':
            cursor.close()
            conn.close()
            return redirect(url_for('create_textbook'))
        
        if action == 'landing_page':
            cursor.close()
            conn.close()
            return redirect(url_for('admin_home'))

        # If Add New Section is clicked, validate inputs and proceed
        if action == 'add_section':
            chapter_id = request.form['chapter_id']
            chapter_num = request.form['chapter_num']
            chapter_title = request.form['chapter_title']

            if not chapter_id or not chapter_num or not chapter_title:
                cursor.close()
                conn.close()
                return "Chapter ID, number, and title are required."

            try:
                # Insert the new chapter if the textbook_id exists
                cursor.execute("""
                    INSERT INTO Chapter (chapter_id, chapter_num, title, textbook_id)
                    VALUES (%s, %s, %s, %s)
                """, (chapter_id, chapter_num, chapter_title, session['textbook_id']))
                conn.commit()

                # Store the chapter_id in session for the next step
                session['chapter_id'] = chapter_id

                # Redirect to Add New Section page
                return redirect(url_for('add_new_section', chapter_id=chapter_id))

            except mysql.connector.Error as err:
                return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    cursor.close()
    conn.close()
    return render_template('add_new_chapter.html', textbook_id=textbook_id)







@app.route('/modify_textbook', methods=['GET', 'POST'])
def modify_textbook():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    if request.method == 'POST':
        action = request.form.get('action')  # Determine which button was clicked

        # Get the entered E-textbook ID
        textbook_id = request.form.get('textbook_id')

        # If Go Back is clicked, redirect to the previous page
        if action == 'go_back':
            return redirect(url_for('admin_home'))

        # If Landing Page is clicked, redirect to Admin Landing Page
        if action == 'landing_page':
            return redirect(url_for('admin_home'))

        # If an action requires a textbook ID, validate its existence
        if action in ['add_chapter', 'modify_chapter']:
            if not textbook_id:
                return "E-textbook ID is required to perform this action."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the textbook ID exists in the database
            cursor.execute("SELECT * FROM Textbook WHERE textbook_id = %s", (textbook_id,))
            existing_textbook = cursor.fetchone()

            cursor.close()
            conn.close()

            if not existing_textbook:
                # If the textbook ID does not exist, return an error message
                return "The specified textbook ID does not exist. Please enter a valid textbook ID."

            # Redirect based on the action
            if action == 'add_chapter':
                return redirect(url_for('add_new_chapter', textbook_id=textbook_id))
            elif action == 'modify_chapter':
                return redirect(url_for('modify_chapter', textbook_id=textbook_id))

    return render_template('modify_textbook.html')


# Route for creating a new active course
@app.route('/create_new_active_course', methods=['GET', 'POST'])
def create_course():
    if 'role' in session and session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    if request.method == 'POST':
        # Handle course creation logic
        return "New Active Course created successfully!"

    return render_template('create_new_active_course.html')

# Route for creating a new evaluation course
@app.route('/create_new_eval_course', methods=['GET', 'POST'])
def create_eval_course():
    if 'role' in session and session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    if request.method == 'POST':
        # Handle evaluation course creation logic
        return "New Evaluation Course created successfully!"

    return render_template('create_new_eval_course.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Clear session data
    return redirect(url_for('start_menu'))

@app.route('/modify_chapter', methods=['GET', 'POST'])
def modify_chapter():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    if request.method == 'POST':
        action = request.form.get('action')  # Determine which button was clicked

        # Get the chapter ID from the form
        chapter_id = request.form.get('chapter_id')

        # If Go Back is clicked, discard the input and go back to the previous page
        if action == 'go_back':
            return redirect(url_for('modify_textbook'))

        # If Landing Page is clicked, discard the input and go to Admin Landing Page
        if action == 'landing_page':
            return redirect(url_for('admin_home'))

        # If an action requires a chapter ID, validate its existence
        if action in ['add_section', 'modify_section']:
            if not chapter_id:
                return "Chapter ID is required to perform this action."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the chapter ID exists in the database
            cursor.execute("SELECT * FROM Chapter WHERE chapter_id = %s", (chapter_id,))
            existing_chapter = cursor.fetchone()

            cursor.close()
            conn.close()

            if not existing_chapter:
                # If the chapter ID does not exist, return an error message
                return "The specified chapter ID does not exist. Please enter a valid chapter ID."

            # Redirect based on the action
            if action == 'add_section':
                return redirect(url_for('add_new_section', chapter_id=chapter_id))
            elif action == 'modify_section':
                return redirect(url_for('modify_section', chapter_id=chapter_id))

    return render_template('modify_chapter.html')



@app.route('/add_new_section/<chapter_id>', methods=['GET', 'POST'])
def add_new_section(chapter_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    # Store the chapter_id in session
    session['chapter_id'] = chapter_id

    if request.method == 'POST':
        action = request.form.get('action')

        section_number = request.form.get('section_number')
        section_title = request.form.get('section_title')

        # Handle Go Back or Landing Page actions
        if action == 'go_back':
            return redirect(url_for('modify_chapter', chapter_id=chapter_id))
        if action == 'landing_page':
            return redirect(url_for('admin_home'))

        # Handle adding a new content block
        if action == 'add_content_block':
            if not section_number or not section_title:
                return "Section number and title are required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the section number already exists within the chapter
            cursor.execute("""
                SELECT * FROM Section WHERE section_num = %s AND chapter_id = %s
            """, (section_number, session['chapter_id']))
            existing_section = cursor.fetchone()

            if existing_section:
                # If a section with the same number exists, return an error message
                cursor.close()
                conn.close()
                return "A section with this number already exists in the chapter. Please use a different section number."

            try:
                # Insert the new section into the database
                cursor.execute("""
                    INSERT INTO Section (section_num, title, chapter_id)
                    VALUES (%s, %s, %s)
                """, (section_number, section_title, session['chapter_id']))  # Use chapter_id from session
                conn.commit()

                # Redirect to Add New Content Block page
                return redirect(url_for('add_new_content_block', section_id=cursor.lastrowid))

            except mysql.connector.Error as err:
                return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    return render_template('add_new_section.html', chapter_id=chapter_id)



@app.route('/add_new_content_block/<section_id>', methods=['GET', 'POST'])
def add_new_content_block(section_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    # Connect to the database to check if the section_id exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Section WHERE section_id = %s", (section_id,))
    existing_section = cursor.fetchone()

    if not existing_section:
        # If section_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified section ID does not exist. Please enter a valid section ID."

    cursor.close()
    conn.close()

    if request.method == 'POST':
        action = request.form.get('action')  # Determine which button was clicked

        # Get the content block ID from the form
        contentblock_id = request.form.get('contentblock_id')

        # If Go Back is clicked, discard the input and go back to the previous page
        if action == 'go_back':
            return redirect(url_for('add_new_section', chapter_id=session['chapter_id']))

        # If Landing Page is clicked, discard the input and go to Admin Landing Page
        if action == 'landing_page':
            return redirect(url_for('admin_home'))

        # If Add Text is clicked, validate the input and redirect to Add Text page
        if action == 'add_text':
            if not contentblock_id:
                return "Content Block ID is required to add text."
            return redirect(url_for('add_text_content', contentblock_id=contentblock_id))

        # If Add Picture is clicked, validate the input and redirect to Add Picture page
        if action == 'add_picture':
            if not contentblock_id:
                return "Content Block ID is required to add a picture."
            return redirect(url_for('add_picture_content', contentblock_id=contentblock_id))

        # If Add Activity is clicked, validate the input and redirect to Add Activity page
        if action == 'add_activity':
            if not contentblock_id:
                return "Content Block ID is required to add an activity."
            return redirect(url_for('add_activity_content', contentblock_id=contentblock_id))

    return render_template('add_new_content_block.html', section_id=section_id)


@app.route('/modify_section/<chapter_id>', methods=['GET', 'POST'])
def modify_section(chapter_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    if request.method == 'POST':
        action = request.form.get('action')  # Determine which button was clicked

        # Get the section number from the form
        section_number = request.form.get('section_number')

        # If Go Back is clicked, discard the input and go back to the previous page
        if action == 'go_back':
            return redirect(url_for('modify_chapter', chapter_id=chapter_id))

        # If Landing Page is clicked, discard the input and go to Admin Landing Page
        if action == 'landing_page':
            return redirect(url_for('admin_home'))

        # For actions requiring section validation, check if section_number exists in the chapter
        if action in ['add_content_block', 'modify_content_block']:
            if not section_number:
                return "Section number is required to perform this action."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the section exists for the given chapter_id and section_number
            cursor.execute("""
                SELECT section_id FROM Section WHERE section_num = %s AND chapter_id = %s
            """, (section_number, chapter_id))
            section = cursor.fetchone()

            cursor.close()
            conn.close()

            if not section:
                # If section_number does not exist within the chapter, return an error
                return "The specified section number does not exist in this chapter. Please enter a valid section number."

            # Retrieve the section_id from the query result for use in redirects
            section_id = section[0]

            # Redirect based on action
            if action == 'add_content_block':
                return redirect(url_for('add_new_content_block', section_id=section_id))
            elif action == 'modify_content_block':
                return redirect(url_for('modify_content_block', section_id=section_id))

    return render_template('modify_section.html', chapter_id=chapter_id)


@app.route('/modify_content_block/<section_id>', methods=['GET', 'POST'])
def modify_content_block(section_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    if request.method == 'POST':
        action = request.form.get('action')  # Determine which button was clicked

        # Get the content block ID from the form
        contentblock_id = request.form.get('contentblock_id')

        # If Go Back is clicked, discard the input and go back to the previous page
        if action == 'go_back':
            return redirect(url_for('modify_section', chapter_id=session['chapter_id']))

        # If Landing Page is clicked, discard the input and go to Admin Landing Page
        if action == 'landing_page':
            return redirect(url_for('admin_home'))

        # For actions that require contentblock_id validation
        if action in ['add_text', 'add_picture', 'add_activity']:
            if not contentblock_id:
                return "Content Block ID is required to perform this action."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the contentblock_id exists in the ContentBlock table for the specified section
            cursor.execute("""
                SELECT * FROM ContentBlock WHERE contentblock_id = %s AND section_id = %s
            """, (contentblock_id, section_id))
            existing_contentblock = cursor.fetchone()

            cursor.close()
            conn.close()

            if not existing_contentblock:
                # If contentblock_id does not exist, return an error message
                return "The specified Content Block ID does not exist in this section. Please enter a valid Content Block ID."

            # Redirect based on action
            if action == 'add_text':
                return redirect(url_for('add_text_content', contentblock_id=contentblock_id))
            elif action == 'add_picture':
                return redirect(url_for('add_picture_content', contentblock_id=contentblock_id))
            elif action == 'add_activity':
                return redirect(url_for('add_activity_content', contentblock_id=contentblock_id))

    return render_template('modify_content_block.html', section_id=section_id)


@app.route('/add_text_content/<contentblock_id>', methods=['GET', 'POST'])
def add_text_content(contentblock_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    # Connect to the database to check if the content block exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (contentblock_id,))
    existing_contentblock = cursor.fetchone()

    if not existing_contentblock:
        # If contentblock_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Content Block ID does not exist. Please enter a valid Content Block ID."

    if request.method == 'POST':
        action = request.form.get('action')  # Determine which button was clicked

        # If Go Back is clicked, discard the input and go back to the previous page
        if action == 'go_back':
            cursor.close()
            conn.close()
            return redirect(url_for('add_new_content_block', section_id=session['section_id']))

        # If Landing Page is clicked, discard the input and go to Admin Landing Page
        if action == 'landing_page':
            cursor.close()
            conn.close()
            return redirect(url_for('admin_home'))

        # If Add Text is clicked, validate the input and save the text to the database
        if action == 'add_text':
            text_content = request.form.get('text_content')

            if not text_content:
                cursor.close()
                conn.close()
                return "Text content is required."

            try:
                # Update the text content in the existing content block
                cursor.execute("""
                    UPDATE ContentBlock
                    SET content = %s, content_type = 'text'
                    WHERE contentblock_id = %s
                """, (text_content, contentblock_id))
                conn.commit()

                return "Text content added successfully!"
            except mysql.connector.Error as err:
                return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    cursor.close()
    conn.close()
    return render_template('add_text_content.html', contentblock_id=contentblock_id)





@app.route('/add_picture_content/<contentblock_id>', methods=['GET', 'POST'])
def add_picture_content(contentblock_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    # Connect to the database to check if the content block exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (contentblock_id,))
    existing_contentblock = cursor.fetchone()

    if not existing_contentblock:
        # If contentblock_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Content Block ID does not exist. Please enter a valid Content Block ID."

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" action
        if action == 'go_back':
            cursor.close()
            conn.close()
            return redirect(url_for('add_new_content_block', section_id=session['section_id']))

        # Handle "Landing Page" action
        if action == 'landing_page':
            cursor.close()
            conn.close()
            return redirect(url_for('admin_home'))

        # Handle adding the picture content
        if action == 'add_picture':
            picture_url = request.form.get('picture_url')

            if not picture_url:
                cursor.close()
                conn.close()
                return "Picture URL is required."

            try:
                # Update the content block with the new picture URL
                cursor.execute("""
                    UPDATE ContentBlock
                    SET content = %s, content_type = 'picture'
                    WHERE contentblock_id = %s
                """, (picture_url, contentblock_id))
                conn.commit()

                return "Picture content added successfully!"
            except mysql.connector.Error as err:
                return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    cursor.close()
    conn.close()
    return render_template('add_picture_content.html', contentblock_id=contentblock_id)




@app.route('/add_activity_content/<contentblock_id>', methods=['GET', 'POST'])
def add_activity_content(contentblock_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    # Connect to the database to check if the content block exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (contentblock_id,))
    existing_contentblock = cursor.fetchone()

    if not existing_contentblock:
        # If contentblock_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Content Block ID does not exist. Please enter a valid Content Block ID."

    if request.method == 'POST':
        action = request.form.get('action')  # Determine which button was clicked

        # Handle "Go Back" action
        if action == 'go_back':
            cursor.close()
            conn.close()
            return redirect(url_for('add_new_content_block', section_id=session['section_id']))

        # Handle "Landing Page" action
        if action == 'landing_page':
            cursor.close()
            conn.close()
            return redirect(url_for('admin_home'))

        # Handle adding a question to the activity
        if action == 'add_question':
            activity_id = request.form.get('activity_id')

            if not activity_id:
                cursor.close()
                conn.close()
                return "Activity ID is required."

            # Store the activity_id in the session for further use
            session['activity_id'] = activity_id

            cursor.close()
            conn.close()
            # Redirect to Add Question page
            return redirect(url_for('add_question', activity_id=activity_id))

    cursor.close()
    conn.close()
    return render_template('add_activity_content.html', contentblock_id=contentblock_id)



@app.route('/add_question/<activity_id>', methods=['GET', 'POST'])
def add_question(activity_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    # Connect to the database to check if the activity exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Activity WHERE activity_id = %s", (activity_id,))
    existing_activity = cursor.fetchone()

    if not existing_activity:
        # If activity_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Activity ID does not exist. Please enter a valid Activity ID."

    if request.method == 'POST':
        action = request.form.get('action')  # Determine which button was clicked

        # Handle "Cancel" action
        if action == 'cancel':
            cursor.close()
            conn.close()
            return redirect(url_for('add_activity_content', contentblock_id=session['contentblock_id']))

        # Handle "Landing Page" action  
        if action == 'landing_page':
            cursor.close()
            conn.close()
            return redirect(url_for('admin_home'))

        # Handle saving the question
        if action == 'save':
            # Validate required fields
            question_id = request.form.get('question_id')
            question_text = request.form.get('question_text')
            option1_text = request.form.get('option1_text')
            option1_label = request.form.get('option1_label')

            if not question_id or not question_text or not option1_text or not option1_label:
                cursor.close()
                conn.close()
                return "Question ID, Question Text, and Option 1 are required."

            # Optional fields for additional options and explanations
            option1_explanation = request.form.get('option1_explanation')
            option2_text = request.form.get('option2_text')
            option2_explanation = request.form.get('option2_explanation')
            option2_label = request.form.get('option2_label')
            option3_text = request.form.get('option3_text')
            option3_explanation = request.form.get('option3_explanation')
            option3_label = request.form.get('option3_label')
            option4_text = request.form.get('option4_text')
            option4_explanation = request.form.get('option4_explanation')
            option4_label = request.form.get('option4_label')

            try:
                # Insert the question and options into the Activity table
                cursor.execute("""
                    INSERT INTO Activity (activity_id, question, correct_ans, incorrect_ans1, incorrect_ans2, incorrect_ans3, explanation, contentblock_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (question_id, question_text, option1_text, option2_text, option3_text, option4_text, option1_explanation, activity_id))
                conn.commit()

                return "Question added successfully!"
            except mysql.connector.Error as err:
                return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    cursor.close()
    conn.close()
    return render_template('add_question.html', activity_id=activity_id)


@app.route('/create_new_active_course', methods=['GET', 'POST'])
def create_new_active_course():
    if 'role' in session and session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    if request.method == 'POST':
        action = request.form.get('action')  # Determine which button was clicked

        # If Cancel is clicked, discard the input and go back to the previous page
        if action == 'cancel':
            return redirect(url_for('admin_home'))

        # If Landing Page is clicked, discard the input and go to Admin Landing Page
        if action == 'landing_page':
            return redirect(url_for('admin_home'))

        # If Save is clicked, validate the input and save the course to the database
        if action == 'save':
            course_id = request.form.get('course_id')
            course_name = request.form.get('course_name')
            e_textbook_id = request.form.get('e_textbook_id')
            faculty_id = request.form.get('faculty_id')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            token = request.form.get('token')
            capacity = request.form.get('capacity')

            # Validate required fields
            if not course_id or not course_name or not e_textbook_id or not faculty_id:
                return "Course ID, Course Name, E-textbook ID, and Faculty Member ID are required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the e_textbook_id exists in the Textbook table
            cursor.execute("SELECT * FROM Textbook WHERE textbook_id = %s", (e_textbook_id,))
            existing_textbook = cursor.fetchone()

            if not existing_textbook:
                cursor.close()
                conn.close()
                return "The specified E-textbook ID does not exist. Please enter a valid E-textbook ID."

            try:
                # Insert the new course record into the database
                cursor.execute("""
                    INSERT INTO ActiveCourse (course_id, course_name, e_textbook_id, faculty_id, start_date, end_date, token, capacity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (course_id, course_name, e_textbook_id, faculty_id, start_date, end_date, token, capacity))
                conn.commit()

                return "Active Course created successfully!"
            except mysql.connector.Error as err:
                return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    return render_template('create_new_active_course.html')


@app.route('/create_new_eval_course', methods=['GET', 'POST'])
def create_new_eval_course():
    if 'role' in session and session['role'] != 'admin':
        return redirect(url_for('login', user_type='admin'))

    if request.method == 'POST':
        action = request.form.get('action')  # Determine which button was clicked

        # If Cancel is clicked, discard the input and go back to the previous page
        if action == 'cancel':
            return redirect(url_for('admin_home'))

        # If Landing Page is clicked, discard the input and go to Admin Landing Page
        if action == 'landing_page':
            return redirect(url_for('admin_home'))

        # If Save is clicked, validate the input and save the evaluation course to the database
        if action == 'save':
            course_id = request.form.get('course_id')
            course_name = request.form.get('course_name')
            e_textbook_id = request.form.get('e_textbook_id')
            faculty_id = request.form.get('faculty_id')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            # Validate required fields
            if not course_id or not course_name or not e_textbook_id or not faculty_id:
                return "Course ID, Course Name, E-textbook ID, and Faculty Member ID are required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the e_textbook_id exists in the Textbook table
            cursor.execute("SELECT * FROM Textbook WHERE textbook_id = %s", (e_textbook_id,))
            existing_textbook = cursor.fetchone()

            if not existing_textbook:
                cursor.close()
                conn.close()
                return "The specified E-textbook ID does not exist. Please enter a valid E-textbook ID."

            try:
                # Insert the new evaluation course record into the database
                cursor.execute("""
                    INSERT INTO EvalCourse (course_id, course_name, e_textbook_id, faculty_id, start_date, end_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (course_id, course_name, e_textbook_id, faculty_id, start_date, end_date))
                conn.commit()

                return "Evaluation Course created successfully!"
            except mysql.connector.Error as err:
                return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    return render_template('create_new_eval_course.html')



@app.route('/login/faculty', methods=['GET', 'POST'])
def login_faculty():
    if request.method == 'POST':
        # Check the action: Sign-In or Go Back
        action = request.form['action']

        # If user clicks Go Back, discard input and return to start menu
        if action == 'go_back':
            return redirect(url_for('start_menu'))

        # If user clicks Sign-In, validate credentials
        if action == 'sign_in':
            user_id = request.form['user_id']
            password = request.form['password']

            # Connect to database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to check login credentials for faculty role
            cursor.execute("SELECT * FROM User WHERE user_id=%s AND password=%s AND role='faculty'", (user_id, password))
            user = cursor.fetchone()

            if user:
                # Store user details in session
                session['user_id'] = user[0]
                session['role'] = user[5]  # Assuming 'role' is the 6th column in the User table

                # Redirect to faculty landing page
                return redirect(url_for('faculty_home'))
            else:
                # If login credentials are incorrect
                return "Login Incorrect. Please try again."

            # Cleanup
            cursor.close()
            conn.close()

    # Render the faculty login page on GET request or form submission failure
    return render_template('login_faculty.html')

@app.route('/faculty_home')
def faculty_home():
    # Check if the user is logged in and is a faculty member
    if 'role' in session and session['role'] == 'faculty':
        return render_template('faculty_home.html')
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_active_course', methods=['GET', 'POST'])
def faculty_active_course():
    # Ensure user is a faculty member
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            course_id = request.form.get('course_id')

            if not course_id:
                return "Course ID is required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the course ID exists in the database
            cursor.execute("SELECT * FROM Course WHERE course_id = %s", (course_id,))
            course = cursor.fetchone()

            cursor.close()
            conn.close()

            if course:
                # If course exists, store course_id in session and go to the menu
                session['course_id'] = course_id
                return redirect(url_for('faculty_active_course_menu'))
            else:
                # If course does not exist, display an error message
                return "Invalid Course ID. Please enter a valid Course ID."
        
        # Render the input form for course ID
        return render_template('faculty_active_course.html')
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_active_course_menu')
def faculty_active_course_menu():
    if 'role' in session and session['role'] == 'faculty' and 'course_id' in session:
        return render_template('faculty_active_course_menu.html', course_id=session['course_id'])
    else:
        return redirect(url_for('faculty_active_course'))

@app.route('/faculty_evaluation_course', methods=['GET', 'POST'])
def faculty_evaluation_course():
    # Ensure user is a faculty member
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            course_id = request.form.get('course_id')

            if not course_id:
                return "Course ID is required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the course ID exists and is an evaluation course
            cursor.execute("SELECT * FROM Course WHERE course_id = %s AND course_type = 'evaluation'", (course_id,))
            course = cursor.fetchone()

            cursor.close()
            conn.close()

            if course:
                # If course exists, store course_id in session and go to the menu
                session['course_id'] = course_id
                return redirect(url_for('faculty_evaluation_course_menu'))
            else:
                # If course does not exist, display an error message
                return "Invalid Course ID or not an Evaluation Course. Please enter a valid Evaluation Course ID."
        
        # Render the input form for course ID
        return render_template('faculty_evaluation_course.html')
    else:
        return redirect(url_for('login', user_type='faculty'))
@app.route('/view_courses', methods=['GET', 'POST'])
def view_courses():
    # Ensure user is logged in and is a faculty member
    if 'role' in session and session['role'] == 'faculty':
        faculty_id = session['user_id']  # Get the faculty ID from session
        
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query to fetch courses assigned to the logged-in faculty member
        cursor.execute("SELECT course_id, course_title FROM Course WHERE faculty_id = %s", (faculty_id,))
        assigned_courses = cursor.fetchall()

        cursor.close()
        conn.close()

        # Handle "Go Back" action
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'go_back':
                return redirect(url_for('faculty_home'))

        # Render the view_courses.html template with the assigned courses
        return render_template('view_courses.html', courses=assigned_courses)
    else:
        return redirect(url_for('login', user_type='faculty'))
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    # Ensure the user is logged in and is a faculty member
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')

            # Handle "Go Back" action
            if action == 'go_back':
                return redirect(url_for('faculty_home'))

            # Handle "Update" action
            if action == 'update':
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_new_password = request.form.get('confirm_new_password')

                # Validate inputs
                if not current_password or not new_password or not confirm_new_password:
                    return "All fields are required."

                if new_password != confirm_new_password:
                    return "New password and confirmation do not match."

                # Connect to the database
                conn = get_db_connection()
                cursor = conn.cursor()

                # Check if the current password is correct
                cursor.execute("SELECT * FROM User WHERE user_id = %s AND password = %s AND role = 'faculty'", (session['user_id'], current_password))
                user = cursor.fetchone()

                if not user:
                    cursor.close()
                    conn.close()
                    return "Current password is incorrect."

                # Update the password in the database
                try:
                    cursor.execute("UPDATE User SET password = %s WHERE user_id = %s", (new_password, session['user_id']))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    return "Password updated successfully!"
                except mysql.connector.Error as err:
                    cursor.close()
                    conn.close()
                    return f"An error occurred: {err}"

        # Render the change_password.html template for GET requests or form failure
        return render_template('change_password.html')
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/view_worklist', methods=['GET', 'POST'])
def view_worklist():
    # Ensure user is a faculty member
    if 'role' in session and session['role'] == 'faculty':
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the waiting list of students (status 'pending' in Enrollment table)
        cursor.execute("""
            SELECT User.user_id, User.first_name, User.last_name, Enrollment.course_id 
            FROM User
            JOIN Enrollment ON User.user_id = Enrollment.student_id
            WHERE Enrollment.status = 'pending' AND Enrollment.course_id = %s
        """, (session['course_id'],))  # Assuming 'course_id' is stored in session for the active course
        waiting_list = cursor.fetchall()

        cursor.close()
        conn.close()

        if request.method == 'POST':
            action = request.form.get('action')

            # Go Back option
            if action == 'go_back':
                return redirect(url_for('faculty_active_course_menu'))

        return render_template('view_worklist.html', waiting_list=waiting_list)
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/approve_enrollment', methods=['GET', 'POST'])
def approve_enrollment():
    # Ensure user is a faculty member
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            student_id = request.form.get('student_id')

            # Handle Cancel option
            if action == 'cancel':
                return redirect(url_for('faculty_active_course_menu'))

            # Handle Save option
            if action == 'save':
                if not student_id:
                    return "Student ID is required."

                # Connect to the database
                conn = get_db_connection()
                cursor = conn.cursor()

                # Update enrollment status to 'approved' if the student ID exists in the pending enrollments
                cursor.execute("""
                    UPDATE Enrollment 
                    SET status = 'approved' 
                    WHERE student_id = %s AND course_id = %s AND status = 'pending'
                """, (student_id, session['course_id']))

                # Check if any rows were affected (indicating success)
                if cursor.rowcount > 0:
                    conn.commit()
                    message = "Enrollment approved successfully!"
                else:
                    message = "Failed to approve enrollment. The student may not exist or is already approved."

                cursor.close()
                conn.close()

                return render_template('approve_enrollment.html', message=message)

        # Render the approval form on GET request
        return render_template('approve_enrollment.html')
    else:
        return redirect(url_for('login', user_type='faculty'))
@app.route('/view_students', methods=['GET', 'POST'])
def view_students():
    # Ensure user is a faculty member and course_id is in session
    if 'role' in session and session['role'] == 'faculty' and 'course_id' in session:
        if request.method == 'POST':
            # Handle Go Back option
            if request.form.get('action') == 'go_back':
                return redirect(url_for('faculty_active_course_menu'))

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to retrieve students enrolled in the specified course
        cursor.execute("""
            SELECT User.user_id, User.first_name, User.last_name 
            FROM Enrollment 
            JOIN User ON Enrollment.student_id = User.user_id 
            WHERE Enrollment.course_id = %s AND Enrollment.status = 'approved'
        """, (session['course_id'],))
        
        students = cursor.fetchall()

        cursor.close()
        conn.close()

        # Render the view students template with the list of students
        return render_template('view_students.html', students=students)
    else:
        return redirect(url_for('login', user_type='faculty'))
@app.route('/add_ta', methods=['GET', 'POST'])
def add_ta():
    # Ensure user is a faculty member
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')  # Determine which button was clicked

            # Handle Cancel option
            if action == 'cancel':
                return redirect(url_for('faculty_active_course_menu'))

            # Handle Save option
            if action == 'save':
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                email = request.form.get('email')
                default_password = request.form.get('default_password')

                if not first_name or not last_name or not email or not default_password:
                    return "All fields are required."

                # Connect to the database
                conn = get_db_connection()
                cursor = conn.cursor()

                # Check if the email already exists
                cursor.execute("SELECT * FROM User WHERE email = %s", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    cursor.close()
                    conn.close()
                    return "A user with this email already exists. Please use a different email."

                try:
                    # Insert the new TA into the User table
                    cursor.execute("""
                        INSERT INTO User (first_name, last_name, email, password, role)
                        VALUES (%s, %s, %s, %s, 'ta')
                    """, (first_name, last_name, email, default_password))
                    conn.commit()

                    return "TA added successfully!"
                except mysql.connector.Error as err:
                    return f"An error occurred: {err}"

                finally:
                    cursor.close()
                    conn.close()

        return render_template('add_ta.html')
    else:
        return redirect(url_for('login', user_type='faculty'))
@app.route('/faculty_add_new_chapter', methods=['GET', 'POST'])
def faculty_add_new_chapter():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')

            # Handle "Go Back" option
            if action == 'go_back':
                return redirect(url_for('faculty_active_course_menu'))

            # Handle "Add New Section" option
            if action == 'add_section':
                chapter_id = request.form.get('chapter_id')
                chapter_title = request.form.get('chapter_title')

                if not chapter_id or not chapter_title:
                    return "Chapter ID and Title are required."

                # Connect to the database
                conn = get_db_connection()
                cursor = conn.cursor()

                # Check if the chapter ID already exists
                cursor.execute("SELECT * FROM Chapter WHERE chapter_id = %s", (chapter_id,))
                existing_chapter = cursor.fetchone()

                if existing_chapter:
                    cursor.close()
                    conn.close()
                    return "A chapter with this ID already exists. Please enter a unique chapter ID."

                try:
                    # Insert the new chapter into the Chapter table
                    cursor.execute("""
                        INSERT INTO Chapter (chapter_id, title)
                        VALUES (%s, %s)
                    """, (chapter_id, chapter_title))
                    conn.commit()

                    # Store the chapter ID in session for adding sections
                    session['chapter_id'] = chapter_id

                    # Redirect to Add New Section page
                    return redirect(url_for('faculty_add_new_section', chapter_id=chapter_id))

                except mysql.connector.Error as err:
                    return f"An error occurred: {err}"

                finally:
                    cursor.close()
                    conn.close()

        return render_template('faculty_add_new_chapter.html')
    else:
        return redirect(url_for('login', user_type='faculty'))
@app.route('/faculty_modify_chapter', methods=['GET', 'POST'])
def faculty_modify_chapter():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            chapter_id = request.form.get('chapter_id')

            # Check if the chapter ID is provided
            if not chapter_id:
                return "Chapter ID is required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the chapter ID exists in the database
            cursor.execute("SELECT * FROM Chapter WHERE chapter_id = %s", (chapter_id,))
            chapter = cursor.fetchone()

            if not chapter:
                cursor.close()
                conn.close()
                return "Invalid Chapter ID. Please enter a valid Chapter ID."

            # Perform action based on user selection
            if action == 'faculty_hide_chapter':
                # Example logic for hiding a chapter
                cursor.execute("UPDATE Chapter SET visible = FALSE WHERE chapter_id = %s", (chapter_id,))
                conn.commit()
                message = "Chapter hidden successfully."
            elif action == 'faculty_delete_chapter':
                # Example logic for deleting a chapter
                cursor.execute("DELETE FROM Chapter WHERE chapter_id = %s", (chapter_id,))
                conn.commit()
                message = "Chapter deleted successfully."
            elif action == 'faculty_add_section':
                # Redirect to add new section page
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_add_new_section', chapter_id=chapter_id))
            elif action == 'faculty_modify_section':
                # Redirect to modify section page
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_modify_section', chapter_id=chapter_id))
            elif action == 'go_back':
                # Go back to previous page
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_active_course_menu'))
            
            cursor.close()
            conn.close()
            return message

        return render_template('faculty_modify_chapter.html')
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_hide_chapter', methods=['GET', 'POST'])
def faculty_hide_chapter():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            chapter_id = request.form.get('chapter_id')

            # If user clicks "Cancel", go back to the modify chapter page
            if action == 'cancel':
                return redirect(url_for('faculty_modify_chapter'))

            # If user clicks "Save", proceed to hide the chapter
            if action == 'save':
                # Connect to the database
                conn = get_db_connection()
                cursor = conn.cursor()

                try:
                    # Update the chapter visibility to 'hidden' or equivalent
                    cursor.execute("UPDATE Chapter SET visible = FALSE WHERE chapter_id = %s", (chapter_id,))
                    conn.commit()

                    message = "Chapter hidden successfully."
                except mysql.connector.Error as err:
                    message = f"Failed to hide the chapter: {err}"
                finally:
                    cursor.close()
                    conn.close()
                
                return message

        # Render the hide chapter confirmation form
        return render_template('faculty_hide_chapter.html')
    else:
        return redirect(url_for('login', user_type='faculty'))
@app.route('/faculty_delete_chapter', methods=['GET', 'POST'])
def faculty_delete_chapter():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            chapter_id = request.form.get('chapter_id')

            # If user clicks "Cancel", go back to the modify chapter page
            if action == 'cancel':
                return redirect(url_for('faculty_modify_chapter'))

            # If user clicks "Save", proceed to delete the chapter
            if action == 'save':
                # Connect to the database
                conn = get_db_connection()
                cursor = conn.cursor()

                try:
                    # Delete the chapter based on the chapter ID
                    cursor.execute("DELETE FROM Chapter WHERE chapter_id = %s", (chapter_id,))
                    conn.commit()

                    message = "Chapter deleted successfully."
                except mysql.connector.Error as err:
                    message = f"Failed to delete the chapter: {err}"
                finally:
                    cursor.close()
                    conn.close()
                
                return message

        # Render the delete chapter confirmation form
        return render_template('faculty_delete_chapter.html')
    else:
        return redirect(url_for('login', user_type='faculty'))
@app.route('/faculty_add_new_section', methods=['GET', 'POST'])
def faculty_add_new_section():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            section_number = request.form.get('section_number')
            section_title = request.form.get('section_title')

            # If "Go Back" is chosen, redirect to the previous page
            if action == 'go_back':
                return redirect(url_for('faculty_modify_chapter'))  # Replace with the correct route

            # If "Add New Content Block" is chosen, validate input and proceed
            if action == 'add_content_block':
                if not section_number or not section_title:
                    return "Section Number and Title are required."

                # Connect to the database
                conn = get_db_connection()
                cursor = conn.cursor()

                try:
                    # Insert the new section into the database
                    cursor.execute("""
                        INSERT INTO Section (section_num, title, chapter_id)
                        VALUES (%s, %s, %s)
                    """, (section_number, section_title, session.get('chapter_id')))  # Ensure `chapter_id` is stored in the session
                    conn.commit()

                    # Redirect to add content block after successfully creating section
                    return redirect(url_for('faculty_add_new_content_block', section_id=cursor.lastrowid))

                except mysql.connector.Error as err:
                    return f"An error occurred: {err}"

                finally:
                    cursor.close()
                    conn.close()

        # Render the Add New Section form on GET request
        return render_template('faculty_add_new_section.html')
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_modify_section', methods=['GET', 'POST'])
def faculty_modify_section():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            section_number = request.form.get('section_number')

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Validate section existence
            cursor.execute("SELECT section_id FROM Section WHERE section_num = %s", (section_number,))
            section = cursor.fetchone()

            if not section:
                cursor.close()
                conn.close()
                return "Invalid Section Number. Please try again."

            section_id = section[0]  # Store section ID for further operations

            # Option Handling - Redirect to specific functions for each action
            cursor.close()
            conn.close()

            if action == 'go_back':
                return redirect(url_for('faculty_modify_chapter'))
            elif action == 'hide_section':
                return redirect(url_for('faculty_hide_section', section_id=section_id))
            elif action == 'delete_section':
                return redirect(url_for('faculty_delete_section', section_id=section_id))
            elif action == 'add_content_block':
                return redirect(url_for('faculty_add_new_content_block', section_id=section_id))
            elif action == 'modify_content_block':
                return redirect(url_for('faculty_modify_content_block', section_id=section_id))

        # Render the Modify Section form on GET request
        return render_template('faculty_modify_section.html')
    else:
        return redirect(url_for('login', user_type='faculty'))

# Separate route for hiding a section
@app.route('/faculty_hide_section/<section_id>', methods=['GET', 'POST'])
def faculty_hide_section(section_id):
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'save':
                # Hide the section
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("UPDATE Section SET is_hidden = 1 WHERE section_id = %s", (section_id,))
                    conn.commit()
                    message = "Section successfully hidden!"
                except mysql.connector.Error as err:
                    message = f"An error occurred: {err}"
                finally:
                    cursor.close()
                    conn.close()
                return message
            elif action == 'cancel':
                return redirect(url_for('faculty_modify_section'))
        return render_template('faculty_hide_section.html', section_id=section_id)
    else:
        return redirect(url_for('login', user_type='faculty'))

# Separate route for deleting a section
@app.route('/faculty_delete_section/<section_id>', methods=['GET', 'POST'])
def faculty_delete_section(section_id):
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'save':
                # Delete the section
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("DELETE FROM Section WHERE section_id = %s", (section_id,))
                    conn.commit()
                    message = "Section successfully deleted!"
                except mysql.connector.Error as err:
                    message = f"An error occurred: {err}"
                finally:
                    cursor.close()
                    conn.close()
                return message
            elif action == 'cancel':
                return redirect(url_for('faculty_modify_section'))
        return render_template('faculty_delete_section.html', section_id=section_id)
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_add_new_content_block', methods=['GET', 'POST'])
def faculty_add_new_content_block():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            content_block_id = request.form.get('content_block_id')

            # Validate Content Block ID input
            if not content_block_id:
                return "Content Block ID is required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the Content Block ID exists
            cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (content_block_id,))
            existing_contentblock = cursor.fetchone()

            cursor.close()
            conn.close()

            if not existing_contentblock:
                return "Invalid Content Block ID. Please try again."

            # Route handling based on selected option
            if action == 'add_text':
                return redirect(url_for('faculty_add_text', content_block_id=content_block_id))
            elif action == 'add_picture':
                return redirect(url_for('faculty_add_picture', content_block_id=content_block_id))
            elif action == 'add_activity':
                return redirect(url_for('faculty_add_activity', content_block_id=content_block_id))
            elif action == 'go_back':
                return redirect(url_for('faculty_modify_section'))

        # Render the form to enter Content Block ID and select an action on GET request
        return render_template('faculty_add_new_content_block.html')
    else:
        return redirect(url_for('login', user_type='faculty'))

# Routes for adding content types
@app.route('/faculty_add_text/<content_block_id>', methods=['GET', 'POST'])
def faculty_add_text(content_block_id):
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            text_content = request.form.get('text_content')
            if not text_content:
                return "Text content is required."
            
            # Add text content to the content block
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE ContentBlock SET content = %s, content_type = 'text' WHERE contentblock_id = %s",
                               (text_content, content_block_id))
                conn.commit()
                return "Text content added successfully!"
            except mysql.connector.Error as err:
                return f"An error occurred: {err}"
            finally:
                cursor.close()
                conn.close()

        return render_template('fcaulty_add_text.html', content_block_id=content_block_id)
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_add_picture/<content_block_id>', methods=['GET', 'POST'])
def faculty_add_picture(content_block_id):
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            picture_url = request.form.get('picture_url')
            if not picture_url:
                return "Picture URL is required."

            # Add picture content to the content block
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE ContentBlock SET content = %s, content_type = 'picture' WHERE contentblock_id = %s",
                               (picture_url, content_block_id))
                conn.commit()
                return "Picture content added successfully!"
            except mysql.connector.Error as err:
                return f"An error occurred: {err}"
            finally:
                cursor.close()
                conn.close()

        return render_template('faculty_add_picture.html', content_block_id=content_block_id)
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_add_activity/<content_block_id>', methods=['GET', 'POST'])
def faculty_add_activity(content_block_id):
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            activity_id = request.form.get('activity_id')

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Validate if the activity ID already exists
            cursor.execute("SELECT * FROM Activity WHERE activity_id = %s", (activity_id,))
            existing_activity = cursor.fetchone()

            if existing_activity:
                cursor.close()
                conn.close()
                return "Activity ID already exists. Please use a unique Activity ID."

            # Option Handling
            if action == 'go_back':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_modify_content_block', content_block_id=content_block_id))

            elif action == 'add_question':
                try:
                    # Insert the new activity record into the database
                    cursor.execute("""
                        INSERT INTO Activity (activity_id, contentblock_id)
                        VALUES (%s, %s)
                    """, (activity_id, content_block_id))
                    conn.commit()

                    # Redirect to the Add Question page after adding the activity
                    return redirect(url_for('faculty_add_question', activity_id=activity_id))

                except mysql.connector.Error as err:
                    return f"An error occurred: {err}"

                finally:
                    cursor.close()
                    conn.close()

        # Render the Add Activity form on GET request
        return render_template('faculty_add_activity.html', content_block_id=content_block_id)
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_modify_content_block', methods=['GET', 'POST'])
def faculty_modify_content_block():
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            content_block_id = request.form.get('content_block_id')

            # Validate Content Block ID input
            if not content_block_id:
                return "Content Block ID is required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if Content Block ID exists
            cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (content_block_id,))
            content_block = cursor.fetchone()

            if not content_block:
                cursor.close()
                conn.close()
                return "Invalid Content Block ID. Please try again."

            # Option handling based on selected action
            if action == 'hide_content_block':
                try:
                    cursor.execute("UPDATE ContentBlock SET is_hidden = 1 WHERE contentblock_id = %s", (content_block_id,))
                    conn.commit()
                    return "Content Block successfully hidden!"
                except mysql.connector.Error as err:
                    return f"An error occurred: {err}"

            elif action == 'delete_content_block':
                try:
                    cursor.execute("DELETE FROM ContentBlock WHERE contentblock_id = %s", (content_block_id,))
                    conn.commit()
                    return "Content Block successfully deleted!"
                except mysql.connector.Error as err:
                    return f"An error occurred: {err}"

            elif action == 'add_text':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_add_text', content_block_id=content_block_id))

            elif action == 'add_picture':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_add_picture', content_block_id=content_block_id))

            elif action == 'hide_activity':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_hide_activity', content_block_id=content_block_id))

            elif action == 'delete_activity':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_delete_activity', content_block_id=content_block_id))

            elif action == 'add_activity':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_add_activity', content_block_id=content_block_id))

            elif action == 'go_back':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_modify_section'))

            # Cleanup connection
            cursor.close()
            conn.close()

        # Render the Modify Content Block form on GET request
        return render_template('faculty_modify_content_block.html')
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_hide_content_block/<content_block_id>', methods=['GET', 'POST'])
def faculty_hide_content_block(content_block_id):
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if Content Block exists
            cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (content_block_id,))
            content_block = cursor.fetchone()

            if not content_block:
                cursor.close()
                conn.close()
                return "Invalid Content Block ID. Please try again."

            # Option Handling
            if action == 'save':
                try:
                    cursor.execute("UPDATE ContentBlock SET is_hidden = 1 WHERE contentblock_id = %s", (content_block_id,))
                    conn.commit()
                    message = "Content Block successfully hidden!"
                except mysql.connector.Error as err:
                    message = f"An error occurred: {err}"
                finally:
                    cursor.close()
                    conn.close()
                    return message

            elif action == 'cancel':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_modify_content_block', section_id=content_block[3]))  # Assuming section_id is stored in the 4th column

        # Render the Hide Content Block form on GET request
        return render_template('faculty_hide_content_block.html', content_block_id=content_block_id)
    else:
        return redirect(url_for('login', user_type='faculty'))


@app.route('/faculty_delete_content_block/<content_block_id>', methods=['GET', 'POST'])
def faculty_delete_content_block(content_block_id):
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if Content Block exists
            cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (content_block_id,))
            content_block = cursor.fetchone()

            if not content_block:
                cursor.close()
                conn.close()
                return "Invalid Content Block ID. Please try again."

            # Option Handling
            if action == 'save':
                try:
                    cursor.execute("DELETE FROM ContentBlock WHERE contentblock_id = %s", (content_block_id,))
                    conn.commit()
                    message = "Content Block successfully deleted!"
                except mysql.connector.Error as err:
                    message = f"An error occurred: {err}"
                finally:
                    cursor.close()
                    conn.close()
                    return message

            elif action == 'cancel':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_modify_content_block', section_id=content_block[3]))  # Assuming section_id is stored in the 4th column

        # Render the Delete Content Block form on GET request
        return render_template('faculty_delete_content_block.html', content_block_id=content_block_id)
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_hide_activity/<activity_id>', methods=['GET', 'POST'])
def faculty_hide_activity(activity_id):
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if Activity exists
            cursor.execute("SELECT * FROM Activity WHERE activity_id = %s", (activity_id,))
            activity = cursor.fetchone()

            if not activity:
                cursor.close()
                conn.close()
                return "Invalid Activity ID. Please try again."

            # Option Handling
            if action == 'save':
                try:
                    cursor.execute("UPDATE Activity SET is_hidden = 1 WHERE activity_id = %s", (activity_id,))
                    conn.commit()
                    message = "Activity successfully hidden!"
                except mysql.connector.Error as err:
                    message = f"An error occurred: {err}"
                finally:
                    cursor.close()
                    conn.close()
                    return message

            elif action == 'cancel':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_modify_content_block', section_id=activity[3]))  # Assuming section_id is stored in the 4th column

        # Render the Hide Activity form on GET request
        return render_template('faculty_hide_activity.html', activity_id=activity_id)
    else:
        return redirect(url_for('login', user_type='faculty'))
    
@app.route('/faculty_delete_activity/<activity_id>', methods=['GET', 'POST'])
def faculty_delete_activity(activity_id):
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if Activity exists
            cursor.execute("SELECT * FROM Activity WHERE activity_id = %s", (activity_id,))
            activity = cursor.fetchone()

            if not activity:
                cursor.close()
                conn.close()
                return "Invalid Activity ID. Please try again."

            # Option Handling
            if action == 'save':
                try:
                    cursor.execute("DELETE FROM Activity WHERE activity_id = %s", (activity_id,))
                    conn.commit()
                    message = "Activity successfully deleted!"
                except mysql.connector.Error as err:
                    message = f"An error occurred: {err}"
                finally:
                    cursor.close()
                    conn.close()
                    return message

            elif action == 'cancel':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_modify_content_block', section_id=activity[3]))  # Assuming section_id is stored in the 4th column

        # Render the Delete Activity form on GET request
        return render_template('faculty_delete_activity.html', activity_id=activity_id)
    else:
        return redirect(url_for('login', user_type='faculty'))

@app.route('/faculty_add_question/<activity_id>', methods=['GET', 'POST'])
def faculty_add_question(activity_id):
    if 'role' in session and session['role'] == 'faculty':
        if request.method == 'POST':
            action = request.form.get('action')
            question_id = request.form.get('question_id')
            question_text = request.form.get('question_text')
            option_1 = request.form.get('option_1')
            explanation_1 = request.form.get('explanation_1')
            option_2 = request.form.get('option_2')
            explanation_2 = request.form.get('explanation_2')
            option_3 = request.form.get('option_3')
            explanation_3 = request.form.get('explanation_3')
            option_4 = request.form.get('option_4')
            explanation_4 = request.form.get('explanation_4')
            answer = request.form.get('answer')

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Validate if the question ID already exists
            cursor.execute("SELECT * FROM Question WHERE question_id = %s", (question_id,))
            existing_question = cursor.fetchone()

            if existing_question:
                cursor.close()
                conn.close()
                return "Question ID already exists. Please use a unique Question ID."

            # Option Handling
            if action == 'cancel':
                cursor.close()
                conn.close()
                return redirect(url_for('faculty_add_activity', content_block_id=session.get('content_block_id')))

            elif action == 'save':
                try:
                    # Insert the new question record into the database
                    cursor.execute("""
                        INSERT INTO Question (question_id, question_text, option_1, explanation_1, option_2, explanation_2,
                        option_3, explanation_3, option_4, explanation_4, answer, activity_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (question_id, question_text, option_1, explanation_1, option_2, explanation_2,
                          option_3, explanation_3, option_4, explanation_4, answer, activity_id))
                    conn.commit()

                    return "Question added successfully!"
                except mysql.connector.Error as err:
                    return f"An error occurred: {err}"
                finally:
                    cursor.close()
                    conn.close()

        # Render the Add Question form on GET request
        return render_template('faculty_add_question.html', activity_id=activity_id)
    else:
        return redirect(url_for('login', user_type='faculty'))
@app.route('/login/ta', methods=['GET', 'POST'])
def login_ta():
    if request.method == 'POST':
        action = request.form.get('action')

        # If TA chooses to go back, redirect to home
        if action == 'go_back':
            return redirect(url_for('home'))

        # If TA chooses to sign in, validate credentials
        elif action == 'sign_in':
            user_id = request.form.get('user_id')
            password = request.form.get('password')

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to check TA login credentials
            cursor.execute("SELECT * FROM User WHERE user_id = %s AND password = %s AND role = 'ta'", (user_id, password))
            user = cursor.fetchone()

            # Close the database connection
            cursor.close()
            conn.close()

            if user:
                # Store TA details in session
                session['user_id'] = user[0]
                session['role'] = 'ta'

                # Redirect to TA landing page
                return redirect(url_for('ta_home'))
            else:
                # Incorrect login credentials
                return "Login Incorrect. Please try again."

    # Render the TA login page on GET request or form submission failure
    return render_template('login_ta.html')

@app.route('/ta_home')
def ta_home():
    if 'role' in session and session['role'] == 'ta':
        return render_template('ta_home.html')
    else:
        return redirect(url_for('login_ta'))

@app.route('/ta_active_course', methods=['GET', 'POST'])
def ta_active_course():
    if 'role' in session and session['role'] == 'ta':
        if request.method == 'POST':
            action = request.form.get('action')
            course_id = request.form.get('course_id')

            # Validate the Course ID
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT course_id FROM ActiveCourse WHERE course_id = %s", (course_id,))
            course = cursor.fetchone()
            cursor.close()
            conn.close()

            if not course:
                return "Invalid Course ID. Please enter a valid Course ID."

            # Action Handling
            if action == 'view_students':
                return redirect(url_for('ta_view_students', course_id=course_id))
            elif action == 'add_new_chapter':
                return redirect(url_for('ta_add_new_chapter', course_id=course_id))
            elif action == 'modify_chapters':
                return redirect(url_for('ta_modify_chapters', course_id=course_id))
            elif action == 'go_back':
                return redirect(url_for('ta_home'))

        # Render the TA Active Course page on GET request
        return render_template('ta_active_course.html')
    else:
        return redirect(url_for('login_ta'))
@app.route('/ta_view_courses', methods=['GET', 'POST'])
def ta_view_courses():
    if 'role' in session and session['role'] == 'ta':
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'go_back':
                return redirect(url_for('ta_home'))

        # Retrieve courses assigned to the TA from the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT course_id, course_name FROM ActiveCourse
            WHERE ta_id = %s
        """, (session['user_id'],))
        courses = cursor.fetchall()
        cursor.close()
        conn.close()

        # Render the courses in the template
        return render_template('ta_view_courses.html', courses=courses)
    else:
        return redirect(url_for('login', user_type='ta'))
@app.route('/ta_change_password', methods=['GET', 'POST'])
def ta_change_password():
    if 'role' in session and session['role'] == 'ta':
        if request.method == 'POST':
            action = request.form.get('action')
            
            # Handle "Go Back" option
            if action == 'go_back':
                return redirect(url_for('ta_home'))

            # Handle password update
            if action == 'update_password':
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')

                # Verify new password confirmation
                if new_password != confirm_password:
                    return "New passwords do not match. Please try again."

                # Connect to the database
                conn = get_db_connection()
                cursor = conn.cursor()

                # Verify current password
                cursor.execute("SELECT password FROM User WHERE user_id = %s AND role = 'ta'", (session['user_id'],))
                result = cursor.fetchone()
                
                if result is None or result[0] != current_password:
                    cursor.close()
                    conn.close()
                    return "Current password is incorrect. Please try again."

                # Update password in the database
                try:
                    cursor.execute("UPDATE User SET password = %s WHERE user_id = %s AND role = 'ta'", (new_password, session['user_id']))
                    conn.commit()
                    message = "Password successfully updated!"
                except mysql.connector.Error as err:
                    message = f"An error occurred: {err}"
                finally:
                    cursor.close()
                    conn.close()

                return message

        # Render the Change Password form on GET request
        return render_template('ta_change_password.html')
    else:
        return redirect(url_for('login', user_type='ta'))
@app.route('/ta_view_students', methods=['GET', 'POST'])
def ta_view_students():
    if 'role' in session and session['role'] == 'ta':
        # Assuming course_id is stored in the session or passed as a parameter
        course_id = session.get('course_id')

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve the list of students in the course
        cursor.execute("""
            SELECT student_id, first_name, last_name, email 
            FROM Student
            WHERE course_id = %s
        """, (course_id,))
        students = cursor.fetchall()

        cursor.close()
        conn.close()

        if request.method == 'POST':
            # Go back to the previous page when "Go Back" is selected
            action = request.form.get('action')
            if action == 'go_back':
                return redirect(url_for('ta_active_course'))

        # Render the students list template on GET request
        return render_template('ta_view_students.html', students=students)
    else:
        return redirect(url_for('login', user_type='ta'))
@app.route('/ta_add_new_chapter', methods=['GET', 'POST'])
def ta_add_new_chapter():
    if 'role' in session and session['role'] == 'ta':
        course_id = session.get('course_id')  # Assume course_id is stored in session

        if request.method == 'POST':
            action = request.form.get('action')

            # Handle Go Back action
            if action == 'go_back':
                return redirect(url_for('ta_active_course'))

            # Handle Add New Chapter action
            elif action == 'add_new_chapter':
                chapter_id = request.form.get('chapter_id')
                chapter_title = request.form.get('chapter_title')

                # Validate input
                if not chapter_id or not chapter_title:
                    return "Chapter ID and Title are required."

                # Connect to the database
                conn = get_db_connection()
                cursor = conn.cursor()

                try:
                    # Insert the new chapter into the database
                    cursor.execute("""
                        INSERT INTO Chapter (chapter_id, title, course_id)
                        VALUES (%s, %s, %s)
                    """, (chapter_id, chapter_title, course_id))
                    conn.commit()

                    return "Chapter added successfully!"
                except mysql.connector.Error as err:
                    return f"An error occurred: {err}"
                finally:
                    cursor.close()
                    conn.close()

        # Render the Add New Chapter form on GET request
        return render_template('ta_add_new_chapter.html')
    else:
        return redirect(url_for('login', user_type='ta'))
@app.route('/ta_modify_chapter', methods=['GET', 'POST'])
def ta_modify_chapter():
    if 'role' in session and session['role'] == 'ta':
        if request.method == 'POST':
            action = request.form.get('action')
            chapter_id = request.form.get('chapter_id')

            # Validate input
            if not chapter_id:
                return "Chapter ID is required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the chapter exists
            cursor.execute("SELECT * FROM Chapter WHERE chapter_id = %s", (chapter_id,))
            chapter = cursor.fetchone()

            if not chapter:
                cursor.close()
                conn.close()
                return "Invalid Chapter ID. Please try again."

            # Handle actions based on the menu
            if action == 'go_back':
                cursor.close()
                conn.close()
                return redirect(url_for('ta_active_course'))

            elif action == 'add_new_section':
                cursor.close()
                conn.close()
                return redirect(url_for('ta_add_new_section', chapter_id=chapter_id))

            elif action == 'add_new_activity':
                cursor.close()
                conn.close()
                return redirect(url_for('ta_add_new_activity', chapter_id=chapter_id))

            # Close connection after action handling
            cursor.close()
            conn.close()

        # Render the Modify Chapter form on GET request
        return render_template('ta_modify_chapter.html')
    else:
        return redirect(url_for('login', user_type='ta'))
@app.route('/ta_add_new_section/<chapter_id>', methods=['GET', 'POST'])
def ta_add_new_section(chapter_id):
    if 'role' in session and session['role'] == 'ta':
        if request.method == 'POST':
            action = request.form.get('action')
            section_number = request.form.get('section_number')

            # Validate input
            if not section_number:
                return "Section number is required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the section number already exists in the chapter
            cursor.execute("SELECT * FROM Section WHERE section_num = %s AND chapter_id = %s", (section_number, chapter_id))
            existing_section = cursor.fetchone()

            if existing_section:
                cursor.close()
                conn.close()
                return "A section with this number already exists in this chapter. Please use a different section number."

            # Handle action for adding a content block
            if action == 'add_content_block':
                # Insert the new section into the database
                try:
                    cursor.execute("INSERT INTO Section (section_num, chapter_id) VALUES (%s, %s)", (section_number, chapter_id))
                    conn.commit()
                    section_id = cursor.lastrowid  # Capture the new section ID

                    cursor.close()
                    conn.close()
                    return redirect(url_for('ta_add_new_content_block', section_id=section_id))

                except mysql.connector.Error as err:
                    cursor.close()
                    conn.close()
                    return f"An error occurred: {err}"

            elif action == 'go_back':
                cursor.close()
                conn.close()
                return redirect(url_for('ta_modify_chapter', chapter_id=chapter_id))

        # Render the Add New Section form on GET request
        return render_template('ta_add_new_section.html', chapter_id=chapter_id)
    else:
        return redirect(url_for('login', user_type='ta'))
@app.route('/ta_add_new_content_block/<section_id>', methods=['GET', 'POST'])
def ta_add_new_content_block(section_id):
    if 'role' in session and session['role'] == 'ta':
        if request.method == 'POST':
            action = request.form.get('action')
            content_block_id = request.form.get('content_block_id')

            # Validate input for content block ID
            if not content_block_id:
                return "Content Block ID is required."

            # Handle actions based on the selected option
            if action == 'add_text':
                return redirect(url_for('ta_add_text', content_block_id=content_block_id))
            elif action == 'add_picture':
                return redirect(url_for('ta_add_picture', content_block_id=content_block_id))
            elif action == 'add_activity':
                return redirect(url_for('ta_add_activity', content_block_id=content_block_id))
            elif action == 'hide_activity':
                return redirect(url_for('ta_hide_activity', content_block_id=content_block_id))
            elif action == 'go_back':
                return redirect(url_for('ta_add_new_section', chapter_id=session['chapter_id']))

        # Render the Add New Content Block form on GET request
        return render_template('ta_add_new_content_block.html', section_id=section_id)
    else:
        return redirect(url_for('login', user_type='ta'))
@app.route('/ta_add_text/<content_block_id>', methods=['GET', 'POST'])
def ta_add_text(content_block_id):
    if 'role' in session and session['role'] == 'ta':
        if request.method == 'POST':
            action = request.form.get('action')
            text_content = request.form.get('text_content')

            # Handle Add action
            if action == 'add':
                if not text_content:
                    return "Text content is required."
                
                # Connect to the database and add text content
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO ContentBlock (contentblock_id, content, content_type)
                        VALUES (%s, %s, 'text')
                    """, (content_block_id, text_content))
                    conn.commit()
                    return redirect(url_for('ta_add_new_content_block', section_id=session['section_id']))
                except mysql.connector.Error as err:
                    return f"An error occurred: {err}"
                finally:
                    cursor.close()
                    conn.close()

            # Handle Go Back action
            elif action == 'go_back':
                return redirect(url_for('ta_add_new_content_block', section_id=session['section_id']))

        # Render the Add Text form on GET request
        return render_template('ta_add_text.html', content_block_id=content_block_id)
    else:
        return redirect(url_for('login', user_type='ta'))

@app.route('/ta_add_picture/<contentblock_id>', methods=['GET', 'POST'])
def ta_add_picture(contentblock_id):
    # Check if the user is logged in as TA
    if 'role' not in session or session['role'] != 'ta':
        return redirect(url_for('login', user_type='ta'))

    # Connect to the database to check if the content block exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (contentblock_id,))
    existing_contentblock = cursor.fetchone()

    if not existing_contentblock:
        # If contentblock_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Content Block ID does not exist. Please enter a valid Content Block ID."

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" action
        if action == 'go_back':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_add_new_content_block', section_id=session['section_id']))

        # Handle "Landing Page" action (optional, depends on your app structure)
        if action == 'landing_page':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_home'))

        # Handle adding the picture content
        if action == 'add_picture':
            picture_url = request.form.get('picture_url')

            if not picture_url:
                cursor.close()
                conn.close()
                return "Picture URL is required."

            try:
                # Update the content block with the new picture URL
                cursor.execute("""
                    UPDATE ContentBlock
                    SET content = %s, content_type = 'picture'
                    WHERE contentblock_id = %s
                """, (picture_url, contentblock_id))
                conn.commit()

                return "Picture content added successfully!"
            except mysql.connector.Error as err:
                return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    cursor.close()
    conn.close()
    return render_template('ta_add_picture.html', contentblock_id=contentblock_id)
@app.route('/ta_add_activity/<activity_id>', methods=['GET', 'POST'])
def ta_add_activity(activity_id):
    # Check if the user is logged in as TA
    if 'role' not in session or session['role'] != 'ta':
        return redirect(url_for('login', user_type='ta'))

    # Connect to the database to check if the activity exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Activity WHERE activity_id = %s", (activity_id,))
    existing_activity = cursor.fetchone()

    if not existing_activity:
        # If activity_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Activity ID does not exist. Please enter a valid Activity ID."

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" action
        if action == 'go_back':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_modify_chapter', chapter_id=session.get('chapter_id')))

        # Handle "Add Question" action
        if action == 'add_question':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_add_question', activity_id=activity_id))

    cursor.close()
    conn.close()
    return render_template('ta_add_activity.html', activity_id=activity_id)
@app.route('/ta_add_question/<activity_id>', methods=['GET', 'POST'])
def ta_add_question(activity_id):
    # Check if the user is logged in as TA
    if 'role' not in session or session['role'] != 'ta':
        return redirect(url_for('login', user_type='ta'))

    # Check if the activity_id is valid
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Activity WHERE activity_id = %s", (activity_id,))
    existing_activity = cursor.fetchone()

    if not existing_activity:
        # If activity_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Activity ID does not exist. Please enter a valid Activity ID."

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Cancel" action
        if action == 'cancel':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_add_activity', activity_id=activity_id))

        # Handle "Save" action
        if action == 'save':
            # Collect question details from form data
            question_id = request.form.get('question_id')
            question_text = request.form.get('question_text')
            option_1 = request.form.get('option_1')
            option_1_explanation = request.form.get('option_1_explanation')
            option_2 = request.form.get('option_2')
            option_2_explanation = request.form.get('option_2_explanation')
            option_3 = request.form.get('option_3')
            option_3_explanation = request.form.get('option_3_explanation')
            option_4 = request.form.get('option_4')
            option_4_explanation = request.form.get('option_4_explanation')
            answer = request.form.get('answer')

            if not (question_id and question_text and option_1 and option_2 and option_3 and option_4 and answer):
                cursor.close()
                conn.close()
                return "All fields are required. Please provide complete information."

            try:
                # Insert question into the database
                cursor.execute("""
                    INSERT INTO Question (question_id, activity_id, question_text, option_1, option_1_explanation, option_2, 
                                          option_2_explanation, option_3, option_3_explanation, option_4, option_4_explanation, answer)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (question_id, activity_id, question_text, option_1, option_1_explanation, option_2, option_2_explanation, 
                      option_3, option_3_explanation, option_4, option_4_explanation, answer))
                conn.commit()

                return "Question added successfully!"

            except mysql.connector.Error as err:
                return f"An error occurred: {err}"

            finally:
                cursor.close()
                conn.close()

    cursor.close()
    conn.close()
    return render_template('ta_add_question.html', activity_id=activity_id)
@app.route('/ta_modify_section/<section_id>', methods=['GET', 'POST'])
def ta_modify_section(section_id):
    # Check if the user is logged in as TA
    if 'role' not in session or session['role'] != 'ta':
        return redirect(url_for('login', user_type='ta'))

    # Connect to the database to check if the section exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Section WHERE section_id = %s", (section_id,))
    section = cursor.fetchone()

    if not section:
        # If section_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Section ID does not exist. Please enter a valid Section ID."

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" action
        if action == 'go_back':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_landing_page'))  # Adjust this to the TA landing page route

        # Handle "Add New Content Block" action
        elif action == 'add_new_content_block':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_add_new_content_block', section_id=section_id))

        # Handle "Modify Content Block" action
        elif action == 'modify_content_block':
            contentblock_id = request.form.get('contentblock_id')
            cursor.close()
            conn.close()
            return redirect(url_for('ta_modify_content_block', section_id=section_id, contentblock_id=contentblock_id))

        # Handle "Delete Content Block" action
        elif action == 'delete_content_block':
            contentblock_id = request.form.get('contentblock_id')
            cursor.close()
            conn.close()
            return redirect(url_for('ta_delete_content_block', section_id=section_id, contentblock_id=contentblock_id))

        # Handle "Hide Content Block" action
        elif action == 'hide_content_block':
            contentblock_id = request.form.get('contentblock_id')
            cursor.close()
            conn.close()
            return redirect(url_for('ta_hide_content_block', section_id=section_id, contentblock_id=contentblock_id))

    cursor.close()
    conn.close()
    return render_template('ta_modify_section.html', section=section)
@app.route('/ta_modify_content_block/<section_id>/<contentblock_id>', methods=['GET', 'POST'])
def ta_modify_content_block(section_id, contentblock_id):
    # Check if the user is logged in as TA
    if 'role' not in session or session['role'] != 'ta':
        return redirect(url_for('login', user_type='ta'))

    # Connect to the database to check if the content block exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (contentblock_id,))
    content_block = cursor.fetchone()

    if not content_block:
        # If contentblock_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Content Block ID does not exist. Please enter a valid Content Block ID."

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" action
        if action == 'go_back':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_modify_section', section_id=section_id))

        # Handle "Landing Page" action
        if action == 'landing_page':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_landing_page'))

        # Handle adding text to the content block
        elif action == 'add_text':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_add_text', contentblock_id=contentblock_id))

        # Handle adding a picture to the content block
        elif action == 'add_picture':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_add_picture', contentblock_id=contentblock_id))

        # Handle adding an activity to the content block
        elif action == 'add_activity':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_add_activity', contentblock_id=contentblock_id))

    cursor.close()
    conn.close()
    return render_template('ta_modify_content_block.html', contentblock_id=contentblock_id)
@app.route('/ta_delete_content_block/<contentblock_id>', methods=['GET', 'POST'])
def ta_delete_content_block(contentblock_id):
    # Check if the user is logged in as a TA
    if 'role' not in session or session['role'] != 'ta':
        return redirect(url_for('login', user_type='ta'))

    # Connect to the database to check if the content block exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (contentblock_id,))
    content_block = cursor.fetchone()

    if not content_block:
        # If contentblock_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Content Block ID does not exist. Please enter a valid Content Block ID."

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" action
        if action == 'go_back':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_modify_section', section_id=session.get('section_id')))

        # Handle "Delete" action
        elif action == 'delete':
            try:
                # Delete the content block from the database
                cursor.execute("DELETE FROM ContentBlock WHERE contentblock_id = %s", (contentblock_id,))
                conn.commit()

                cursor.close()
                conn.close()
                return "Content block deleted successfully!"
            except mysql.connector.Error as err:
                cursor.close()
                conn.close()
                return f"An error occurred: {err}"

    cursor.close()
    conn.close()
    return render_template('ta_delete_content_block.html', contentblock_id=contentblock_id)
@app.route('/ta_hide_content_block/<contentblock_id>', methods=['GET', 'POST'])
def ta_hide_content_block(contentblock_id):
    # Check if the user is logged in as a TA
    if 'role' not in session or session['role'] != 'ta':
        return redirect(url_for('login', user_type='ta'))

    # Connect to the database to check if the content block exists
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ContentBlock WHERE contentblock_id = %s", (contentblock_id,))
    content_block = cursor.fetchone()

    if not content_block:
        # If contentblock_id does not exist, close the connection and show an error message
        cursor.close()
        conn.close()
        return "The specified Content Block ID does not exist. Please enter a valid Content Block ID."

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" action
        if action == 'go_back':
            cursor.close()
            conn.close()
            return redirect(url_for('ta_modify_section', section_id=session.get('section_id')))

        # Handle "Hide" action
        elif action == 'hide':
            try:
                # Update the content block to set it as hidden
                cursor.execute("UPDATE ContentBlock SET is_hidden = 1 WHERE contentblock_id = %s", (contentblock_id,))
                conn.commit()

                cursor.close()
                conn.close()
                return "Content block hidden successfully!"
            except mysql.connector.Error as err:
                cursor.close()
                conn.close()
                return f"An error occurred: {err}"

    cursor.close()
    conn.close()
    return render_template('ta_hide_content_block.html', contentblock_id=contentblock_id)
@app.route('/student_login_menu', methods=['GET', 'POST'])
def student_login_menu():
    # If the request is POST, process the selected action
    if request.method == 'POST':
        action = request.form.get('action')

        # Redirect to appropriate pages based on the user's choice
        if action == 'enroll_in_course':
            return redirect(url_for('enroll_in_course'))

        elif action == 'sign_in':
            return redirect(url_for('student_sign_in'))

        elif action == 'go_back':
            return redirect(url_for('home'))  # Assuming 'home' is the homepage route

    # Render the login menu for students on a GET request
    return render_template('student_login_menu.html')

@app.route('/enroll_in_course', methods=['GET', 'POST'])
def enroll_in_course():
    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" action
        if action == 'go_back':
            return redirect(url_for('student_login_menu'))

        # Handle "Enroll" action
        if action == 'enroll':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            course_token = request.form.get('course_token')

            # Validate all fields
            if not (first_name and last_name and email and course_token):
                return "All fields are required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the student is already registered
            cursor.execute("SELECT student_id FROM Students WHERE email = %s", (email,))
            student = cursor.fetchone()

            if not student:
                # Register a new student
                cursor.execute("INSERT INTO Students (first_name, last_name, email) VALUES (%s, %s, %s)", 
                               (first_name, last_name, email))
                conn.commit()
                cursor.execute("SELECT LAST_INSERT_ID()")  # Retrieve the new student_id
                student_id = cursor.fetchone()[0]
            else:
                # Use existing student_id
                student_id = student[0]

            # Add to the waiting list for the specified course
            try:
                cursor.execute("INSERT INTO WaitingList (student_id, course_token) VALUES (%s, %s)", 
                               (student_id, course_token))
                conn.commit()
                message = "Enrollment request submitted successfully! You've been added to the waiting list."
            except mysql.connector.Error as err:
                message = f"An error occurred: {err}"

            cursor.close()
            conn.close()

            return message

    # Render the enrollment form on GET request
    return render_template('enroll_in_course.html')
@app.route('/student_sign_in', methods=['GET', 'POST'])
def student_sign_in():
    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" action
        if action == 'go_back':
            return redirect(url_for('home_page'))

        # Handle "Sign-In" action
        if action == 'sign_in':
            user_id = request.form.get('user_id')
            password = request.form.get('password')

            # Validate inputs
            if not user_id or not password:
                return "Both User ID and Password are required."

            # Connect to the database
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check credentials in the database
            cursor.execute("SELECT * FROM Students WHERE user_id = %s AND password = %s", (user_id, password))
            student = cursor.fetchone()

            cursor.close()
            conn.close()

            if student:
                # Store user details in the session and redirect to the landing page
                session['user_id'] = student[0]  # Assuming the user_id is the first column in Students table
                session['role'] = 'student'
                return redirect(url_for('student_landing_page'))
            else:
                # Display error message for invalid credentials
                return "Login Incorrect. Please try again."

    # Render the login form on GET request
    return render_template('student_sign_in.html')
@app.route('/student_landing_page', methods=['GET', 'POST'])
def student_landing_page():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('student_sign_in'))

    # Connect to the database to retrieve e-book, chapter, section, and block data
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the hierarchical content structure to display on the landing page
    cursor.execute("""
        SELECT e.book_id, e.title AS ebook_title, c.chapter_id, c.title AS chapter_title,
               s.section_id, s.title AS section_title, b.block_id, b.title AS block_title
        FROM Ebooks e
        JOIN Chapters c ON e.book_id = c.book_id
        JOIN Sections s ON c.chapter_id = s.chapter_id
        JOIN Blocks b ON s.section_id = b.section_id
        ORDER BY e.book_id, c.chapter_id, s.section_id, b.block_id
    """)
    content_structure = cursor.fetchall()

    cursor.close()
    conn.close()

    if request.method == 'POST':
        action = request.form.get('action')

        # Option to view a section
        if action == 'view_section':
            return redirect(url_for('view_section'))

        # Option to view participation activity points
        elif action == 'view_participation':
            return redirect(url_for('view_participation_activity_point'))

        # Option to logout
        elif action == 'logout':
            session.clear()
            return redirect(url_for('home_page'))

    return render_template('student_landing_page.html', content_structure=content_structure)
@app.route('/view_section', methods=['GET', 'POST'])
def view_section():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('student_sign_in'))

    if request.method == 'POST':
        action = request.form.get('action')
        chapter_id = request.form.get('chapter_id')
        section_id = request.form.get('section_id')

        # Go Back action
        if action == 'go_back':
            return redirect(url_for('student_landing_page'))

        # Validate Chapter ID and Section ID and proceed to View Block
        if action == 'view_block':
            if not chapter_id or not section_id:
                return "Chapter ID and Section ID are required."

            # Connect to the database to check if the section exists
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM Sections
                WHERE chapter_id = %s AND section_id = %s
            """, (chapter_id, section_id))
            section = cursor.fetchone()
            cursor.close()
            conn.close()

            if section:
                # Redirect to View Block with section details
                return redirect(url_for('view_block', chapter_id=chapter_id, section_id=section_id))
            else:
                return "Invalid Chapter ID or Section ID. Please try again."

    return render_template('view_section.html')
@app.route('/view_block/<chapter_id>/<section_id>/<block_id>', methods=['GET', 'POST'])
def view_block(chapter_id, section_id, block_id):
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('student_sign_in'))

    # Connect to the database to retrieve the block details
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT block_id, content, block_type, correct_answer, explanation
        FROM ContentBlock
        WHERE chapter_id = %s AND section_id = %s AND block_id = %s
    """, (chapter_id, section_id, block_id))
    block = cursor.fetchone()
    cursor.close()
    conn.close()

    if not block:
        return "Invalid Block ID. Please check your input and try again."

    block_type = block[2]  # "content" or "activity"
    correct_answer = block[3]
    explanation = block[4]

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle "Go Back" action
        if action == 'go_back':
            return redirect(url_for('view_section'))

        # Handle "Next/Submit" action
        if action == 'next_submit':
            if block_type == 'activity':
                selected_answer = request.form.get('selected_answer')

                # Check if answer is correct
                if selected_answer == correct_answer:
                    feedback = "Correct! " + explanation
                else:
                    feedback = "Incorrect. " + explanation

                # Redirect to the next block or return to landing page if last block
                next_block_id = get_next_block_id(chapter_id, section_id, block_id)
                if next_block_id:
                    return redirect(url_for('view_block', chapter_id=chapter_id, section_id=section_id, block_id=next_block_id))
                else:
                    return redirect(url_for('student_landing_page'))
            else:
                # If content, simply go to the next block
                next_block_id = get_next_block_id(chapter_id, section_id, block_id)
                if next_block_id:
                    return redirect(url_for('view_block', chapter_id=chapter_id, section_id=section_id, block_id=next_block_id))
                else:
                    return redirect(url_for('student_landing_page'))

    return render_template('view_block.html', block=block, block_type=block_type)
def get_next_block_id(chapter_id, section_id, current_block_id):
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query to get the next block in sequence
    cursor.execute("""
        SELECT block_id
        FROM ContentBlock
        WHERE chapter_id = %s AND section_id = %s AND block_id > %s
        ORDER BY block_id ASC
        LIMIT 1
    """, (chapter_id, section_id, current_block_id))
    
    next_block = cursor.fetchone()

    # Close the database connection
    cursor.close()
    conn.close()

    # If there's a next block, return its ID; otherwise, return None
    return next_block[0] if next_block else None
@app.route('/student/view_participation_points')
def view_participation_points():
    # Check if the user is logged in as a student
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login', user_type='student'))
    
    student_id = session.get('user_id')

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve the participation activity points for the student
    cursor.execute("""
        SELECT participation_points
        FROM StudentParticipation
        WHERE student_id = %s
    """, (student_id,))
    
    participation_points = cursor.fetchone()

    # Close the connection
    cursor.close()
    conn.close()

    # Check if participation points are found
    if participation_points:
        points = participation_points[0]
    else:
        points = "No participation data available."

    # Render the template with the participation points
    return render_template('view_participation_points.html', points=points)


if __name__ == '__main__':
    app.run(debug=True)
