import subprocess  # For executing shell commands
from flask import Flask, render_template, request, redirect, url_for  # Flask web framework imports
from models import delete_files_in_folder, create_schedule, cut_audio, time_to_seconds, get_schedule, update_schedule, reset_schedule 
from datetime import datetime  # For handling date and time operations
import multiprocessing  # For parallel execution
import pytz  # For timezone conversions
import time  # For sleep/delay operations
import os  # For file system operations
import re # For sanitizing filenames

# Initialize Flask app with a specific static_url_path
app = Flask(__name__, static_url_path='/static')

# Initialize variables for managing audio processes and app state
audio_process = None  # Placeholder for the audio playing process
stop_audio_event = multiprocessing.Event()  # Event signal to stop audio playback
app_state = {"daySong": 'test', "endSong": None, "app_state": 'test', "audio_state": False, "error": False, "volume": 75, "schedule":"1", "schedule_1": create_schedule(),"schedule_2":create_schedule(), "schedule_3":create_schedule()}  # App state dictionary

def sanitize_filename(filename):
    """
    Sanitizes the filename by removing spaces and punctuation from the base name,
    preserving the file extension, and handling extra dots correctly.
    """
    base_name, extension = os.path.splitext(filename)
    
    # Replace spaces with underscores in the base name
    sanitized_base = base_name.replace(" ", "_")
    
    # Remove punctuation except for dots and underscores in the base name
    sanitized_base = re.sub(r'[^\w-]', '', sanitized_base)
    
    # Combine the sanitized base name with the original extension
    sanitized_filename = sanitized_base + extension
    
    return sanitized_filename

# Function to get a list of files in a given folder
def get_files_in_folder(folder_path):
    #Returns a list of file names in the specified folder path. Returns an empty list if the folder does not exist
    return [os.path.basename(file) for file in os.listdir(folder_path)] if os.path.exists(folder_path) else []

# Function to get the full file path for a file in the static directory
def get_full_file_path(subfolder, filename):
    #Constructs and returns the absolute path for a file located in a subfolder of the app's static directory
    return os.path.abspath(os.path.join(app.root_path, 'static', subfolder, filename))

# Function to update the application state with the current song based on the subfolder and filename
def update_app_state(subfolder, filename):
    #Updates the app_state dictionary with the filename of the current song, based on the subfolder
    app_state[subfolder + "Song"] = filename

# Function to start the audio player in a separate process
def start_audio_player(stop_event):
    #Continuously plays audio based on the current time and a predefined schedule, until the stop_event is set
    while not stop_event.is_set():
        current_time = datetime.now(pytz.timezone('US/Eastern')).strftime("%I:%M %p")
        schedule = app_state["schedule"]

        for item in schedule:
            if item['time'] == current_time:
                subfolder = 'day' if item['type'] == 'day' else 'end'
                filename = app_state[subfolder + "Song"]
                audio_url = get_full_file_path(subfolder, filename)
                subprocess.run(["mpg123", audio_url])

                wait_time = 60 if item['type'] == 'day' else 300
                time.sleep(wait_time)

        time.sleep(5)

def restart_audio_player():
    global audio_process, stop_audio_event, app_state
    # Check if the audio process is currently running
    if audio_process is not None and audio_process.is_alive():
        # If running, signal the current process to stop
        stop_audio_event.set()
        audio_process.join()  # Wait for it to stop
        stop_audio_event.clear()  # Reset the event for next use
        
        # Start a new audio process with the updated state
        audio_process = multiprocessing.Process(target=start_audio_player, args=(stop_audio_event,))
        audio_process.start()
        app_state["audio_state"] = True  # Ensure the audio state is marked as running
    else:
        # If not running, just update the state without starting the process
        # This is useful when the application is in a stopped state
        app_state["audio_state"] = False  # Ensure the audio state is marked as not running

