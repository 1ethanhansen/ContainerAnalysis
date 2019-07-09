import os
import sys
import yaml
import tarfile
import urllib
import shutil
import logging
import errno
from nested_lookup import nested_lookup

		
def mkdir_p(path):
	"""Allow us to make sub dirs, just like mkdir -p
	This is used to move the files from the Application tarball into the permanet 
	Applications dir in the root of the project's dir. Why you ask? For debuggin of course!"""
	try:
		os.makedirs(path)
	except OSError as exc:  # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise

def generate_output(app_obj):
	"""writes to a 'yaml' file using some space and colons."""

	logging.info('%s: Num of images: %s Num of tags: %s Num of repos: %s', 
		app_obj.name, str(len(app_obj.images)), str(len(app_obj.tags)), str(len(app_obj.images)))

	with open ('generated_input.yaml', 'a') as outputski:
		if len(app_obj.images) != len(app_obj.tags) or len(app_obj.repos) != len(app_obj.images):
			#app_obj.is_bad = True
			outputski.write('# ' + app_obj.name + ':\n')
			outputski.write('# ***ERROR SOMETHING NOT FORMATTED CORRECTLY\n')
			outputski.write('# *** go to ./Applications and view the values.yaml file\n')
		else:
			outputski.write('  ' + app_obj.name + ':\n')
			for i in range(len(app_obj.images)):
				final_repo = 'hub.docker.com/' + app_obj.clean_repos[i] + '/' + str(app_obj.tags[i])
				image = str(app_obj.images[i])

				if str(app_obj.images[i]) == "" or str(app_obj.images[i]) is None:
					image = "imageNAme" #TODO this is a quick fix for --debug mode and ibm-cem
				outputski.write('    '+ image + ': ' + final_repo + '\n')

def parse_image_repo(app_obj):
	"""from list of repo strings, get image names and repos.
		will use ibmcom if no repo is there"""

	if (len(app_obj.repos) != 0 and app_obj.repos is not None):
		for repo in app_obj.repos:
			if repo is None:#double check it
				continue

			if "ibmcom" in repo:#repos = ibmcom/image_name or image_name or ibmcom
				if "/" in repo:
					app_obj.clean_repos.append(repo.split("/",1)[0])
					app_obj.images.append(repo.split("/",1)[1])
					#at this point, have all the info
			else:
				if "/" in repo:
					app_obj.clean_repos.append(repo.split("/",1)[0])
					app_obj.images.append(repo.split("/",1)[1])
				else:
					#its not a repo, its the image name
					#print "ibmcom NOT in repo. and NO SLASH!\n"
					app_obj.images.append(repo)
					app_obj.clean_repos.append("ibmcom")

	"""write a yaml file to easily see exactly what info about each 
	container in the App was parsed"""
	if logging.getLogger().level == logging.DEBUG:
		generate_output(app_obj)

def get_app_info(app_obj, yaml_file):
	"""Loads an apps values.yaml into yaml_doc. 
	use nested_lookup library to get repositories, images, and their tags"""

	with open(yaml_file, 'r') as values:
		yaml_doc = yaml.safe_load(values)

	#results from this will contain repository results
	image_results = nested_lookup(key='image', document=yaml_doc, wild=True, with_keys=True)

	tag_from_image = nested_lookup(key='tag', document=image_results, wild=True)

	#print tag_from_image

	if app_obj.name == "ibm-microclimate":
		tag_from_image = [item for sublist in tag_from_image for item in sublist]

	if app_obj.name == "ibm-reactive-platform-lagom-sample" or app_obj.name == "ibm-eventstreams-rhel-dev":
		#this app contains a large list comprised of another list and a dict
		#all the tags are the same so grab teh first value in the dict
		for tag in tag_from_image:
			if type(tag) is dict:
				for k,v in tag.items():
					tag_from_image = v

	# add the tags to app obj
	if (len(tag_from_image) > 0):
		if app_obj.name == "ibm-eventstreams-dev":
			#the first member of the list is a dict so turn it into a dict
			tag_dict = next(item for item in tag_from_image[0])

			for image,tag in tag_dict.items():
				app_obj.tags = str(tag)
		else:
			app_obj.tags = tag_from_image

	repo_from_image = nested_lookup(key='repository', document=image_results, wild=True)

	#ibm-ace-server-dev is getting a dict in a list as the repo_from_image
	if app_obj.name == "ibm-ace-server-dev":
		#the format we get is {image: repo}
		ace_server_dict = next(item for item in repo_from_image)
		for image,repo in ace_server_dict.items():
			app_obj.images.append(str(image))
			app_obj.repos.append(str(repo))
			app_obj.clean_repos.append(str(repo))
		if len(app_obj.images) != len(app_obj.tags):
			#there is a single tag for all the images. so add more tags
			missing_tags = len(app_obj.images) - len(app_obj.tags)
			for i in range(missing_tags):
				app_obj.tags.append(str(app_obj.tags[0]))

		return

	if (len(repo_from_image) == 0):
		repo_from_image = nested_lookup(key='name', document=image_results, wild=True)
		if (len(repo_from_image) == 0):
			repo_from_image = nested_lookup(key='imageName', document=image_results, wild=True)
			if (len(repo_from_image) == 0):
				repo_from_image = nested_lookup(key='Image', document=image_results, wild=True)

	#add repos to app obj
	logging.info('%s Num of repos: %s', app_obj.name, str(len(repo_from_image)))

	# add repos to app object
	if len(repo_from_image) > 0:
		for repo in repo_from_image:

			#TODO for microclimate, this repo var is actually a list of 2 repos along with other lists
			if isinstance(repo, list):#could be a sub list (ibm-microservicebuilder-pipeline)
				for i in repo:
					#print "\n repo is a list, has member: " + str(i)
					if type(i) is dict: #the image name may be a dict so iterate
					#	print "\n repo is a DICT"
						for k,v in i.items(): 
							if "ibmcom" in str(v) and "/" in str(v):
								#typically this means all the repos use the same tag_from_image
					#			print "\n DICT has ibmcom and slash " + str(v)
								if type(v) is dict:
					#				print "\n DICT_SUB_DICT!"
									for j,l in v.items(): 
										if "ibmcom" in str(l) and "/" in str(l):
											app_obj.repos.append(str(v))
								else:
									app_obj.repos.append(str(v))

					if type(i) != dict:
						# it should be in format org/app_name MUST CONTAIN / (not a dict)
						if "ibmcom" in str(i) and "/" in str(i):
							app_obj.repos.append(str(i))
			else:
				if '/' in str(repo):
					#SEEMS LIKE THE BEST (ONLY) WORKING EXAMPLES. repo aint a sublist and has a slash
					logging.info('repo: %s', repo)
					app_obj.repos.append(repo)
				else:
					repo = "ibmcom/" + repo
					app_obj.repos.append(str(repo))
					#TODO ibm-eventstreams-dev lands here with "ibmcom" as the repo!
					#repo is not a list and has no slash
	else: 
		print("\n Cannot locate any repos for images. \n NADA! \n")

	#NOTE: number tags != number of repos
	parse_image_repo(app_obj)

