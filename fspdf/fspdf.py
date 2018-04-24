# -*- coding: utf-8 -*-


"""fspdf.fspdf: Fill and sign PDFs."""


__version__ = "0.1.1"


import tkinter as tk
import os
import argparse
import configparser
import tempfile
import shutil
import subprocess
from PIL import ImageTk, Image, ImageFont, ImageDraw


class Page():
    def __init__(self, img_file, canvas):
        self.img_file = img_file
        self.img = Image.open(img_file)
        self.width = self.img.width
        self.height = self.img.height
        self.rel_width = 1
        self.annotations = []
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
        for s in self.annotations:
            s.canvas_draw()
        self.canvas.update_idletasks()
        print("Page redrawn at {}/{} ({}x{})".format(self.xoffset,
              self.yoffset, self.width, self.height))


class Annotation():
    def __init__(self, page, img, event=None):
        self.page = page
        page.annotations.append(self)
        self.img = img
        self.img_orig = img
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
            self.x = event.x
            self.y = event.y
            self.rel_x = (self.x - page.xoffset) / page.width
            self.rel_y = (self.y - page.yoffset) / page.height
            self.page.canvas_draw()

    def delete(self, event):
        self.page.canvas.delete(tk.CURRENT)
        self.page.annotations.remove(self)

    def resize(self, width):
        if width > self.page.img.width:
            width = self.page.img.width
        if width < 50:
            width = 50
        if self.img.width == width:
            return
        self.width = width
        self.rel_width = width / self.page.width
        nimg = self.img_orig
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
        self.page.canvas.tag_bind(self.oid, "<Button-3>", self.delete)
        print("Drawing annotation at {}/{}, oid={}, width: {}"
              .format(self.x,
                      self.y,
                      self.oid,
                      self.width))
        self.page.canvas.update_idletasks()

    def image_draw(self, image):
        x = int(self.rel_x * image.width)
        y = int(self.rel_y * image.height)
        width = int(self.rel_width * image.width)
        nimg = self.img_orig
        scale = width / nimg.width
        height = int(nimg.height * scale)
        nimg = nimg.resize((width, height), Image.ANTIALIAS)
        image.paste(nimg, (x - width // 2, y - height // 2))

    def smaller(self, event):
        self.resize(self.img.width * 0.9)
        self.page.canvas.itemconfig(tk.CURRENT, image=self.tkimg)
        self.page.canvas.update_idletasks()

    def larger(self, event):
        self.resize(self.img.width * 1.2)
        self.page.canvas.itemconfig(tk.CURRENT, image=self.tkimg)
        self.page.canvas.update_idletasks()

    def drag_start(self, event):
        '''Begining drag of an object'''
        event.widget.tag_click = True
        # record the item and its location
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        print("Start dragging at {}x{}".format(event.x, event.y))
        print("Current pos: {}x{}".format(self.x, self.y))

    def drag_end(self, event):
        '''End drag of an object'''
        self.rel_x = (self.x - self.page.xoffset) / self.page.width
        self.rel_y = (self.y - self.page.yoffset) / self.page.height
        # reset the drag information
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0
        print("End dragging at {}x{}".format(event.x, event.y))
        print("Current pos: {}x{}".format(self.x, self.y))
        self.page.canvas_draw()

    def drag(self, event):
        '''Handle dragging of an object'''
        # compute how much the mouse has moved
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        # move the object the appropriate amount
        self.page.canvas.move(tk.CURRENT, delta_x, delta_y)
        self.x = self.x + delta_x
        self.y = self.y + delta_y
        # record the new position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y


class Fspdf:
    def __init__(self, pdf_file, sig_file):
        self.pdf_file = pdf_file
        self.sig_file = sig_file

        # Create temporary directory
        tempdir = tempfile.TemporaryDirectory(prefix="pdfsign-")
        self.tmp_pdf = os.path.join(tempdir.name, "input.pdf")
        print("Temporary Directory: {}".format(tempdir))
        print("Working on {}".format(self.pdf_file))

        # Copy pdf file to temporary directory
        shutil.copyfile(self.pdf_file, self.tmp_pdf)

        # Convert it to png images
        subprocess.run(["convert", "-density", "150", self.tmp_pdf,
                        "-alpha", "off",
                       "".join([self.tmp_pdf[:-4], "-%04d.png"])],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)

        # Filenames of png images are sorted and correspond to pages in PDF
        png_files = sorted([os.path.join(tempdir.name, f)
                           for f in os.listdir(tempdir.name)
                           if f[-4:] == ".png"])
        print("Generated page images: {}".format(", ".join(png_files)))

        self.pages = []

        root = tk.Tk()

        img = Image.open(png_files[0])
        print("Image dimensions: {}x{}".format(img.width, img.height))

        left = tk.Frame(root, bg="white")
        right = tk.Frame(root, bg="red")

        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        self.mode = tk.StringVar()
        self.mode.set("off")

        off_button = tk.Radiobutton(right, text="Off", variable=self.mode,
                                    value="off", indicatoron=0)
        sign_button = tk.Radiobutton(right, text="Sign", variable=self.mode,
                                     value="sign", indicatoron=0)
        fill_button = tk.Radiobutton(right, text="Fill", variable=self.mode,
                                     value="fill", indicatoron=0)
        off_button.pack(fill=tk.X)
        sign_button.pack(fill=tk.X)
        fill_button.pack(fill=tk.X)

        self.text = tk.Text(right, height=10, width=30)
        self.text.pack()

        prev_button = tk.Button(right, text="Previous page",
                                command=self.prev_page)
        prev_button.pack()

        next_button = tk.Button(right, text="Next page",
                                command=self.next_page)
        next_button.pack()

        ps_button = tk.Button(right, text="Save signed PDF",
                              command=self.save_pdf)
        ps_button.pack()

        self.canvas = tk.Canvas(left)
        self.canvas.tag_click = False
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        self.canvas.update()
        for img in png_files:
            p = Page(img, self.canvas)
            self.pages.append(p)
        self.page = self.pages[0]
        self.page.canvas_draw()

        self.canvas.bind("<Configure>", self.resize)
        self.canvas.bind("<Button-1>", self.create_element)
        tk.mainloop()

    def save_pdf(self):
        orig = Image.open(self.page.img_file)
        stamp_files = []
        empty = Image.new("RGBA", (orig.width, orig.height), (0, 0, 0, 0))

        for p in self.pages:
            stamp = Image.new("RGBA", (orig.width, orig.height), (0, 0, 0, 0))
            for s in p.annotations:
                s.image_draw(stamp)
            stamp_file = "{}-stamp.png".format(p.img_file[:-4])
            stamp.save(stamp_file)
            stamp_files.append(stamp_file)

        empty_file = "{}-empty.png".format(self.page.img_file[:-4])
        empty.save(empty_file)
        stamp_pdf = "{}-stamp.pdf".format(self.tmp_pdf[:-4])
        # Convert it to png images
        subprocess.run(["convert", *stamp_files, empty_file, stamp_pdf],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)
        subprocess.run(["pdftk", self.tmp_pdf, "multistamp", stamp_pdf,
                        "output", "{}-signed.pdf".format(self.pdf_file[:-4])],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=True)

    def resize(self, event):
        print("Window resiszing...")
        print("event {}x{}".format(event.width, event.height))
        print("canvas {}x{}".format(self.canvas.winfo_width(),
                                    self.canvas.winfo_height()))
        self.page.box_resize(self.canvas.winfo_width(),
                             self.canvas.winfo_height())
        self.page.canvas_draw()

    def create_element(self, event):
        if event.widget.tag_click:
            event.widget.tag_click = False
            return
        print("Left click, mode is \"{}\".".format(self.mode.get()))
        if self.mode.get() == "sign":
            img = Image.open(self.sig_file)
            Annotation(self.page, img, event)
        elif self.mode.get() == "fill":
            value = self.text.get("1.0", "end-1c").strip()
            if value == "":
                print("No text, returning...")
                return
            fnt = ImageFont.truetype('Pillow/Tests/fonts/DejaVuSans.ttf', 72)
            txt = Image.new('RGBA', (1000, 1000), (0, 0, 0, 0))
            d = ImageDraw.Draw(txt)
            size = d.textsize(value, font=fnt)
            if size[0] == 0 or size[1] == 0:
                print("Fill image is empty, returning")
                return
            txt = Image.new('RGBA', size, (0, 0, 0, 0))
            d = ImageDraw.Draw(txt)
            print("Size of text: {}".format(size))
            d.text((0, 0), value, font=fnt, fill=(0, 0, 0, 255))
            Annotation(self.page, txt, event)

    def prev_page(self):
        cur = self.pages.index(self.page)
        if cur > 0:
            self.page = self.pages[cur - 1]
            self.page.canvas_draw()

    def next_page(self):
        cur = self.pages.index(self.page)
        if cur < len(self.pages) - 1:
            self.page = self.pages[cur + 1]
            self.page.canvas_draw()


def main():
    config = configparser.ConfigParser()
    for loc in (os.curdir, os.path.expanduser("~"),
                "/etc/fspdf"):
        try:
            with open(os.path.join(loc, "fspdf.conf")) as source:
                config.read(source)
        except IOError:
            pass
    parser = argparse.ArgumentParser(description="Fill and sign any PDF.")
    parser.add_argument('pdf_file', metavar='PDF_FILE', type=str,
                        help='The PDF file to be filled and signed')
    parser.add_argument('sig_file', metavar='SIGNATURE_FILE', type=str,
                        help='A transparent png image wih yo signature')
    args = parser.parse_args()
    print("Executing fspds version %s." % __version__)
    Fspdf(args.pdf_file, args.sig_file)
