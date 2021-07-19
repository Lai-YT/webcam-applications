import os.path
import shutil

# Config settings
path1 = "train/action_01"
path2 = "train/action_02"

def reset_training_folder():
    '''
    Delete the captured images in the "train" folder.
    If the directory is already empty, put a text to the user.
    '''
    if not os.path.isdir(path1) and not os.path.isdir(path2):
        print("Directory is already empty.")
    else:
        if os.path.isdir(path1):
            shutil.rmtree(path1, ignore_errors=True)
        if os.path.isdir(path2):
            shutil.rmtree(path2, ignore_errors=True)
