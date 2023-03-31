
def import_template(view, event):
	"""
	DESCRIPTION: converts a template file from csv into json, and displays it in a preview table
	PARAMETERS: view (object): the form that is importing the file, event(object): the file to upload
	RETURNS: null
	"""
	file_string = event.file.getString()
	view.view.custom.data = []
	for line in file_string.split("\n")[1:]:
		line = line.split(",")
		
		view.view.custom.data.append({
			"English": line[0],
			"Spanish": line[1]
		})
		system.util.modifyTranslation(line[0], line[1], "es")
	view.view.custom.uploaded = True
	
	
def download_template_file(data):
	"""
	DESCRIPTION: downloads a file that represents all the setpoints in a dashboard as a CSV(but not their positions)
	PARAMETERS: view (object): the carousel that holds all the pages of the template
	RETURNS: null
	"""
	data = General.Conversion.convert_dataset_to_list(data)
	translations = "English, Spanish\n"
	for english_spanish in data:
#		system.perspective.print(data)
		translations += "%s,%s\n"%(
			english_spanish["English"],
			english_spanish["Spanish"]
		)
	system.perspective.download("translation.csv", translations)
	
def add_entry(en, es): # get data from add entry page 
	pass
	