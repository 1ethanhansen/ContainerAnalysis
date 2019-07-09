import requests
import json
import logging

from utils.crawler import find_image
from utils.crawler import get_repo_pages

class App:
	"""This is the App Name but easier to use mainimage, subimage for documentation
	These attributes will be from values.yaml (from a tgz)which is derived from
	the big index.yaml file. Keywords are taken from Chart.yaml which is not saved anywhere.
	"""
	def __init__(self, name, url):
		self.name = name
		self.url = url #location of the tarball 
		self.num_supported_images = ''
		self.sub_images_supported = [ ]#should be same length as keys[1] from yaml
		self.sub_images = [ ] #all the images for Main image. for output_CSV()
		
		self.keywords = [ ]
		self.repos = [ ] #not parsed
		self.tags = [ ]
		self.images = [ ]
		self.clean_repos = [ ] #sanitized
		self.values_exists = False
		self.Charts_exists = False
		self.is_bad = False # something did't parse correctly so its causing problems


	def add_keyword(self, keyword):
		self.keywords.append(keyword)

	def verify(self):
		"""iterate thru an App's sub images to make sure we have all the info we need.
		if something doesn't seem right, let it be known"""

		if len(self.tags) == 0:
			self.is_bad = True

		if len(self.images) == 0:
			self.is_bad = True

		#if images != tags, just use first tag
		#if len(self.images) != len(self.tags) or len(self.repos) != len(self.images):
		if len(self.repos) != len(self.images):
			self.is_bad = True

		for image_obj in self.sub_images:
			if image_obj.name is None or image_obj.name == "":
				print("gotcha in verify()")
			#iterate thru images in app and set the app.is_bad var based on image info		
			if image_obj.exist_in_repo == False:
		 		self.is_bad = True

