import os
import yaml
import sys
from objects.hub import Hub
from objects.image import App
from objects.image import Image

from utils.indexparser import get_tarfile

#Just making sure travis CI works for now
def travis_trial():
	print("It works")
	return True

def output_app_keywords(main_image, f):
	""" use keywords from App. no for loop so outputs only once"""

	if 'amd64' in main_image.keywords and 'ppc64le' in main_image.keywords and 's390x' in main_image.keywords:
		f.write('%s,Y,Y,Y\n' %(main_image.name)) 
		return

	if 'amd64' in main_image.keywords and 'ppc64le' in main_image.keywords:
		f.write('%s,Y,Y,N\n' %(main_image.name)) 
		return
	
	if 'amd64' in main_image.keywords and 's390x' in main_image.keywords:
		f.write('%s,Y,N,Y\n' %(main_image.name))
		return

	if 'ppc64le' in main_image.keywords and 's390x' in main_image.keywords:
		f.write('%s,N,Y,Y\n' %(main_image.name))
		return

	if 'amd64' in main_image.keywords:
		f.write('%s,Y,N,N\n' %(main_image.name))
		return

	if 'ppc64le' in main_image.keywords:
		f.write('%s,N,Y,N\n' %(main_image.name))
		return

	if 's390x' in main_image.keywords:
		f.write('%s,N,N,Y\n' %(main_image.name))
		return

	# if arch is not in keyword, pring it out anyways
	f.write('%s,N,N,N\n' %(main_image.name))

def output_CSV(main_image, f):
	"""from a list of images in the App, determine if all the images are supported/
	If all the images are supported then do not output anything.

	This will return to runit() and do it again for another main image
	"""

	output_app_keywords(main_image, f)

	if main_image.is_bad == True:
		f.write(',,,,Images not parsed correctly from index.yaml\n')
		return

	for image_obj in main_image.sub_images:

		if image_obj.is_amd64 and image_obj.is_ppc64le and image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,%s,%s,Y,Y,Y,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,%s,%s,Y,Y,Y,N\n' % (image_obj.name, image_obj.container))

		if image_obj.is_amd64 and image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,%s,%s,Y,Y,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,%s,%s,Y,Y,N,N\n' % (image_obj.name, image_obj.container))
	
		if image_obj.is_amd64 and not image_obj.is_ppc64le and image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,%s,%s,Y,N,Y,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,%s,%s,Y,N,Y,N\n' % (image_obj.name, image_obj.container))
			
		if image_obj.is_amd64 and not image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,%s,%s,Y,N,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,%s,%s,Y,N,N,N\n' % (image_obj.name, image_obj.container))

		if not image_obj.is_amd64 and image_obj.is_ppc64le and image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,%s,%s,N,Y,Y,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,%s,%s,N,Y,Y,N\n' % (image_obj.name, image_obj.container))

			
		if not image_obj.is_amd64 and image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,%s,%s,N,Y,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,%s,%s,N,Y,N,N\n' % (image_obj.name, image_obj.container))
			 
		if not image_obj.is_amd64 and not image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,%s,%s,N,N,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				if image_obj.exist_in_repo == False: #TODO could use app.is_bad??
					main_image.is_bad = True
					f.write(',,,,%s NOT FOUND IN REPO,%s,N,N,N,N\n' % (image_obj.name, image_obj.container))
				else:
					f.write(',,,,%s,%s,N,N,N,N\n' % (image_obj.name, image_obj.container))

def add_header_to_yaml():
	"""add creds and proper formatting to yaml so we can runit"""

	#if we are not in debug mode, still need creds, so create the file
	if os.path.exists("generated_input.yaml") is False:
		open("generated_input.yaml", 'a').close()

	generated_input = os.getcwd() + "/generated_input.yaml"

	f = open(generated_input, "r")
	contents = f.readlines()
	f.close()

	contents.insert(0, "registries:\n")
	contents.insert(1, "  hub.docker.com:\n")
	contents.insert(2, "    ibmdev: MTAweWFyZC0=\n")
	contents.insert(3, "container-images:\n")

	f = open(generated_input, "w")
	contents = "".join(contents)
	f.write(contents)
	f.close()

	return generated_input

