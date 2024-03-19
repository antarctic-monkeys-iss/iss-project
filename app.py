from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, send_file
from flask_mysqldb import MySQL
import jwt
import bcrypt
from werkzeug.utils import secure_filename
from datetime import datetime
import traceback
import io
import base64

app = Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MySQL
mysql = MySQL(app)

# Secret key for JWT
app.config['SECRET_KEY'] = 'your_secret_key'

# Landing page
@app.route('/')
def landing():
    # Check if user is logged in
    if 'token' in request.cookies:
        token = request.cookies['token']
        try:
            # Verify token
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            email = decoded_token['email']

            # If user is logged in, redirect to index page
            return redirect(url_for('index'))
        except jwt.ExpiredSignatureError:
            # Token expired, handle refresh or reauthentication
            return redirect(url_for('login'))
        except jwt.InvalidTokenError:
            # Invalid token
            return redirect(url_for('login'))
    else:
        # If user is not logged in, redirect to login page
        return redirect(url_for('login'))


# Signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Hash password with bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert user into the database
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (name, hashed_password, email))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('index'))

    return render_template('signup.html')


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == 'admin@admin.com' and password == 'admin':
            return redirect(url_for('admin'))

        # Retrieve user from database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # Generate JWT token upon successful login
            token = jwt.encode({'email': email}, app.config['SECRET_KEY'], algorithm='HS256')

            # Set token as a cookie
            response = make_response(redirect(url_for('index')))
            response.set_cookie('token', token)

            return response
        else:
            return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')


# Index page
@app.route('/index')
def index():
    try:
        # Retrieve token from cookie
        token = request.cookies.get('token')

        if token:
            # Verify token
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            email = decoded_token['email']

            # Connect to the database
            cur = mysql.connection.cursor()

            # Execute the query to retrieve all image content
            cur.execute("SELECT image_name, image_content FROM images WHERE email = %s", (email,))
            image_data = cur.fetchall()

            # Close the database connection
            cur.close()

            if image_data:
                images = [base64.b64encode(row['image_content']).decode('utf-8') for row in image_data]
                titles = [row['image_name'] for row in image_data]
                zipped_data = zip(images, titles)
                return render_template('index.html', email=email, zipped_data=zipped_data)
            else:
                return render_template('index.html', email=email, error='No images found')
        else:
            # No token found, redirect to login page
            return redirect(url_for('login'))
    except jwt.ExpiredSignatureError:
        # Token expired, handle refresh or reauthentication
        return redirect(url_for('login'))
    except jwt.InvalidTokenError:
        # Invalid token
        return redirect(url_for('login'))
    except Exception as e:
        traceback.print_exc()
        print(e)  # Add this line to print the exception details
        return render_template('index.html', error='Internal Server Error')

# Sign out
@app.route('/signout')
def signout():
    # Remove token cookie
    response = make_response(redirect(url_for('login')))
    response.set_cookie('token', '', expires=0)

    return response

# Function to get the next serial number (id)
def get_next_serial_number():
    try:
        # Connect to the database
        cur = mysql.connection.cursor()

        # Execute the query to get all serial numbers (id)
        cur.execute("SELECT id FROM images")
        
        # Fetch all serial numbers
        serial_numbers = cur.fetchall()

        # Close the database connection
        cur.close()

        # Find the highest integer that doesn't occur in the serial numbers
        existing_numbers = set(serial_number['id'] for serial_number in serial_numbers)
        highest_available_number = 1

        while highest_available_number in existing_numbers:
            highest_available_number += 1

        return highest_available_number

    except Exception as e:
        traceback.print_exc()
        return None
    
def get_song_serial_number():
    try:
        # Connect to the database
        cur = mysql.connection.cursor()

        # Execute the query to get all serial numbers (id)
        cur.execute("SELECT id FROM songs")
        
        # Fetch all serial numbers
        serial_numbers = cur.fetchall()

        # Close the database connection
        cur.close()

        # Find the highest integer that doesn't occur in the serial numbers
        existing_numbers = set(serial_number['id'] for serial_number in serial_numbers)
        highest_available_number = 1

        while highest_available_number in existing_numbers:
            highest_available_number += 1

        return highest_available_number

    except Exception as e:
        traceback.print_exc()
        return None


