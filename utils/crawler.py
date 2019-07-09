import requests
import json
import logging

def find_image(self, regis)
	"""Pretty much the same as get_images_from_repo() but finds a specific
	image"""
	logging.warning('Searching for %s now...', self.name)
	if(self.org == 'ppc64le'):
		self.org = 'ibmcom'
	else:
		self.org = 'ppc64le'

	repo_count = get_repo_count(regis, self.org, self.header)#num of repos per org
	repo_pages = get_repo_pages(repo_count)#number of pages to query

	for i in range(1,repo_pages+1):
		repo_url = ('https://' + regis + '/v2/repositories/' + self.org +
					'/?page='+ str(i) +'&page_size=100')
		logging.debug('Trying %s', repo_url)
		r = requests.get(repo_url, headers=self.header)
		r.raise_for_status()
		data = json.loads(r.text)

		if i == repo_pages:	# we have 100 images EXCEPT on last page.
			repo_extra = int(repo_count % 100) # gotta do this again
			for j in range(repo_extra):
				image_name = data["results"][j]["name"]
				if (image_name == self.name):
					logging.debug('Successfully found %s in %s',
									self.name, self.org)
					self.get_image_tag_count(regis, header)
			break # last page so no more repos.

		for j in range(100): # we have 100 images 4 this repo on this page
			image_name = data["results"][j]["name"]
			if (image_name == self.name):
				logging.debug('Successfully found %s in %s',
								self.name, self.org)
				self.get_image_tag_count(regis, header)

def get_repo_count(regis, org, header):
	"""repos exist in organizations iterate over organization list and get 100
		repos per page
	"""
	url = ('https://' + regis + '/v2/repositories/' + org
			+ '/?page=1&page_size=100')

	r = requests.get(url, headers=header)  # go get the repositories
	r.raise_for_status()

	data = json.loads(r.text) # turns the reply into JSON, a dict of strings

	repo_count = int(data["count"]) # get count of repos in an organization
	return repo_count

def get_repo_pages(repo_count):
	""" We are limited to get only 100 entries per page. This func does some
		simple math to get the number of pages to query incase we cannot find
		an image
	"""
	if repo_count <= 100:
		logging.critical('get_repo_pages(): only 1 page of repos (less than 100 repos)')
		sys.exit()

	repo_pages = int(repo_count / 100) # how many pages to query?
	repo_extra = int(repo_count % 100) # how many repos left on last page?

	if (repo_extra > 0): # if we have 200 images exactly, we dont get 3 pages
		repo_pages += 1
	return repo_pages

#NEVER CALLED. unless we want to call queryHub() and get it all.
def get_images_from_repo(repo_pages, repo_count, regis, org, header):
	#range(start,end,step) so from page=1 to page=repo_pages+1 cause python range starts at 0 -> n-1
	for i in range(1,repo_pages+1):
		repo_url = 'https://' + regis + '/v2/repositories/' + org + '/?page='+ str(i) +'&page_size=100'
		print(repo_url)
		r = requests.get(repo_url, headers=header)
		#checkStatusCode(r, repo_url)
		data = json.loads(r.text)

		#problem is we have 100 images EXCEPT on last page.
		if i == repo_pages:
			repo_extra = int(repo_count % 100) #gotta do this again to avoid another var in func call
			for j in range(repo_extra):
				image_name = data["results"][j]["name"]
				print(j, image_name)
			break #last page so no more repos.

		#otherwise we have 100 images on this page for repo
		for j in range(100):
			image_name = data["results"][j]["name"]
			print("(dockerhub, %s, %s)"% (org, image_name))

#NEVER CALLED. can be used in the future as a crawler.gets all images in the list of organizations
def queryHub():
	hub = HubObj()

	hub.tokenAuth()

	for org in hub.org_list:
		num_repos = getRepoCount(hub.regis, org, hub.header)#num of repos per org
		pages = getRepoPages(num_repos)#number of pages to query
		getImagesFromRepo(pages, num_repos, hub.regis, org, hub.header)