def get_registries(yaml_doc):
	"""setup Hub objects and store in a list of objects"""

	hub_list = [ ]

	with open(yaml_doc, 'r') as input_file:
		yaml_doc = yaml.safe_load(input_file)
	
	for url in yaml_doc['registries'].iteritems():
		for repos in url[1].iteritems():
			hub = Hub(url[0],repos[0],repos[1])
			hub_list.append(hub)
	return hub_list

def print_obj(app_obj):

	print("\nApp: %s \nLen Images: %s \n Sub Images: %s \n "%(app_obj.name, str(len(app_obj.images)), str(len(app_obj.sub_images))))

	print("keywords")
	print("----")
	for key in app_obj.keywords:
		print(key)

	for image_obj in app_obj.sub_images:
		print("\nimage name: %s"%(image_obj.name))
		print("image org: %s"%(image_obj.org))
		print("Num tags: %s"%(str(len(image_obj.tags))))
		for tag in image_obj.tags:
			print("tag: %s"%(tag))


def testit(app_name, yaml_doc):
	"""just get info for 1 app and print it out. 
	Start by parsing index.yaml and create a seperate dir for the app since we will not check black_list"""

	url_for_app = " "

	#keys = MainImage.name, values=url where a tgz file contains values.yaml
	for k, v in yaml_doc["entries"].iteritems():
		if k == app_name:
			url_for_app = ''.join(v[0]['urls']) #returns a list with only 1 element = url str
			break
		
	generated_yaml_doc = add_header_to_yaml() # add creds to top of yaml file
	hub_list = get_registries(generated_yaml_doc)
	"""create a Hub object containing url and creds. return a list of
	objects"""


	app_obj = App(app_name, str(url_for_app))

	#mkdir_p(str(os.getcwd() + "/Applications-TEST/" + app_obj.name)) #Create the Applications/app_name dir
	get_tarfile(app_obj) #Download tarballs and start parsing

	if str(len(app_obj.images)) == "0":
		print(app_obj.name)
		print("THIS app has no tags. Likely not parsed correctly")
		print("\nCheck out:")
		print("\t cat ./Applications/%s/values.yaml"%(app_obj.name))
		print("\nbye bye")
		sys.exit()


	yaml_doc = add_header_to_yaml() # add creds to top of yaml file
	hub_list = get_registries(yaml_doc)

	print("\n Begin test\n app_obj.image =? app_obj.tags")
	print(len(app_obj.images))
	print(len(app_obj.tags))
	for i in range(len(app_obj.images)):
		
		name = str(app_obj.images[i])
		org = str(app_obj.clean_repos[i])

		if len(app_obj.tags) == 0:
			print("NO CONTAINERS")
			container = "Not found!"
		else: 
			#print(app_obj.images)
			if len(app_obj.tags) < len(app_obj.images):
				container = str(app_obj.tags[0])
			else:
				container = str(app_obj.tags[i])


		image_obj = Image(name, org, container)
		regis = 'hub.docker.com/' #TODO - add more repos

		for obj in hub_list: #only authorize the regis for the image we want
			if regis == obj.regis:
				obj.token_auth()
				image_obj.header = obj.header
				break

		image_obj.get_image_tag_count(regis)

		if (image_obj.num_tags > 100):
			"""since we use a iterator to store tag name along with data,
				if there is more than 100 tags than no data is stored. we
				only need 1 container to get arch, we still get all the
				data we want"""
			logging.warning('more than 100 tags. Querying several pages')
			image_obj.get_alot_image_tag_names(regis)
			#this function also gets arch for the image.
			logging.warning('no data stored in image_obj')
			# we can only get 100 tag names per page

		if(image_obj.num_tags < 99 and image_obj.num_tags > 0):
			# also gets arch for the image.
			image_obj.get_image_tag_names(regis)

		if image_obj.container in image_obj.tags:
			image_obj.is_container = True
			#now the container is part of image_obj
			image_obj.get_archs(regis, image_obj.container)

		app_obj.sub_images.append(image_obj)
		#From here, all the vars are set for the output.

	print_obj(app_obj)

	f = open("results-TESTSKI.csv", "a+")
	f.write("App,amd64,ppc64le,s390x,Images,Container,amd64,ppc64le,s390x,Tag Exists?\n")
	output_CSV(app_obj, f) # After creating a list of all the subimages in mainImage, output it
	f.close() #close csv file

	print("\n Please see:\n \t cat results-TESTSKI.csv \n")
	sys.exit()
