import mysql.connector  # Assuming you're using MySQL
import cv2
import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
import io
from PIL import Image
import math


def cross_dissolve(prev_frame, next_frame, transition_duration):
    transition_frames = []
    for i in range(transition_duration):
        alpha = i / transition_duration
        blended_frame = cv2.addWeighted(prev_frame, 1 - alpha, next_frame, alpha, 0)
        transition_frames.append(blended_frame)
    return transition_frames

def fade_in_out(prev_frame, next_frame, transition_duration):
    transition_frames = []
    for i in range(transition_duration):
        alpha = i / transition_duration
        fade_in_frame = cv2.addWeighted(prev_frame, 1 - alpha, next_frame, alpha, 0)
        fade_out_frame = cv2.addWeighted(next_frame, 1 - alpha, prev_frame, alpha, 0)
        transition_frames.append(fade_in_frame)
        transition_frames.append(fade_out_frame)
    return transition_frames

# Implement other transition effects here...

def create_video_with_transitions(img_paths, delay_between_frames, transition_type, include_audio, audio_path):
    # Find the dimensions of the largest image
    max_height = 0
    max_width = 0
    for img in img_paths:
        image = Image.open(io.BytesIO(img[0]))
        image.save(img[1])
        frame = cv2.imread(img[1])
        os.remove(img[1])
        height, width, _ = frame.shape
        max_height = max(max_height, height)
        max_width = max(max_width, width)

    cv2_fourcc = cv2.VideoWriter_fourcc(*'DIVX')  # Change fourcc codec to DIVX

    video = cv2.VideoWriter("video.avi", cv2_fourcc, 30, (max_width, max_height))  # Initialize video writer

    if video is None:
        print("Error: Failed to initialize video writer.")
        exit()

    transition_duration = 15  # Set duration of transition between frames (in frames)
    for i, img in enumerate(img_paths):
        image = Image.open(io.BytesIO(img[0]))
        image.save(img[1])
        frame = cv2.imread(img[1])
        os.remove(img[1])
        height, width, _ = frame.shape
        resized_frame = cv2.resize(frame, (max_width, max_height))  # Resize image to match max dimensions

        # Write frames with transition between images
        if i > 0:
            if transition_type == 'cross_dissolve':
                transition_frames = cross_dissolve(prev_frame, resized_frame, transition_duration)
            elif transition_type == 'fade_in_out':
                transition_frames = fade_in_out(prev_frame, resized_frame, transition_duration)
            # Add more transitions here...

            for transition_frame in transition_frames:
                video.write(transition_frame)

        # Write the last frame without transition
        video.write(resized_frame)

        # Add delay between frames
        for _ in range(delay_between_frames * 30):
            video.write(resized_frame)

        prev_frame = resized_frame

    video.release()

    if include_audio:
        video_clip = VideoFileClip("video.avi")
        audio_clip = AudioFileClip("song.mp3")
        if audio_clip.duration < video_clip.duration:
            num_repeats = math.ceil(video_clip.duration / audio_clip.duration)

            # Concatenate the audio clips to match the video duration
            concatenated_audio_clip = concatenate_audioclips([audio_clip] * num_repeats)

            # Specify the file path to save the modified audio file
            modified_audio_file_path = "modified_song.mp3"

            # Write the modified audio data to the file
            concatenated_audio_clip.write_audiofile(modified_audio_file_path)
            audio_clip_new = AudioFileClip("modified_song.mp3")
            video_clip = video_clip.set_audio(audio_clip_new)
        else:
            audio_clip = audio_clip.set_duration(video_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)
        video_clip.write_videofile("video.avi".replace('.avi', '_with_audio.avi'), codec='libx264', audio_codec='aac')