# Existing route
@app.route('/upload-images', methods=['POST'])
def upload_images():
    token = request.cookies.get('token')

    if token:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        email = decoded_token['email']

    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400

        images = request.files.getlist('images')
        names = request.form.getlist('names')  # Get the list of names

        uploaded_paths = []

        for i in range(len(images)):
            image = images[i]
            serial_number = get_next_serial_number()
            image_content = image.read()

            try:
                cur = mysql.connection.cursor()

                # Execute the query to insert image information with the image content and name
                cur.execute("""
                    INSERT INTO images (id, image_name, image_content, email, time_of_upload)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (serial_number, names[i], image_content, email))

                cur.execute("""
                    DELETE n2 FROM images n1, images n2
                    WHERE n1.id > n2.id
                    AND n1.image_content = n2.image_content
                    AND n1.email = n2.email
                """)

                mysql.connection.commit()
                cur.close()

            except Exception as db_error:
                traceback.print_exc()
                return jsonify({'error': 'Failed to insert into database'}), 500

            uploaded_paths.append({'serial_number': serial_number, 'status': 'success'})

        print(f"Images uploaded to database with serial numbers: {[path['serial_number'] for path in uploaded_paths]}")

        return jsonify({'message': 'Images uploaded successfully', 'uploaded_paths': uploaded_paths})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error'}), 500

    
# New route to display uploaded images
@app.route('/uploaded-images')
def uploaded_images():
    token = request.cookies.get('token')

    if token:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        email = decoded_token['email']
    
    try:
        # Connect to the database
        cur = mysql.connection.cursor()

        # Execute the query to retrieve images for the logged-in user
        cur.execute("""
            SELECT id, time_of_upload
            FROM images
            WHERE email = %s
        """, (email,))

        # Fetch all the images
        images = cur.fetchall()

        # Close the database connection
        cur.close()

        return render_template('uploaded_images.html', images=images)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error'}), 500

# New route to get image content
@app.route('/get-image/<int:image_id>')
def get_image(image_id):
    try:
        # Connect to the database
        cur = mysql.connection.cursor()

        # Execute the query to retrieve image content
        cur.execute("""
            SELECT image_content
            FROM images
            WHERE id = %s
        """, (image_id,))

        # Fetch the image content
        image_data = cur.fetchone()

        # Close the database connection
        cur.close()

        if image_data:
            # Create an in-memory file-like object for the image content
            image_content = io.BytesIO(image_data['image_content'])

            # Send the image file as a response
            return send_file(image_content, mimetype='image/jpeg')  # Adjust mimetype based on your image format

        return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error'}), 500
        

@app.route('/upload-song', methods=['POST'])
def upload_song():
    token = request.cookies.get('token')

    if token:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        email = decoded_token['email']

    try:
        song_name = request.form.get('song_name')
        song_content = request.files['song_content'].read()
        song_number = get_song_serial_number()

        # Insert song information into the database
        try:
            cur = mysql.connection.cursor()

            # Execute the query to insert song information with the song content
            cur.execute("""
                INSERT INTO songs (id, song_name, song_content, email)
                VALUES (%s, %s, %s, %s)
            """, (song_number, song_name, song_content, email))

            cur.execute("""
                    DELETE n1 FROM songs n1, songs n2
                    WHERE n1.id > n2.id
                    AND n1.song_content = n2.song_content
                    AND n1.email = n2.email
                """)

            # Commit the transaction
            mysql.connection.commit()

            # Close the database connection
            cur.close()

            return jsonify({'status': 'success', 'message': f'Successfully uploaded {song_name}'})

        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Error uploading song: {str(e)}'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error decoding token: {str(e)}'}), 401
    
@app.route('/remove-song', methods=['POST'])
def remove_song():
    token = request.cookies.get('token')

    if token:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        email = decoded_token['email']

    try:
        song_name = request.form.get('song_name')
        song_content = request.files['song_content'].read()
        song_number = get_song_serial_number()

        # Insert song information into the database
        try:
            cur = mysql.connection.cursor()

            # Execute the query to insert song information with the song content
            cur.execute("""
                DELETE FROM songs WHERE song_content = (%s)AND email = (%s);
            """, (song_content, email))

            # Commit the transaction
            mysql.connection.commit()

            # Close the database connection
            cur.close()

            return jsonify({'status': 'success', 'message': f'Successfully uploaded {song_name}'})

        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Error uploading song: {str(e)}'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error decoding token: {str(e)}'}), 401

@app.route('/admin')
def admin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, email FROM users")
    users = cur.fetchall()
    cur.close()
    return render_template('admin.html', users=users)

@app.route('/remove-item-from-gallery', methods=['POST'])
def remove_from_gallery():
    token = request.cookies.get('token')

    if token:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        email = decoded_token['email']

    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400

        images = request.files.getlist('images')
        deleted_paths = []

        for i in range(len(images)):
            image = images[i]
            image_content = image.read()

            try:
                cur = mysql.connection.cursor()

                cur.execute("""
                    DELETE FROM images WHERE image_content = (%s) AND email = (%s);
                """, (image_content, email))               

                mysql.connection.commit()
                cur.close()

            except Exception as db_error:
                traceback.print_exc()
                return jsonify({'error': 'Failed to delete from database'}), 500

        return jsonify({'message': 'Images deleted successfully'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
