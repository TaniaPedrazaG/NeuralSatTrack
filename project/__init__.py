import ttkbootstrap as ttk
from PIL import Image, ImageTk
import interface

root = ttk.Window(themename="darkly")
ico = Image.open('./assets/sat-orbit.png')
photo = ImageTk.PhotoImage(ico)
root.wm_iconphoto(False, photo)
app = interface.AppInterface(root)
root.mainloop()
