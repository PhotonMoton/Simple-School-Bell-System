# Import necessary modules and packages
import subprocess
from flask import Flask, render_template, request, redirect, url_for
from models import delete_files_in_folder, createSchedule, cut_audio, time_to_seconds
from datetime import datetime
import multiprocessing
import pytz
import time
import os

# Flask application setup
app = Flask(__name__, static_url_path='/static')
daySong = 'test'  # Default value for day song
endSong = 'test'  # Default value for end song
audio_process = None  # Process for audio player
stop_audio_event = multiprocessing.Event()  # Event to signal audio player to stop

# Route to display the index page
@app.route('/')
def index():
    global daySong
    global endSong
    global audio_process

    # Retrieve the path to the 'day' folder within the app
    day_folder_path = os.path.join(app.root_path, 'static', 'day')

    # Get a list of files in the 'day' folder
    files_in_folder = os.listdir(day_folder_path)

    if files_in_folder:
        # Iterate through the files and set 'daySong' to the last file in the folder
        for file in files_in_folder:
            daySong = os.path.basename(file)

    # Retrieve the path to the 'end' folder within the app
    end_folder_path = os.path.join(app.root_path, 'static', 'end')

    # Get a list of files in the 'end' folder
    files_in_folder = os.listdir(end_folder_path)

    if files_in_folder:
        # Iterate through the files and set 'endSong' to the last file in the folder
        for file in files_in_folder:
            endSong = os.path.basename(file)

        if audio_process is None or not audio_process.is_alive():
            # Clear the stop event to allow the audio player to run
            stop_audio_event.clear()

            # Start a new process for the audio player
            audio_process = multiprocessing.Process(target=start_audio_player, args=(stop_audio_event,))
            audio_process.start()
    # Render the index.html template with the last files saved as the current song
    return render_template('index.html', daySong=daySong, endSong=endSong, audio_on=audio_process.is_alive())


# Route to handle file uploads
@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    global daySong
    global endSong
    global stop_audio_event
    global audio_process
    songSubFolder = 'day'  # Default subfolder for songs
    start_time_seconds = 0

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        # Retrieve data from the form
        file = request.files['file']
        songSubFolder = request.form.get('selectedOption')
        start_time_seconds = time_to_seconds(request.form.get('start_time'))
        if start_time_seconds == "error":
            return render_template('index.html', daySong=daySong, endSong=endSong, audio_on=audio_process.is_alive(), error=True)

        end_time_seconds = start_time_seconds+45

        if file.filename == '':
            return redirect(request.url)

        if file:
            # Delete all files in the song folder before uploading a new file
            static_folder_path = os.path.join(app.root_path, 'static',  songSubFolder)
            delete_files_in_folder(static_folder_path)

            # Save the new file to the song folder
            filename = os.path.join(static_folder_path, file.filename)
            file.save(filename)


            # Set 'daySong' or 'endSong' to the basename of the uploaded file based on the subfolder
            if songSubFolder == 'day':
                # Set the start and stop times for the song
                cut_audio(filename, start_time_seconds, end_time_seconds)
                daySong = os.path.basename(filename)
            if songSubFolder == 'end':
                endSong = os.path.basename(filename)

            # Redirect to the index page with the new song
            return render_template('index.html', daySong=daySong, endSong=endSong, audio_on=audio_process.is_alive())

    # Redirect to the index page if the request method is not POST
    return redirect(url_for('index'))

# Function to start the audio player in a separate process
def start_audio_player(stop_event):
    global daySong
    global endSong

    # Construct the audio path
    base_directory = os.path.abspath(os.path.dirname(__file__))
    songSubFolder = 'day'  # Default subfolder for songs
    audio_url = os.path.abspath(os.path.join(base_directory, 'static', songSubFolder, daySong))

    # Pull the schedule from model.py
    schedule = createSchedule()

    while not stop_event.is_set():
        # Get the current time in the Eastern Time zone
        eastern_timezone = pytz.timezone('US/Eastern')
        current_time = datetime.now(eastern_timezone).strftime("%I:%M %p")

        for item in schedule:
            if item['time'] == current_time:
                if item['type'] == 'day':
                    songSubFolder = 'day'
                    audio_url = os.path.abspath(os.path.join(base_directory, 'static', songSubFolder, daySong))
                    # Play the audio file using mpg123
                    os.system("mpg123 " + audio_url)

                    # Wait for 60 seconds before checking the schedule again
                    time.sleep(60)
                if item['type'] == 'end':
                    songSubFolder = 'end'
                    audio_url = os.path.abspath(os.path.join(base_directory, 'static', songSubFolder, endSong))
                    # Play the audio file using mpg123
                    os.system("mpg123 " + audio_url)

                    # Wait for 300 seconds before checking the schedule again
                    time.sleep(300)

        # Wait for 5 seconds before checking the schedule again
        time.sleep(5)

# Route to start the audio player
@app.route('/start', methods=['POST', 'GET'])
def start():
    global audio_process
    global stop_audio_event

    if audio_process is None or not audio_process.is_alive():
        # Clear the stop event to allow the audio player to run
        stop_audio_event.clear()

        # Start a new process for the audio player
        audio_process = multiprocessing.Process(target=start_audio_player, args=(stop_audio_event,))
        audio_process.start()

        # Redirect to the index page with the current song
        return render_template('index.html', daySong=daySong, endSong=endSong, audio_on=audio_process.is_alive())
    else:
        # Redirect to the index page with the current song if the audio player is already running
        return render_template('index.html', daySong=daySong, endSong=endSong, audio_on=audio_process.is_alive())

# Route to stop the audio player
@app.route('/stop', methods=['POST', 'GET'])
def stop():
    global audio_process
    global stop_audio_event

    if audio_process and audio_process.is_alive():
        # Set the stop event to signal the audio player to stop
        stop_audio_event.set()

        # Wait for the audio player process to stop
        audio_process.join()

    # Redirect to the index page with the current song
    return render_template('index.html', daySong=daySong, endSong=endSong, audio_on=audio_process.is_alive())

# Route for the test play button
@app.route('/test', methods=['POST', 'GET'])
def test():

    # Construct the audio path
    base_directory = os.path.abspath(os.path.dirname(__file__))
    audio_url = os.path.abspath(os.path.join(base_directory, 'static', 'day', daySong))

    # Run audio and wait 60 seconds
    os.system("mpg123 " + audio_url)
    time.sleep(60)

    # Redirect to the index page with the current song
    return render_template('index.html', daySong=daySong, endSong=endSong, audio_on=audio_process.is_alive())


# Run the Flask application
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
