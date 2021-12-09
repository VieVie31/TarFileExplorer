"""
This is a little tar files explorer in python with tkinter.

It allows :
    - to preview images contained in a tar file 
    - extract files or subdirectory of the given tar file

Due to the image preview feature, it requires the PIL dependency.

@author: VieVie31

```bash
>>> python tfe.py file.tar
```
"""
import os
import sys
import tarfile
import tempfile
import tkinter as tk
import platform
import subprocess

from tkinter import messagebox
from collections import defaultdict

from PIL import Image, ImageTk 


DELIMITER = os.path.sep

def system_viewer(filepath: str):
    """
    Try to open `filepath` with the default system viewer.
    """
    if platform.system() == 'Darwin':
        # Mac OS X
        subprocess.call(('open', filepath))
    elif platform.system() == 'Windows':
        # Windows
        os.startfile(filepath)
    else:
        # linux variants
        subprocess.call(('xdg-open', filepath))
    

class TarFileExplorer:
    def __init__(self, tar_filename: str):
        self.tar_root = tarfile.open(tar_filename)

        tar_files_pathes = [p for p in self.tar_root.getnames()]
        tar_parents = [DELIMITER.join(p.split(DELIMITER)[:-1]) for p in tar_files_pathes]
        tar_files_pathes, tar_parents = zip(*sorted(zip(tar_files_pathes, tar_parents)))

        self.tree_dict = defaultdict(lambda: [])
        for parent, path_file in zip(tar_parents, tar_files_pathes):
            self.tree_dict[parent].append(path_file)


        self.tmpdir = tempfile.TemporaryDirectory()

        self.current_path = ''
        self.opened_at_least_one_tmp = False



        self.window = tk.Tk()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.title(f"TarFile Explorer - {tar_filename}")

        self.listbox = tk.Listbox(self.window, width=25)
        tk.Grid.rowconfigure(self.window, 0, weight=1)
        self.listbox.grid(row=0, column=0, sticky="nsew")


        self.listbox.bind('<Double-Button>', self.dbl_click_listbox)
        self.listbox.bind('<Return>', self.dbl_click_listbox)
        self.listbox.bind('<<ListboxSelect>>', self.click_listbox)


        self.cv = tk.Canvas(self.window)
        self.cv.bind('<Double-Button>', self.extract_selection)
        self.cv.grid(row=0, column=1, sticky="nsew") 

        self.populate(self.tree_dict[''])
        # Set default focus and selection on the first item of the entries
        self.listbox.selection_set(0)
        self.listbox.focus_set()

        self.window.geometry("600x400")  


    def populate(self, L):
        # Remove all items
        self.listbox.delete(0, last=self.listbox.size())

        # Replace with new items
        for e in L:
            self.listbox.insert(tk.END, e)


    def dbl_click_listbox(self, event):
        selection = self.listbox.selection_get()

        if selection == '..':
            # Go back to parent
            selection = DELIMITER.join(self.current_path.split(DELIMITER)[:-1])

        elif self.tar_root.getmember(selection).isfile():
            # If it's a file : un-compress it and open it in the temp dir with the default viewer
            filepath = self.tmpdir.name + DELIMITER + selection.split(DELIMITER)[-1]
            with open(filepath, 'wb') as f:
                self.opened_at_least_one_tmp = True
                tf = self.tar_root.extractfile(selection)
                f.write(tf.read())
                system_viewer(filepath)
            return

        self.current_path = selection
        self.populate(
              (['..'] if self.current_path != '' else [])  \
            + self.tree_dict[self.current_path] #[p.split(DELIMITER)[-1] for p in self.tree_dict[self.current_path]]
        )

    
    def click_listbox(self, event):
        selection = self.listbox.selection_get()

        canvas_width = self.window.winfo_width() - self.listbox.winfo_width() - 20 # Padding (10, 10)
        canvas_height = self.window.winfo_height() - 20


        self.cv.config(width=canvas_width + 20, height=canvas_height + 20)
        self.cv.delete('all')

        # If the display space is too small do not display anything…
        if min(canvas_height, canvas_width) <= 50:
            return


        # Parent dir is selected : do nothing
        if selection == '..':
            return

        # If not a file do not do anything
        if not self.tar_root.getmember(selection).isfile():
            self.cv.create_text(canvas_width // 2, 20, text="Double Click HERE to UnTar…", fill='blue')
            return
        
        # If not a recognised image extension: do nothing either
        if not (selection[-4:].lower() in ['.png', '.tif', '.jpg'] or selection[-5:].lower() in ['.jpeg', '.tiff', '.webp']):
            self.cv.create_text(canvas_width // 2, 20, text="Double Click HERE to UnTar…", fill='blue')
            return


        image_file = self.tar_root.extractfile(selection)
        
        im = Image.open(image_file)
        im.thumbnail((canvas_width, canvas_height))

        self.photo = ImageTk.PhotoImage(im)  

        self.cv.create_image((canvas_width - im.size[0]) // 2 + 10, (canvas_height - im.size[1]) // 2 + 10, image=self.photo, anchor='nw') 
        self.cv.update()


    def extract_selection(self, event):
        selection = self.listbox.selection_get()

        # Ignore parent dict…
        if selection == '..':
            return

        # Uncompress and open the dir where it's uncompressed…
        if self.tar_root.getmember(selection).isfile():
            self.tar_root.extract(selection)
            system_viewer(DELIMITER.join(selection.split(DELIMITER)[:-1]))
        else: # is dir
            recursive_extract = [selection]
            while len(recursive_extract):
                s = recursive_extract[0]
                recursive_extract = recursive_extract[1:]
                self.tar_root.extract(s)
                recursive_extract.extend(self.tree_dict[s])
            system_viewer(selection)


    def on_close(self):
        if not self.opened_at_least_one_tmp or messagebox.askokcancel(
                "Quit TarExplorer", "Do you want to quit the current viewer ?\n"
                "Files opened with double click in this interface will be lost…"
                ):
            self.tmpdir.cleanup()
            self.window.destroy()


    def mainloop(self):
        self.window.mainloop() 



if __name__ == "__main__":
    # Execute like if it was lanched from the current dir (to better find relative pathes)
    os.chdir(os.getcwd())
    te = TarFileExplorer(tar_filename=sys.argv[1])
    te.mainloop()



