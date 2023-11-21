import os, hashlib
import io
import PIL
from PIL import Image
import base64
import logging

def getAllFiles(path):
	files = []
	try:
		thisDir = os.scandir(path)
	except:
		logging.debug("failed getAllFiles os.scandir() for: " + str(path))

	for i in thisDir:
		try:
			if i.is_file():
				files.append(i.path)
			elif i.is_dir():
				for x in getAllFiles(i.path):
					files.append(x)
		except:
			logging.debug("failed getAllFiles is_file or is_dir for: " + str(i.path))
			
	return files
	
def sha256sum(filename):
    with open(filename, 'rb', buffering=0) as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def getDupes(directories, verbose=True) -> dict:
	#directories to dedupe, print text?
	hashes = {}
	for folder in directories:
		allFiles = getAllFiles(folder)
		#select all the .jpg files
		jpgs = [x for x in allFiles if x.lower().endswith(".jpg")]
		counter = 0
		for x in jpgs:
			h = sha256sum(x)
			if h in hashes:
				hashes[h].append(x)
			else:
				hashes[h] = [x]

	hashes_copy = {}

	for key in hashes.keys():
		#logging.info(key)
		value = hashes[key]	#is a list
		if len(value) > 1: # is there more than one entry?
			hashes_copy[key] = value
	
	return hashes_copy
	
def convert_to_bytes(file_or_bytes, resize=None, fill=False):
	'''
	Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
	Turns into  PNG format in the process so that can be displayed by tkinter
	:param file_or_bytes: either a string filename or a bytes base64 image object
	:type file_or_bytes:  (Union[str, bytes])
	:param resize:  optional new size
	:type resize: (Tuple[int, int] or None)
	:return: (bytes) a byte-string object
	:rtype: (bytes)
	'''
	#https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Image_Viewer_Thumbnails.py

	if isinstance(file_or_bytes, str):
		img = PIL.Image.open(file_or_bytes)
	else:
		try:
			img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
		except Exception as e:
			dataBytesIO = io.BytesIO(file_or_bytes)
			img = PIL.Image.open(dataBytesIO)

	cur_width, cur_height = img.size
	if resize:
		new_width, new_height = resize
		scale = min(new_height / cur_height, new_width / cur_width)
		img = img.resize((int(cur_width * scale), int(cur_height * scale)), PIL.Image.LANCZOS)
	if fill:
		img = make_square(img, THUMBNAIL_SIZE[0])
	with io.BytesIO() as bio:
		img.save(bio, format="PNG")
		del img
		return bio.getvalue()
