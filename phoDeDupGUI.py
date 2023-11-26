import PySimpleGUI as sg
import phoDeDupLib as pddl
import os
import logging


#setup logfile
logger = logging.getLogger('pdd')
logging.basicConfig(filename="phoDeDup.log", format='%(asctime)s %(levelname)-8s %(message)s', 
	encoding="utf-8", level=logging.INFO)
logger.info("started phoDeDup")

#setup variables
PAGESIZE = 200
#used to abort multiple windows
#ABORT = False


sg.theme("DarkAmber")

#define the main window
selected_folders = []
lst = sg.Listbox(values=selected_folders, size=(60, 6), key="-LISTBOX-")
layout = [  [sg.Checkbox("debug messages in logfile", default=False, key="-debug-", enable_events=True, change_submits=True)],
			[sg.Text("Choose a folder to remove duplicates from using the 'Browse' button,\nthen 'Add folder to selection' to add it to the list.", size=(None, 2))], 
			[sg.Text("Folder:"), sg.In(size=(60,1), enable_events=True, key="-FOLDER-"), sg.FolderBrowse()],
			[sg.Button("Add folder to selection", key="Add"), sg.Button("Remove")],
			[lst], 
			[sg.Text("'Find duplicate images' will analyse the listed folder(s)\n for duplicate .jpg files, including within subfolders.", size=(None, 2))],
			[sg.Button("Find duplicate images", key="Run"), sg.Button("Exit")]
		]

window = sg.Window("Photo De-Duplicator", layout, resizable=True)


#define secondary file selection window
def popup(duplicates, totalDupes, thisPage, pageCount):

	#********************************
	#popup window contains: a Column, which contains in one list an Image, a Button, and a Column, again containing a list of checkboxes, labelled with a filename
	#building this happens inside-out
	#********************************
	#dupes
	
	#size of thumbnails to display
	thumbsize = (100, 100)
	
	item_list = []
	checkbox_keys = []
	for key in duplicates.keys():
		
		#generate checkbox keys for later use
		for f in duplicates[key]:
			checkbox_keys.append(f)
			
		#for each hash only load the image once (because identical),
		#so read the first one, dupes[key][0]
		
		#nasty way of getting nested items: left-aligned photo, 
		#with filenames and checkboxes vertically to the right
		checkboxes = [ [sg.Checkbox(x, key=x)] for x in duplicates[key] ]
		#print(checkboxes[0][-1:])
		try:
			img = pddl.convert_to_bytes(duplicates[key][0], thumbsize)
		except:
			img = bytes(0) # empty image, handles failed file read
		item_list.append([sg.Image(data=img), 
							sg.Button("Open\nimage", size=(5, 2), key="imagebutton"+duplicates[key][0]),
							sg.Column(checkboxes, pad=20)
						])
						
	#which photo range, from 0, dupesLen are we currently showing
	start = ((thisPage-1)*PAGESIZE) + 1
	stop = start + PAGESIZE - 1
	#unless we are on the last page, which likely won't be the full size:
	if thisPage == pageCount:
		stop = totalDupes
	
	layout_sec = [	[sg.Text("{} duplicated photo(s) found, this is page {} of {}.".format(totalDupes, thisPage, pageCount))],
					[sg.Text("Showing photos {}-{}.".format(start, stop))],
					[sg.Text("Select files to delete. You can select betwen none and all files for each photo.\nSelecting all items from a photo will delete all copies of that photo!", size=(None, 2))], 
					[sg.Column(item_list, size=(1000, 500), scrollable=True, vertical_scroll_only=False)],
					[sg.Text("'Close' may take some time to open the next window, be patient. ")],
					[sg.Button("Delete selected files and open the next page of photos", key="Delete"), sg.Button("Close this window and open the next page of photos", key="Close"), sg.Button("Exit and return to folder selection", key="Abort")]
				]
	#remove "Close" button if we're on the last page
	if thisPage == pageCount:
		del layout_sec[-1][1]
		
	window_sec = sg.Window("PDD", layout_sec, modal=True, resizable=True)
	
	ABORT = False
	while True:
		event_sec, values_sec = window_sec.read()
		if event_sec == sg.WIN_CLOSED or event_sec == "Close":
			break
		if event_sec == "Abort":
			ABORT = True
			break
		if event_sec.startswith("imagebutton"):
			os.startfile(event_sec[11:])  #strip out the "imagebuttton" from button/filename
		if event_sec == "Delete":
			files_to_delete = []
			ftd_counter = 0
			for f in checkbox_keys:
				checkbox = window_sec.Element(f)
				if checkbox.get():
					files_to_delete.append(f)
					ftd_counter += 1
			
			if not ftd_counter:
				sg.popup_ok("No files selected")
			elif sg.popup_ok_cancel("Are you sure you want to delete {} files?".format(ftd_counter)) == "OK":
				failure_message = ""
				for f in files_to_delete:
					try:
						os.remove(f)
						logger.info("deleted {}".format(f))
					except:
						logger.warning("failed to delete {}".format(f))
						failure_message = "\nSome files were skipped due to an error;\nSee phoDeDup.log for details"
				sg.popup_ok("Files deleted"+failure_message)
				break
	window_sec.close()
	return ABORT

dir = False
dupes = []
debug_old = False

while True:
	event, values = window.read()
	if event == sg.WIN_CLOSED or event == "Exit":
		break
	debug_checkbox = values["-debug-"]
	if debug_checkbox != debug_old:
		debug_old = debug_checkbox
		#has debug just been set to True?
		if debug_old:
			logger.setLevel(logging.DEBUG)
			logger.info("level set to DEBUG")
		else:
			logger.setLevel(logging.INFO)
			logger.info("level set to INFO")
	if event == "-FOLDER-":
		dir = values["-FOLDER-"].replace("/", os.sep) 	#fixes mixed / and \
		if os.path.isdir(dir) and dir not in selected_folders:
			selected_folders.append(dir)
	if event == "Add" and dir:
		window.Element("-LISTBOX-").Update(values=selected_folders)
	if event == "Remove":
		val = lst.get()[0]
		selected_folders.remove(val)
		window.Element("-LISTBOX-").Update(values=selected_folders)
	if event == "Run" and selected_folders:
		logger.info("analysing folders: " + ", ".join(selected_folders))
		dupes = pddl.getDupes(selected_folders)
		
		dupesLen = len(dupes)
		totalFiles = sum([len(list(dupes.values())[i]) for i in range(dupesLen)])
		
		logger.info(str(dupesLen) + " duplicated photos found")
		logger.info(str(totalFiles) + " total files")
		
		
		chunks = list(pddl.chunks(dupes, SIZE=PAGESIZE))
		pages = len(chunks)
		#ignore all input while popups are running
		window.disable()
		ABORT = False
		for i in range(pages):
			if not ABORT:
				dupes_chunk = chunks[i]
				#format: popup(duplicates, totalDupes, thisPage, pageCount)
				ABORT = popup(dupes_chunk, dupesLen, i+1, pages)
				
		ABORT = False
		window.enable()
		
#print(len(win

window.close()
logger.info("closed phoDeDup")
