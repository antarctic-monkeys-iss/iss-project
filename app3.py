from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, UniqueConstraint
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.dialects.postgresql import BYTEA
from werkzeug.utils import secure_filename
from datetime import datetime
import jwt
import bcrypt
import traceback
import io
import base64

app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = "cockroachdb://antarctic:HBVCEcPaB0kquTdTlW8lTw@issproject-9037.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/project?sslmode=disable"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

# Define models
class User(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, server_default=db.text("unique_rowid()"))
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(BYTEA, nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

    __tablename__ = 'users'

class Image(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, server_default=db.text("unique_rowid()"))
    image_content = db.Column(BYTEA, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    time_of_upload = db.Column(db.TIMESTAMP, nullable=True, server_default=db.func.current_timestamp())
    image_name = db.Column(db.String(255), nullable=True)

    __tablename__ = "images"

class Song(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, server_default=db.text("unique_rowid()"))
    song_name = db.Column(db.String(255), nullable=False)
    song_content = db.Column(BYTEA, nullable=False)
    email = db.Column(db.String(255), nullable=False)

    __tablename__ = "songs"

class Preloaded(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(255), nullable=False)
    song_content = db.Column(db.LargeBinary, nullable=False)

    __tablename__ = "preloaded_songs"

# Landing page
@app.route('/')
def landing():
    if 'token' in request.cookies:
        token = request.cookies['token']
        try:
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            email = decoded_token['email']
            return redirect(url_for('index'))
        except jwt.ExpiredSignatureError:
            return redirect(url_for('login'))
        except jwt.InvalidTokenError:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

# Signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            new_user = User(username=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('index'))
        except IntegrityError:
            db.session.rollback()
            return render_template('signup.html', error='Email already exists')
    return render_template('signup.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == 'admin@admin.com' and password == 'admin':
            return redirect(url_for('admin'))
        try:
            user = User.query.filter_by(email=email).one()
            if bcrypt.checkpw(password.encode('utf-8'), user.password):
                token = jwt.encode({'email': email}, app.config['SECRET_KEY'], algorithm='HS256')
                response = make_response(redirect(url_for('index')))
                response.set_cookie('token', token)
                return response
            else:
                return render_template('login.html', error='Invalid email or password')
        except NoResultFound:
            return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')

# Index page
@app.route('/index')
def index():
    try:
        token = request.cookies.get('token')
        if token:
            decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            email = decoded_token['email']
            
            # Query image and song data for the user
            image_data = Image.query.filter_by(email=email).all()
            song_data = Song.query.filter_by(email=email).all()
            preloaded = Preloaded.query.all()
            if not preloaded:
                create_preloaded()
                preloaded = Preloaded.query.all()
            song_contents = [row.song_content for row in song_data]
            
            preloaded_names = [row.song_name for row in preloaded]
            preloaded_contents = [row.song_content for row in preloaded]
        
            # Prepare song data
            song_names = [row.song_name for row in song_data]
            song_contents = [row.song_content for row in song_data]
            zipped_song_data = zip(song_names, song_contents)
            zipped_preloaded_data = zip(preloaded_names, preloaded_contents)
            if not preloaded_names:
                zipped_preloaded_data = None
            if image_data:
                # Prepare image data
                images = [base64.b64encode(row.image_content).decode('utf-8') for row in image_data]
                zipped_image_data = zip(images, [f'Image {i+1}' for i in range(len(image_data))])
                return render_template('index.html', email=email, zipped_image_data=zipped_image_data, zipped_song_data=zipped_song_data, zipped_preloaded_data=zipped_preloaded_data)
            else:
                return render_template('index.html', email=email, zipped_song_data=zipped_song_data, image_error='No images found', zipped_preloaded_data=zipped_preloaded_data)
        else:
            return redirect(url_for('login'))
    except jwt.ExpiredSignatureError:
        return redirect(url_for('login'))
    except jwt.InvalidTokenError:
        return redirect(url_for('login'))
    except Exception as e:
        traceback.print_exc()
        print(e)
        return render_template('index.html', error='Internal Server Error')

# Sign out
@app.route('/signout')
def signout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('token', '', expires=0)
    return response

# Function to get the next serial number (id)
def get_next_serial_number():
    try:
        highest_available_number = db.session.query(func.max(Image.id)).scalar() or 0
        return highest_available_number + 1
    except Exception as e:
        traceback.print_exc()
        return None

def get_next_song_serial_number():
    try:
        highest_available_number = db.session.query(func.max(Song.id)).scalar() or 0
        return highest_available_number + 1
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
                new_image = Image(id=serial_number, image_name =names[i], image_content=image_content, email=email)
                db.session.add(new_image)
                db.session.commit()
            except Exception as db_error:
                traceback.print_exc()
                db.session.rollback()
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
        images = Image.query.filter_by(email=email).all()
        return render_template('uploaded_images.html', images=images)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error'}), 500

# New route to get image content
@app.route('/get-image/<int:image_id>')
def get_image(image_id):
    try:
        image_data = Image.query.filter_by(id=image_id).one()
        if image_data:
            image_content = io.BytesIO(image_data.image_content)
            return send_file(image_content, mimetype='image/jpeg')
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
        song_number = get_next_song_serial_number()
        try:
            if Song.query.filter_by(song_content=song_content, email=email):
                Song.query.filter_by(song_content=song_content, email=email).delete()
            new_song = Song(id=song_number, song_name=song_name, song_content=song_content, email=email)
            db.session.add(new_song)
            db.session.commit()
            return jsonify({'status': 'success', 'message': f'Successfully uploaded {song_name}'})
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'Error uploading song: {str(e)}'}), 500
    except Exception as e:
        traceback.print_exc()
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
        try:
            Song.query.filter_by(song_content=song_content, email=email).delete()
            db.session.commit()
            return jsonify({'status': 'success', 'message': f'Successfully removed {song_name}'})
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'Error removing song: {str(e)}'}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'Error decoding token: {str(e)}'}), 401