def set_volume(volume):
    #Set the system volume with amixer (ALSA). Volume is a percentage
    subprocess.run(['amixer', 'set', 'Master', f'{volume}%'])


# Flask route for the index page
@app.route('/', methods=['POST', 'GET'])
def index():
    #Handles the index route, initializes the audio process if not already running, and renders the index page with the current app state
    global audio_process, stop_audio_event, app_state

    # Check if the request is redirected from remove_slot
    redirected = request.args.get('redirected', default=False, type=bool)
    if not redirected:
        # Determine paths for day and end song folders
        day_folder_path = os.path.join(app.root_path, 'static', 'day')
        end_folder_path = os.path.join(app.root_path, 'static', 'end')

        # Update app state with the latest song files from each folder
        app_state["daySong"] = get_files_in_folder(day_folder_path)[-1] if os.path.exists(day_folder_path) else None
        app_state["endSong"] = get_files_in_folder(end_folder_path)[-1] if os.path.exists(end_folder_path) else None

        # Update app state with the latest user edited schedule
        app_state["schedule_1"] = get_schedule("schedule_1.json")
        app_state["schedule_2"] = get_schedule("schedule_2.json")
        app_state["schedule_3"] = get_schedule("schedule_3.json")

        # Start audio process if it's not already running
        if audio_process is None:
            stop_audio_event.clear()
            audio_process = multiprocessing.Process(target=start_audio_player, args=(stop_audio_event,))
            audio_process.start()
            app_state["audio_state"] = True
            set_volume(app_state['volume'])

    return render_template('index.html', app_state=app_state)

# Flask route for uploading files
@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    #Handles file uploads, updates app state, and initiates audio processing for uploaded files
    global app_state, stop_audio_event, audio_process

    if request.method == 'POST':
        file = request.files.get('file')
        song_subfolder = request.form.get('selectedOption')
        start_time_seconds = time_to_seconds(request.form.get('start_time'))

        if start_time_seconds == "error":
            app_state["error"] = True
            return redirect(url_for('index', redirected=True))

        app_state["error"] = False
        end_time_seconds = start_time_seconds + 45

        if file:
            # Sanitize the filename
            clean_name = sanitize_filename(file.filename)

            static_folder_path = os.path.join(app.root_path, 'static', song_subfolder)
            delete_files_in_folder(static_folder_path)

            filename = os.path.join(static_folder_path, clean_name)
            file.save(filename)

            if song_subfolder == 'day':
                cut_audio(filename, start_time_seconds, end_time_seconds)

            update_app_state(song_subfolder, os.path.basename(filename))
            restart_audio_player()
            return redirect(url_for('index', redirected=True))

    return redirect(url_for('index', redirected=True))

# Flask route to start audio playback
@app.route('/start', methods=['POST', 'GET'])
def start():
    #Starts the audio playback process if it is not already running and updates the application state
    global audio_process, stop_audio_event, app_state

    # Check if the audio process is not running and start it
    if audio_process is None or not audio_process.is_alive():
        stop_audio_event.clear()  # Reset the stop event
        # Create and start a new process for the audio player
        audio_process = multiprocessing.Process(target=start_audio_player, args=(stop_audio_event,))
        audio_process.start()
        app_state["audio_state"] = True  

    # Render and return the index page with the updated application state
    return redirect(url_for('index', redirected=True))

# Flask route to stop audio playback
@app.route('/stop', methods=['POST', 'GET'])
def stop():
    #Stops the audio playback process if it is running and updates the application state
    global audio_process, stop_audio_event, app_state

    # Check if the audio process is running
    if audio_process and audio_process.is_alive():
        stop_audio_event.set()  # Signal the process to stop
        audio_process.join()  # Wait for the process to finish
        app_state["audio_state"] = False  # Update the app state to indicate audio is not playing

    # Render and return the index page with the updated application state
    return redirect(url_for('index', redirected=True))

