import requests
import json
import base64

class Hub:
	"""An object to connect to dockerhub. Does not store username or password.
	Any user information will be entered at execution.
	"""
	def __init__(self, regis, uname, upass):
		self.regis = regis
		self.uname = uname
		self.upass = base64.b64decode(upass)
		#self.org = org
		self.org_list = ['ppc64le','ibmcom']
		self.header = ''

	def token_auth(self):
		# obtain token
		r = requests.post('https://' + self.regis + '/v2/users/login/',
			json={"username":self.uname, "password":self.upass})

		r.raise_for_status()
		token = json.loads(r.text)["token"]

		# create special packet header with JWT and token
		self.header = {'Authorization': 'JWT ' + token }