class Image:
	""" This is the object containing all the information we care about.
		Eventually all the attributes will contain everything we need

		The info we will need to query dockerhub will be from values.yaml, the
		rest of these attributes will be from hub.docker.com
	"""
	def __init__(self, name, org, container):
		self.name = name
		self.org = org # also called repository or repo
		self.container = container #the container we care about for this image
		self.num_archs = ''
		self.num_tags = ''
		self.is_multiarch = False
		self.is_ppc64le = False
		self.is_amd64 = False
		self.is_s390x = False
		self.archs = [ ]
		self.tags = [ ] # now tag[1] and data[1] give all the info
		self.data = [ ]
		self.header = ''
		self.is_container = False#if container is in tags -regex * works
		self.exist_in_repo = True #if it doesnt exist, big problem!

	def add_tag(self, tag_name):
		self.tags.append(tag_name)

	def add_data(self, new_data):
		self.data.append(new_data)

	def add_arch(self, arch_name):
		self.archs.append(arch_name)

	#TODO: img
	def get_image_tag_count(self, regis):
		image_url = ('https://' + regis + '/v2/repositories/' + self.org + '/'+
					self.name +'/tags/?page=1&page_size=100')
		r = requests.get(image_url, headers=self.header)

		logging.debug('%s %s %s', self.name, self.org, image_url)

		if r.status_code == 404:
			logging.critical('image: %s does not exist in %s organization',
							self.name, self.org)
			logging.critical(image_url)
			#TODO find_image(self, regis)# image is not in this org. big problem!!!
			self.is_container = False
			self.is_multiarch = False
			self.is_ppc64le = False
			self.num_tags = 0
			self.exist_in_repo = False
			return self.num_tags

		r.raise_for_status()

		# turns the reply into JSON containing dict of strings
		data = json.loads(r.text)

		self.num_tags = int(data["count"])

		logging.info('image: %s Tags=%d organization=%s', 
			self.name, self.num_tags, self.org)

		return self.num_tags

	def get_alot_image_tag_names(self, regis):
		"""more than 100 tagsif there is more than 1 pages than we have to
			iterate thru all page_size
			since there is only 100 images per page"""
		image_pages = get_repo_pages(int(self.num_tags))#number of pages to query

		for i in range(1,image_pages+1):
			image_url = ('https://' + regis + '/v2/repositories/' + self.org +
						'/'+ self.name +'/tags/?page='+ str(i) +'&page_size=100')
			logging.debug('Trying %s', image_url)
			r = requests.get(image_url, headers=self.header)
			r.raise_for_status()
			data = json.loads(r.text)

			if i == image_pages:	# we have 100 images EXCEPT on last page.
				tag_extra = int(self.num_tags % 100) # gotta do this again
				for j in range(tag_extra):
					tag_name = data["results"][j]["name"]
					self.add_tag(tag_name)
					 #TODO self.get_image_tag(regis, header, j)
				break # last page so no more repos.

			for j in range(100): # we have 100 images 4 this repo on this page
				tag_name = data["results"][j]["name"]
				self.add_tag(tag_name)
				#TODO self.get_image_tag(regis, header, j)

	def get_image_tag_names(self, regis):
		""" Gets the name of the tags for an image. use tag name to request
			more specific info

			Also set arch values
		"""
		image_url = ('https://' + regis + '/v2/repositories/' + self.org + '/'+
						self.name +'/tags/?page=1&page_size=100')
		logging.debug('get_image_tag_names: %s', image_url)
		r = requests.get(image_url, headers=self.header)
		r.raise_for_status()

		data = json.loads(r.text)

		if (self.num_tags == 0): # double check to avoid failure
			logging.critical('There is no tags for %s', self.name)

		for i in range(self.num_tags):
			tag_name = data["results"][i]["name"]
			self.add_tag(tag_name)
			self.get_image_tag(regis, i)
			logging.info('get_image_tag_names: image name: %s tag: %s', self.name, self.tags[i])

	def get_archs(self, regis, image_tag_name):
		"""determine if specific image tag is multiarch.
		iterate over all the archs and add them to the objects list of
		archs

		Also check if ppc64le is in the list of archs."""

		tag_url = ('https://' + regis + '/v2/repositories/' + self.org + '/'+
					self.name +'/tags/'+ image_tag_name + '/')
		r = requests.get(tag_url, headers=self.header)
		r.raise_for_status()

		data = json.loads(r.text)
		self.num_archs = len(data["images"])
				
		if self.num_archs == 1: #i have one arch so ill take it and quit
			self.is_multiarch = False
			self.add_arch(data["images"][0]["architecture"])
		else:
			self.is_multiarch = True
			for arch_name in range(self.num_archs):
				""" give me the rest of the archs. IT MUST BE MULTIARCH """
				self.add_arch(data["images"][arch_name]["architecture"])
		
				if 'ppc64le' in self.archs:
					self.is_ppc64le = True
				if 'amd64' in self.archs:
					self.is_amd64 = True
				if 's390x' in self.archs:
					self.is_s390x = True

	def get_image_tag(self, regis, itr):
		"""Get the image tag info. the request page contains all the info we
			can get about a specific tag for an image.

			Get the number of architectures here because that is specific image
			tag info.

			Add arch num and arch names to object.
		"""
		tag_url = ('https://' + regis + '/v2/repositories/' + self.org + '/'+
					self.name +'/tags/'+ self.tags[itr] + '/')
		logging.debug('get_image_tag: %s tag:%s %s',
						self.name, self.tags[itr], tag_url)
		r = requests.get(tag_url, headers=self.header)
		r.raise_for_status()

		#this list of data contains ALL the info about each tag on 1 webpage.
		self.add_data(json.loads(r.text))
		logging.debug('get_image_tag: tag name:%s  %s', self.tags[itr], self.data[itr])
		#print(pp_json(data))

# class imageTag:
# 	#imageTagLatest:
# 	"""An object for a specific image tag. Eventually this will contain the
# 	'latest' tag.
# 	 This is benefical because there is a list of architectures and nicely
# 	 stores in the info stored in the image object data attribute"""
# 	name
# 	num_archs
# 	archs =
# 	size =
# 	last_updated
