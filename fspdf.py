import tkinter as tk
import sys
import os
import tempfile
import shutil
import subprocess
from PIL import ImageTk, Image


class Page():
    def __init__(self, img_file, canvas):
        self.img_file = img_file
        self.img = Image.open(img_file)
        self.width = img.width
        self.height = img.height
        self.rel_width = 1
        self.signatures = []
        self.canvas = canvas
        self.xoffset = (self.canvas.winfo_width() - self.width) / 2
        self.yoffset = (self.canvas.winfo_height() - self.height) / 2
        self.tkimg = ImageTk.PhotoImage(image=self.img)
        self.box_resize(self.canvas.winfo_width(),
                        self.canvas.winfo_height())

    def box_resize(self, width, height):
        sw = width / self.width
        sh = height / self.height
        scale = sw if sw < sh else sh
        self.width = int(self.width*scale)
        self.height = int(self.height*scale)
        self.xoffset = (width - self.width) / 2
        self.yoffset = (height - self.height) / 2
        self.img = Image.open(self.img_file)
        self.img = self.img.resize((self.width, self.height),
                                   Image.ANTIALIAS)
        print("New image dimensions: {}x{}".format(self.img.width,
              self.img.height))
        self.tkimg = ImageTk.PhotoImage(image=self.img)
        print("Page resized to {}x{}".format(self.width, self.height))

    def canvas_draw(self):
        self.canvas.delete("all")
        self.canvas.create_image(self.xoffset, self.yoffset,
                                 anchor=tk.NW, image=self.tkimg)
        for s in self.signatures:
            s.canvas_draw()
        self.canvas.update_idletasks()
        print("Page redrawn at {}/{} ({}x{})".format(self.xoffset,
              self.yoffset, self.width, self.height))


class Signature():
    def __init__(self, page, img_file, event=None):
        self.page = page
        page.signatures.append(self)
        self.img_file = img_file
        self.img = Image.open(img_file)
        self.width = img.width
        self.rel_width = self.width / page.width
        self.tkimg = ImageTk.PhotoImage(image=self.img)
        self.oid = None
        self.x = None
        self.y = None
        self.rel_x = None
        self.rel_y = None
        if event is not None:
            self.x = event.x - page.xoffset
            self.y = event.y - page.yoffset
            self.rel_x = self.x / page.width
            self.rel_y = self.y / page.height
            self.canvas_draw()

    def resize(self, width):
        if width > self.page.img.width:
            width = self.page.img.width
        if width < 50:
            width = 50
        if self.img.width == width:
            return
        self.width = width
        self.rel_width = width / self.page.width
        nimg = Image.open(self.img_file)
        scale = width / nimg.width
        self.img = nimg.resize((int(width), int(nimg.height * scale)),
                               Image.NEAREST)
        self.tkimg = ImageTk.PhotoImage(image=self.img)

    def canvas_draw(self):
        if self.oid is not None:
            self.page.canvas.delete(self.oid)
        self.x = self.rel_x * self.page.width + self.page.xoffset
        self.y = self.rel_y * self.page.height + self.page.yoffset
        self.resize(self.page.width * self.rel_width)
        self.oid = self.page.canvas.create_image(self.x, self.y,
                                                 anchor=tk.CENTER,
                                                 image=self.tkimg)
        self.page.canvas.tag_bind(self.oid, "<Button-4>", self.smaller)
        self.page.canvas.tag_bind(self.oid, "<Button-5>", self.larger)
        print("Drawing signature at {}/{}, oid={}".format(self.x,
                                                          self.y, self.oid))
        self.page.canvas.update_idletasks()

    def smaller(self, event):
        self.resize(self.img.width * 0.9)
        canvas.itemconfig(tk.CURRENT, image=self.tkimg)
        canvas.update_idletasks()

    def larger(self, event):
        self.resize(self.img.width * 1.2)
        canvas.itemconfig(tk.CURRENT, image=self.tkimg)
        canvas.update_idletasks()


pdf_file = sys.argv[1]
sig_file = sys.argv[2]

# Create temporary directory
tempdir = tempfile.TemporaryDirectory(prefix="pdfsign-")
tmp_pdf = os.path.join(tempdir.name, "input.pdf")
print("Temporary Directory: {}".format(tempdir))
print("Working on {}".format(pdf_file))

# Copy pdf file to temporary directory
shutil.copyfile(pdf_file, tmp_pdf)

# Convert it to png images
subprocess.run(["convert", "-density", "150", tmp_pdf, "-alpha", "off",
               "".join([tmp_pdf[:-4], "-%04d.png"])],
               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

# Filenames of png images are sorted and correspond to pages in PDF
png_files = sorted([os.path.join(tempdir.name, f)
                   for f in os.listdir(tempdir.name) if f[-4:] == ".png"])
print("Generated page images: {}".format(", ".join(png_files)))


def create_postscript():
    canvas.postscript(file="test1.ps", colormode="color")


def resize(event):
    print("Window resiszing...")
    print("event {}x{}".format(event.width, event.height))
    print("canvas {}x{}".format(canvas.winfo_width(), canvas.winfo_height()))
    page.box_resize(canvas.winfo_width(), canvas.winfo_height())
    page.canvas_draw()


root = tk.Tk()

img = Image.open(png_files[0])
print("Image dimensions: {}x{}".format(img.width, img.height))

left = tk.Frame(root, bg="white")
right = tk.Frame(root, bg="red")

left.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
right.pack(side=tk.RIGHT, fill=tk.Y)

psButton = tk.Button(right, text="Create Postscript",
                     command=create_postscript)
psButton.pack()

canvas = tk.Canvas(left)
canvas.pack(fill=tk.BOTH, expand=tk.YES)
canvas.update()
page = Page(png_files[0], canvas)
page.canvas_draw()

canvas.bind("<Configure>", resize)
canvas.bind("<Button-1>", lambda event: Signature(page,
                                                  sig_file, event))
tk.mainloop()
