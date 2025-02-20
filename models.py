import os
import json
import time
from pydub import AudioSegment
from datetime import datetime

# Create a default schedule
def create_schedule():
  schedule = [
    {"time":"08:25 AM", "type":"day"},
    {"time":"08:30 AM", "type":"day"},
    {"time":"09:10 AM", "type":"day"},
    {"time":"09:15 AM", "type":"day"},
    {"time":"09:55 AM", "type":"day"},
    {"time":"10:00 AM", "type":"day"},
    {"time":"10:40 AM", "type":"day"},
    {"time":"10:45 AM", "type":"day"},
    {"time":"11:25 AM", "type":"day"},
    {"time":"12:05 PM", "type":"day"},
    {"time":"12:10 PM", "type":"day"},
    {"time":"12:50 PM", "type":"day"},
    {"time":"12:55 PM", "type":"day"},
    {"time":"01:35 PM", "type":"day"},
    {"time":"01:40 PM", "type":"day"},
    {"time":"02:20 PM", "type":"day"},
    {"time":"02:25 PM", "type":"day"},
    {"time":"03:05 PM", "type":"end"} 
  ]
  return schedule

def load_schedule_names():
    if not os.path.exists("sched_names.json"):
        print("creating file")
        with open("sched_names.json", 'w') as file:
            schedule_names = {
                "schedule_1": "schedule_1",
                "schedule_2": "schedule_2",
                "schedule_3": "schedule_3",
                }
            json.dump(schedule_names, file)
    with open("sched_names.json", 'r') as file:
       return json.load(file)

def change_schedule_name(schedule, new_name):
    if not os.path.exists("sched_names.json"):
        load_schedule_names()
    with open("sched_names.json", 'r') as file:
        schedules = json.load(file)
        schedules[schedule] = new_name
    with open("sched_names.json", 'w') as file:
        json.dump(schedules, file)

def update_schedule(schedule, new_schedule):
    with open(schedule, 'w') as file:
        json.dump(new_schedule, file)

def load_schedules():
    schedules = {}
    files = os.listdir()
    for file in files:
        filename = file
        if file.startswith('schedule_') and file.endswith(".json") and int(file.split('_')[1].split('.')[0])>3:
            try:
                filename = filename.split('.')[0]
                schedules[filename]=get_schedule(f"{filename}")
            except Exception as e:
                print(f"Error adding {filename}: {e}")
    return schedules

def get_schedule(schedule):
    # Check if the schedule file exists
    if not os.path.exists(schedule):
        print(f"{file} doesn't exist creating new schedule")
    # If not, create a new schedule and save it
        reset_schedule(schedule)
    with open(schedule, 'r') as file:
       print(f"{file} exists. Loading schedule.")
       return json.load(file)

def reset_schedule(schedule):
    with open(schedule, 'w') as file:
        json.dump(create_schedule(), file)

def delete_schedule(schedule):
    try:
        if os.path.isfile(schedule):
            os.unlink(schedule)
    except Exception as e:
        print(f"Error deleting {schedule}: {e}")

def delete_files_in_folder(folder_path):
  # Get a list of all files in the folder
  files = os.listdir(folder_path)

  # Delete each file in the folder
  for file in files:
      file_path = os.path.join(folder_path, file)
      try:
          if os.path.isfile(file_path):
              os.unlink(file_path)
      except Exception as e:
          print(f"Error deleting {file_path}: {e}")


# Edit a audio file to cut out a segment designated by a start and end time
def cut_audio(file_path, start_time, end_time):
    audio = AudioSegment.from_file(file_path)
    new_audio = audio[start_time * 1000:end_time * 1000]
    new_audio.export(file_path, format="mp3")


# Convert HH:MM:SS time format into seconds
def time_to_seconds(time_str):
    if time_str == "":
        return 0

    try:
        # Parse the input time string into a datetime object
        time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
        
        # Calculate the total seconds from the time object
        seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
        
        return seconds
    
    except ValueError:
        # Handle the case where the input time format is invalid
        return "error"
