import os
import threading
import tkinter as tk

from path import to_abs_path


"""parameters of the size of screen"""
window = tk.Tk()
window_width = 350
window_height = 350
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
# notation of size (str): (width)x(height)+x+y
size: str = f'{int(window_width)}x{int(window_height)}+{int((screen_width-window_width)/2)}+{int((screen_height-window_height)/2)}'
window.geometry(size) # size and position
window.title("Webcam Application") # title
window.iconbitmap(to_abs_path("img/webcam.ico")) # icon

start_img = tk.PhotoImage(file=to_abs_path("img/start.jpg")).subsample(2, 2) # image of start button
wait_img =  tk.PhotoImage(file=to_abs_path("img/wait.jpg")).subsample(2, 2)


def alpha(dist_measure: tk.BooleanVar, focus_time: tk.BooleanVar, post_watch: tk.BooleanVar) -> None:
    """Same as the command required in alpha.py.

    Arguments:
        dist_measure/focus_time/post_watch (tk.BooleanVar):
            Three features provided to users.
            Calling (tk.BooleanVar).get() can get the boolean value of the variable.
    """
    command: str = "python " + to_abs_path("alpha.py")
    if dist_measure.get():
        command += " -d"
    if focus_time.get():
        command += " -t"
    if post_watch.get():
        command += " -p"
    os.system(command)


def thread_it(func, *args) -> None:
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    t.start()


def main() -> None:
    """
    Arguments:
        dist_measure/focus_time/post_watch (tk.BooleanVar):
            Three features provided to users.
            BooleanVar() is a type in tkinter, used in declaration of buttons.
    """
    dist_measure: tk.BooleanVar = tk.BooleanVar()
    focus_time:   tk.BooleanVar = tk.BooleanVar()
    post_watch:   tk.BooleanVar = tk.BooleanVar()
    # provide check buttons for users to check the features they want
    tk.Checkbutton(window, text="Distance Measure", variable=dist_measure,
                   onvalue=True, offvalue=False, height=5, width=20).pack()
    tk.Checkbutton(window, text="Timer", variable=focus_time,
                   onvalue=True, offvalue=False, height=5, width=20).pack()
    tk.Checkbutton(window, text="Posture Detection", variable=post_watch,
                   onvalue=True, offvalue=False, height=5, width=20).pack()
    # start button
    tk.Button(window, text="Start Capturing", image=start_img,
              command=lambda: thread_it(alpha, dist_measure, focus_time, post_watch)
             ).pack()
    # start the program
    window.mainloop()


if __name__ == '__main__':
    main()
