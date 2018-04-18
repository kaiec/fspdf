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
        # this data is used to keep track of an
        # item being dragged
        self._drag_data = {"x": 0, "y": 0}
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
        self.page.canvas.tag_bind(self.oid, "<ButtonPress-1>", self.drag_start)
        self.page.canvas.tag_bind(self.oid, "<ButtonRelease-1>", self.drag_end)
        self.page.canvas.tag_bind(self.oid, "<B1-Motion>", self.drag)
        print("Drawing signature at {}/{}, oid={}".format(self.x,
                                                          self.y, self.oid))
        self.page.canvas.update_idletasks()

    def image_draw(self, image):
        x = int(self.rel_x * image.width)
        y = int(self.rel_y * image.height)
        width = int(self.rel_width * image.width)
        nimg = Image.open(self.img_file)
        scale = width / nimg.width
        height = int(nimg.height * scale)
        nimg = nimg.resize((width, height), Image.ANTIALIAS)
        image.paste(nimg, (x - width // 2, y - height // 2))

    def smaller(self, event):
        self.resize(self.img.width * 0.9)
        canvas.itemconfig(tk.CURRENT, image=self.tkimg)
        canvas.update_idletasks()

    def larger(self, event):
        self.resize(self.img.width * 1.2)
        canvas.itemconfig(tk.CURRENT, image=self.tkimg)
        canvas.update_idletasks()

    def drag_start(self, event):
        '''Begining drag of an object'''
        event.widget.tag_click = True
        # record the item and its location
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def drag_end(self, event):
        '''End drag of an object'''
        self.x = self._drag_data["x"] - page.xoffset
        self.y = self._drag_data["y"] - page.yoffset
        self.rel_x = self.x / self.page.width
        self.rel_y = self.y / self.page.height
        # reset the drag information
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0

    def drag(self, event):
        '''Handle dragging of an object'''
        # compute how much the mouse has moved
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        # move the object the appropriate amount
        self.page.canvas.move(tk.CURRENT, delta_x, delta_y)
        # record the new position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y


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


def save_pdf():
    orig = Image.open(page.img_file)
    stamp = Image.new("RGBA", (orig.width, orig.height), (0, 0, 0, 0))
    empty = Image.new("RGBA", (orig.width, orig.height), (0, 0, 0, 0))
    for s in page.signatures:
        s.image_draw(stamp)
    stamp_file = "{}-stamp.png".format(page.img_file[:-4])
    empty_file = "{}-empty.png".format(page.img_file[:-4])
    stamp_pdf = "{}-stamp.pdf".format(tmp_pdf[:-4])
    stamp.save(stamp_file)
    empty.save(empty_file)
    # Convert it to png images
    subprocess.run(["convert", stamp_file, empty_file, stamp_pdf],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    subprocess.run(["pdftk", tmp_pdf, "multistamp", stamp_pdf, "output",
                   "{}-signed.pdf".format(pdf_file[:-4])],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def resize(event):
    print("Window resiszing...")
    print("event {}x{}".format(event.width, event.height))
    print("canvas {}x{}".format(canvas.winfo_width(), canvas.winfo_height()))
    page.box_resize(canvas.winfo_width(), canvas.winfo_height())
    page.canvas_draw()


def create_element(event):
    if event.widget.tag_click:
        event.widget.tag_click = False
        return
    print("Left click, mode is \"{}\".".format(mode.get()))
    if mode.get() == "sign":
        Signature(page, sig_file, event)
    elif mode.get() == "fill":
        pass


root = tk.Tk()

img = Image.open(png_files[0])
print("Image dimensions: {}x{}".format(img.width, img.height))

left = tk.Frame(root, bg="white")
right = tk.Frame(root, bg="red")

left.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
right.pack(side=tk.RIGHT, fill=tk.Y)

mode = tk.StringVar()
mode.set("off")

off_button = tk.Radiobutton(right, text="Off", variable=mode, value="off",
                            indicatoron=0)
sign_button = tk.Radiobutton(right, text="Sign", variable=mode, value="sign",
                             indicatoron=0)
fill_button = tk.Radiobutton(right, text="Fill", variable=mode, value="fill",
                             indicatoron=0)
off_button.pack(fill=tk.X)
sign_button.pack(fill=tk.X)
fill_button.pack(fill=tk.X)

ps_button = tk.Button(right, text="Save signed PDF",
                      command=save_pdf)
ps_button.pack()

canvas = tk.Canvas(left)
canvas.tag_click = False
canvas.pack(fill=tk.BOTH, expand=tk.YES)
canvas.update()
page = Page(png_files[0], canvas)
page.canvas_draw()

canvas.bind("<Configure>", resize)
canvas.bind("<Button-1>", create_element)
tk.mainloop()