def create_video_without_transitions(rows, delay_between_frames, audio_path=None):
    # Find the dimensions of the largest image
    max_height = 0
    max_width = 0

    for img in rows:
        # Convert image content to PIL Image
        image = Image.open(io.BytesIO(img[0]))
        image.save(img[1])

        # Read the temporary image file with OpenCV
        frame = cv2.imread(img[1])
        os.remove(img[1])  # Remove the temporary image file

        # Update max_height and max_width
        height, width, _ = frame.shape
        max_height = max(max_height, height)
        max_width = max(max_width, width)

    # Initialize video writer
    cv2_fourcc = cv2.VideoWriter_fourcc(*'DIVX')  # Change fourcc codec to DIVX
    video = cv2.VideoWriter("video.avi", cv2_fourcc, 30, (max_width, max_height))

    if video is None:
        print("Error: Failed to initialize video writer.")
        exit()

    for img in rows:
        # Convert image content to PIL Image
        image = Image.open(io.BytesIO(img[0]))
        image.save(img[1])

        # Read the temporary image file with OpenCV and resize it
        frame = cv2.imread(img[1])
        os.remove(img[1])  # Remove the temporary image file

        resized_frame = cv2.resize(frame, (max_width, max_height))

        # Write the resized frame to the video
        video.write(resized_frame)

        # Add delay between frames
        for _ in range(delay_between_frames * 30):
            video.write(resized_frame)

    video.release()

    if audio_path:
        video_clip = VideoFileClip("video.avi")
        audio_clip = AudioFileClip("song.mp3")
        if audio_clip.duration < video_clip.duration:
            num_repeats = math.ceil(video_clip.duration / audio_clip.duration)

            # Concatenate the audio clips to match the video duration
            concatenated_audio_clip = concatenate_audioclips([audio_clip] * num_repeats)

            # Specify the file path to save the modified audio file
            modified_audio_file_path = "modified_song.mp3"

            # Write the modified audio data to the file
            concatenated_audio_clip.write_audiofile(modified_audio_file_path)
            audio_clip_new = AudioFileClip("modified_song.mp3")
            video_clip = video_clip.set_audio(audio_clip_new)
        else:
            audio_clip = audio_clip.set_duration(video_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)
        video_clip.write_videofile("video.avi".replace('.avi', '_with_audio.avi'), codec='libx264', audio_codec='aac')

def main():
    transition_input = input("Do you want to add transitions between frames? (yes/no): ")
    if transition_input.lower() == "yes":
        transition_type = input("Enter the transition type (cross_dissolve, fade_in_out, etc.): ")
    else:
        transition_type = None

    audio_input = input("Do you want to include audio? (yes/no): ")
    if audio_input.lower() == "yes":
        include_audio = True
        audio_path = retrieve_audio_from_database()
    else:
        include_audio = False
        audio_path = None

    delay_input = input("Enter the delay between images (in seconds): ")
    delay_between_frames = int(delay_input) if delay_input.isdigit() else 0
    
    rows = retrieve_images_from_database()
    
    if transition_type:
        create_video_with_transitions(rows, delay_between_frames, transition_type, include_audio, audio_path)
    else:
        create_video_without_transitions(rows, delay_between_frames, audio_path)

def connect_to_database():
    # Connect to your database (replace the placeholders with your actual database connection details)
    return mysql.connector.connect(
        host="localhost",
        user="Disha",
        password="#Vilifiedjaguar56",
        database="project"
    )

def retrieve_images_from_database():
    # Connect to the database
    db_connection = connect_to_database()
    cursor = db_connection.cursor()

    # Query to retrieve image blobs and names from the database
    query = "SELECT image_content, image_name FROM images"
    cursor.execute(query)

    # Fetch all rows
    rows = cursor.fetchall()

    # Close cursor and database connection
    cursor.close()
    db_connection.close()

    # Return the image blobs and names as a list of tuples (image_content, image_name)
    return rows

def retrieve_audio_from_database():
    # Connect to the database
    db_connection = connect_to_database()
    cursor = db_connection.cursor()

    # Query to retrieve audio blobs from the database
    query = "SELECT song_content FROM songs"
    cursor.execute(query)

    # Fetch all rows
    songs = cursor.fetchall()

    # Close cursor and database connection
    cursor.close()
    db_connection.close()

    if not songs:
        return None

    # Initialize an empty bytes object to hold concatenated audio
    concatenated_audio = b''

    for audio_blob in songs:
        concatenated_audio += audio_blob[0]

    # Specify the file path to save the audio file
    output_file_path = "song.mp3"

    # Write the concatenated audio data to the file
    with open(output_file_path, 'wb') as audio_file:
        audio_file.write(concatenated_audio)

    return output_file_path

if __name__ == "__main__":
    main()
