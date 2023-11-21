import PySimpleGUI as sg
import phoDeDupLib as pddl
import os
import logging


#setup logfile
logging.basicConfig(filename="phoDeDup.log", format='%(asctime)s %(levelname)-8s %(message)s', 
	encoding="utf-8", level=logging.INFO)
logging.info("started phoDeDup")


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
def popup():
	#size of thumbnails to display
	thumbsize = (100, 100)
	
	item_list = []
	checkbox_keys = []
	for key in dupes.keys():
		
		#generate checkbox keys for later use
		for f in dupes[key]:
			checkbox_keys.append(f)
			
		#for each hash only read the image once (because identical),
		#so read the first one, dupes[key][0]
		
		#nasty way of getting nested items: left-aligned photo, 
		#with filenames and checkboxes vertically to the right
		checkboxes = [ [sg.Checkbox(x, key=x)] for x in dupes[key] ]
		#print(checkboxes[0][-1:])
		try:
			img = pddl.convert_to_bytes(dupes[key][0], thumbsize)
		except:
			img = bytes(0) # empty image, handles failed file read
		item_list.append([sg.Image(data=img), 
							sg.Button("Open\nimage", size=(5, 2), key="imagebutton"+dupes[key][0]),
							sg.Column(checkboxes, pad=20)
						])
	#item_list = item_list[-100:]
	#item_list.append([sg.Text("No more items")])
	#print("item_list {}".format(item_list[-2:]))
	#column = 
	layout_sec = [	[sg.Text("{} duplicated photo(s) found.".format(len(dupes)))],
					[sg.Text("Select files to delete. You can select betwen none and all files for each photo.\nSelecting all items from a photo will delete all copies of that photo!", size=(None, 2))], 
					[sg.Column(item_list, size=(1000, 500), scrollable=True, vertical_scroll_only=False)],
					[sg.Button("Close"), sg.Button("Delete selected files", key="Delete")]
				]
	
	window_sec = sg.Window("PDD", layout_sec, modal=True, resizable=True)
	
	while True:
		event_sec, values_sec = window_sec.read()
		if event_sec == sg.WIN_CLOSED or event_sec == "Close":
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
						logging.info("deleted {}".format(f))
					except:
						logging.warning("failed to delete {}".format(f))
						failure_message = "\nSome files were skipped due to an error;\nSee phoDeDup.log for details"
				sg.popup_ok("Files deleted"+failure_message)
				break
	window_sec.close()

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
			logging.getLogger().setLevel(logging.DEBUG)
			logging.info("level set to DEBUG")
		else:
			logging.getLogger().setLevel(logging.INFO)
			logging.info("level set to INFO")
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
		logging.info("analysing folders: " + ", ".join(selected_folders))
		dupes = pddl.getDupes(selected_folders)
		logging.debug(str(len(dupes)) + "dupes found")
		#select_all = False
		popup()
		
			
window.close()
logging.info("closed phoDeDup")
