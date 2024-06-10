import ttkbootstrap as ttk
from PIL import Image, ImageTk
import downloadTle
import interface

root = ttk.Window(themename="cosmo")
ico = Image.open('./assets/sat-orbit.png')
photo = ImageTk.PhotoImage(ico)
root.wm_iconphoto(False, photo)
interface.Interface(root)

def open_confirmation():
    main_width = root.winfo_width()
    main_height = root.winfo_height()
    x = root.winfo_rootx() + main_width // 3
    y = root.winfo_rooty() + main_height // 3

    root_2 = ttk.Toplevel()
    root_2.geometry(f"+{x}+{y}")
    root_2.grab_set()
    downloadTle.DownloadTLE(root_2)

root.after(1000, open_confirmation)
root.mainloop()