# Flask route for testing audio playback
@app.route('/test', methods=['POST', 'GET'])
def test():
    #Tests the audio playback functionality independently of the scheduled playback
    global app_state, audio_process

    was_running= True
    # Start the audio process for testing if it's not already running
    if audio_process is None or not audio_process.is_alive():
        stop_audio_event.clear()  # Ensure any previous stop event is cleared
        audio_process = multiprocessing.Process(target=start_audio_player, args=(stop_audio_event,))
        audio_process.start()
        app_state["audio_state"] = True
        was_running= False  

    # Directly play the day song for testing
    audio_url = get_full_file_path('day', app_state["daySong"])
    subprocess.run(["mpg123", audio_url])
    time.sleep(60)  # Wait for 60 seconds after playing the test audio

    # Stop the audio process after testing
    if was_running == False:
        stop_audio_event.set()  # Signal the process to stop
        audio_process.join()  # Wait for the process to finish
        app_state["audio_state"] = False  # Update the app state to indicate audio is not playing

    # Render and return the index page with the updated application state
    return redirect(url_for('index', redirected=True))

# Flask route for changing the volume
@app.route('/volume', methods=['POST','GET'])
def volume():
    global app_state
    if request.method == 'POST':
        new_volume = int(request.form.get('volume'))
        app_state['volume']=new_volume
        set_volume(new_volume)
    return redirect(url_for('index', redirected=True))

# Flask route for adding a new time slot to the schedule
@app.route('/add-slot', methods=['POST', 'GET'])
def add_slot():
    global app_state
    if request.method == 'POST':
        option = "schedule_"+app_state["schedule"]
        schedule = app_state[option]
        
        # Get the new time from the front end in 24-hour format
        new_time_24hr = request.form.get('time')  # Expected in 24-hour format, e.g., "15:45"

        # Convert the 24-hour format time to 12-hour format as a text string
        new_time_obj = datetime.strptime(new_time_24hr, '%H:%M')
        new_time_12hr = new_time_obj.strftime('%I:%M %p')  # Converted to 12-hour format

        # Create the new entry with the time as a text string
        new_entry = {
            "time": new_time_12hr,  # Time in 12-hour format as text
            "type": request.form.get('type')
        }

        # Convert new_entry time back to datetime for comparison
        new_entry_time = datetime.strptime(new_time_12hr, '%I:%M %p')

        # Find the position where the new entry should be inserted
        position = len(schedule)  # Default to end if no earlier time is found
        for entry in schedule:
            entry_time = datetime.strptime(entry['time'], '%I:%M %p')
            if entry_time > new_entry_time:
                position = schedule.index(entry)
                break

        # Insert the new entry into the schedule
        schedule.insert(position, new_entry)

        # Make necessary updates
        app_state[option] = schedule
        update_schedule(option+".json", schedule)
        restart_audio_player()

    return redirect(url_for('index', redirected=True))

# Flask route for removing a time slot to the schedule
@app.route('/remove-slot', methods=['POST', 'GET'])
def remove_slot():
    global app_state
    if request.method == 'POST':
        option = "schedule_"+app_state["schedule"]
        schedule = app_state[option]
        
        # Get the time slot to delete from the front end and remove it
        to_delete = {"time":request.form.get('time'), "type":request.form.get('type')}
        if to_delete in schedule:
            schedule.remove(to_delete)

        # Make necessary updates
        app_state[option] = schedule
        update_schedule(option+".json", schedule)
        restart_audio_player()
    return redirect(url_for('index', redirected=True))

# Flask route for changing the current loaded schedule
@app.route('/load-schedule', methods = ['POST', 'GET'])
def load_schedule():
    global app_state
    if request.method == "POST":
        app_state["schedule"] = request.form.get('option')
    restart_audio_player()
    return redirect(url_for('index', redirected=True))

# Main block to run the Flask application on a specified host and port
if __name__ == "__main__":
    app.run(host='10.0.1.179', port=8080)
