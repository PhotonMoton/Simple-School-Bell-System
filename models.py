import os

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


