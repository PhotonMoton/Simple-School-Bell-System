import os
from pydub import AudioSegment

def createSchedule():
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
    {"time":"03:05 PM", "type":"end"}, 
  ]
  return schedule

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



def cut_audio(input_path, output_path, start_time, end_time):
    audio = AudioSegment.from_file(input_path)
    new_audio = audio[start_time * 1000:end_time * 1000]
    new_audio.export(output_path, format="mp3")


