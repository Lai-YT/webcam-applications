import alpha
import os
import tkinter as tk
import threading

from tkinter import *
from PIL import ImageTk, Image

"""window initialization"""
# size of the window and the screen
window = tk.Tk()
window_width = 350
window_height = 350
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
# notation of size (str): (width)x(height)+x+y
size: str = f'{int(window_width)}x{int(window_height)}+{int((screen_width-window_width)/2)}+{int((screen_height-window_height)/2)}'
window.geometry(size) # size and position
# background = tk.Label(window, background = "pink", compound = 'bottom',
#                       width = window_width, height = window_height).pack() # background
window.title("Webcam Application") # title
window.iconbitmap("webcam.ico") # icon

# image of start button, half as small as original image
start_img = PhotoImage(file="start.jpg").subsample(2, 2)


def alpha(dist_measure: tk.BooleanVar, focus_time: tk.BooleanVar, post_watch: tk.BooleanVar) -> None:
    '''
    Same as the command required in alpha.py.
    
    Arguments:
        dist_measure/focus_time/post_watch (tk.BooleanVar):
            Three features provided to users.
            Calling (tk.BooleanVar).get() can get the boolean value of the variable.
    '''
    command: str = "python alpha.py"
    if(dist_measure.get() == True):
        command += " -d"
    if(focus_time.get() == True):
        command += " -t"
    if(post_watch.get() == True):
        command += " -p"
    os.system(command)

def thread_it(func, *args):
    t = threading.Thread(target = func, args = args)
    t.setDaemon(True)
    t.start()

def main() -> None:
    '''
    Arguments:
        dist_measure/focus_time/post_watch (tk.BooleanVar):
            Three features provided to users.
            BooleanVar() is a type in tkinter, used in declaration of buttons.
    '''
    dist_measure: tk.BooleanVar = tk.BooleanVar()
    focus_time:   tk.BooleanVar = tk.BooleanVar() 
    post_watch:   tk.BooleanVar = tk.BooleanVar()
    # provide check buttons for users to check the features they want
    tk.Checkbutton(window, text = "Distance Measure", variable = dist_measure,
                   onvalue = True, offvalue = False, height = 5, width = 20).pack()
    tk.Checkbutton(window, text = "Timer", variable = focus_time,
                   onvalue = True, offvalue = False, height = 5, width = 20).pack()
    tk.Checkbutton(window, text = "Posture Detection", variable = post_watch,
                   onvalue = True, offvalue = False, height = 5, width = 20).pack()  
    # start button
    tk.Button(window, text="Start Capturing", image = start_img,
              command = (lambda: thread_it(alpha, dist_measure, focus_time, post_watch))).pack()
    # start the program
    window.mainloop()

if __name__ == '__main__':
    main()