def chart_file(members):
	"""just extract the Chart.yaml file so that the App's directory has only 1 file"""

	for tarinfo in members:
		if os.path.splitext(tarinfo.name)[0].endswith("Chart") and os.path.splitext(tarinfo.name)[1] == ".yaml":
			if os.path.splitext(tarinfo.name)[0].count("/") == 1: 
			#this ensures we get the Chart.yaml in the top level dir of the App
				yield tarinfo

def obtain_Chart_yaml(main_image, tar):

	tar.extractall(members=chart_file(tar))
	for item in tar.getmembers():
		#Avoid getting 2 of the same files.
		if main_image.Charts_exists is True or item.isdir():
			return
		if item.name.endswith('Chart.yaml') and item.isreg():
			main_image.Charts_exists = True
		
			yaml_file_path_chart = os.path.dirname(os.path.realpath(item.name)) + "/Chart.yaml"
		   #Open up the yaml and just extract keywords from Chart.yaml
			with open(yaml_file_path_chart, 'r') as Chart:
				chart_yaml_doc = yaml.safe_load(Chart)
				if (len(nested_lookup('keywords', document=chart_yaml_doc)) > 0):
					keywords = nested_lookup('keywords', document=chart_yaml_doc)
					for key in keywords:
						for k in key:
							main_image.add_keyword(k)
					
			#done with the re-extracted folder so remove it
			shutil.rmtree(str(os.getcwd() + "/" + main_image.name))

def move_files(app_name, file_in_tar):
	"""once we have the values.yaml or Chart.yaml, move these files to 
	Applications/app_name/ so we can read the yaml files from there and close the tarfile"""

	original_location = os.path.dirname(os.path.realpath(file_in_tar))
	
	#TODO - when running testit, does not make a sub dir of app name
	# a typical big run makes a subdir of the app name which i handle below
	new_location = os.getcwd() + "/Applications/" + app_name

	logging.info('Move from %s to %s', original_location, new_location)

	#current dir is scripts main dir, so just point to Applications/app_name/values.yaml
	shutil.move(str(original_location), str(new_location))

	#recursively get the file since it's in a subdir
	for root, dirs, files in os.walk(new_location):
		for file in files:
			if file.endswith(".yaml"):
				yaml_location = os.path.join(root, file)

	return yaml_location

def value_file(members):
	"""just extract the values.yaml file so that the App's directory has only 1 file"""
	for tarinfo in members:
		if os.path.splitext(tarinfo.name)[0].endswith("values") and os.path.splitext(tarinfo.name)[1] == ".yaml":
			if os.path.splitext(tarinfo.name)[0].count("/") == 1: 
			#this ensures we get the values.yaml in the top level dir of the App
				yield tarinfo

def obtain_values_yaml(main_image, tar):
	"""inside the tgz is the values.yaml which will give us the info to query
	dockerhub"""
	tar.extractall(members=value_file(tar))
	for item in tar.getmembers():
		if item.isdir():
			return
		#Avoid getting 2 of the same files.
		if main_image.values_exists is True: # or item.isdir():
			return
		if item.name.endswith('values.yaml') and item.isreg():
			main_image.values_exists = True
			yaml_location = move_files(main_image.name, item.name)
			get_app_info(main_image, yaml_location)

def get_tarfile(main_image):
	"""get the app name = MainImage.name along with the tgz of the app."""

	file_tmp = urllib.urlretrieve(main_image.url, filename=None)[0]
	base_name = os.path.basename(main_image.url)
	tar = tarfile.open(file_tmp)

	obtain_values_yaml(main_image, tar)
	obtain_Chart_yaml(main_image,tar)