@app.route('/admin')
def admin():
    users = User.query.all()
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
        for image in images:
            try:
                Image.query.filter_by(image_content=image.read(), email=email).delete()
                db.session.commit()
            except Exception as db_error:
                traceback.print_exc()
                db.session.rollback()
                return jsonify({'error': 'Failed to delete from database'}), 500
        return jsonify({'message': 'Images deleted successfully'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal Server Error'}), 500

def create_preloaded():
    songs = Song.query.filter_by(email='preloaded@preloaded.com').all()
    i = 1
    for row in songs:
        new_song = Preloaded(id = i, song_name=row.song_name, song_content=row.song_content)
        db.session.add(new_song)
        db.session.commit()
        i = i + 1

@app.route('/remove-song-from-database', methods=['POST'])
def remove_song_from_database():
    token = request.cookies.get('token')
    if token:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        email = decoded_token['email']
    try:
        song_name = request.form.get('song_name')
        print(song_name)
        song_content = request.form.get('song_content')
        try:
            Song.query.filter_by(song_name=song_name, email=email).delete()
            db.session.commit()
            return jsonify({'status': 'success', 'message': f'Successfully removed {song_name}'})
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'Error removing song: {str(e)}'}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'Error decoding token: {str(e)}'}), 401

@app.route('/add-song-to-database-from-library', methods=['POST'])
def add_song_to_library_from_database():
    token = request.cookies.get('token')
    if token:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        email = decoded_token['email']
    
        song_name = request.form.get('song_name')
        print(song_name)
        song = Song.query.filter_by(song_name=song_name, email='preloaded@preloaded.com').one()
        song_content = song.song_content
        song_number = get_next_song_serial_number()
        try:
            db.session.query(Song).filter(Song.song_name == song_name, Song.email == email).delete()
            new_song = Song(id=song_number, song_name=song_name, song_content=song_content, email=email)
            db.session.add(new_song)
            db.session.commit()
            return jsonify({'status': 'success', 'message': f'Successfully added {song_name}'})
        except Exception as e:
            traceback.print_exc()
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'Error adding song: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)