# fspdf 

[![Build Status](https://travis-ci.org/kaiec/fspdf.svg?branch=master)](https://travis-ci.org/kaiec/fspdf)

Fill and sign any PDF.

## Description

Adobe Reader had a great feature where you can simply fill in text
into a PDF (not only in forms but simply by putting it over the PDF)
and then sign it (not cryptographically, but by adding an image with 
your signature).

This is exactly what is needed to produce filled and signed PDFs without 
having to print them. Great for a paperless office.

As Adobe Reader is not available anymore for Linux, this little tool hopefully can replace it.

The idea is that it will not do anything besides this one task: 

**Fill in arbitrary text and a signature.**

Currently this is a very early prototype, merely a proof-of-concept. fspdf creates an image from all overlay elements (texts and signatures) and turns it into an PDF. This is then stamped on the original PDF using pdftk's multi-stamp feature. If you are interested in joining the project, get in contact. 

Otherwise just wait until this thing works. The good thing is that I will be motivated to continue whenever a sucking PDF file to be filled and signed hits my inbox. I can assure you, this will happen :-)


## Installation

### Latest release:

```
pip install fspdf
```

### Dependencies: 

fspdf is basically a wrapper around convert and pdftk. 
Addtionally, you need python with tk support.

Linux packages:

- python3-tk
- pdftk
- imagemagick or graphicsmagick

For Ubuntu:

```
sudo apt install pdftk imagemagick python3-tk
```

### Get the code

If you want to use the latest development version:

```
git clone https://github.com/kaiec/fspdf.git
```

You can either install it using

```
python3 setup.py install
```

Or you run it directly using

```
./fspdf-runner.py PDFFILE.PDF SIGNATURE.PNG
```

Make sure you have Pillow installed in this case:

```
pip3 install Pillow
```


## Run

Create a transparent png with your signature.

```
fspdf PDFFILE.PDF SIGNATURE.PNG
```

- PDF automatically adjusts to window size.
- Left click to add a text (fill mode) or signature.
- Mouse wheel to adjust size of an element.
- Drag and drop to move element
- hit save button to export to PDFFILE-signed.PDF

## Todo / issues
- scrollable canvas
- config file to configure the signature
- date stamps with configurable date format
- multiline text with adjustable line height (to fill in tables)
- ...
