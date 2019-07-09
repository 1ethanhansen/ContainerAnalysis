from setuptools import setup
from setuptools import find_packages

setup(name='ContainerAnalysis',
      version='0.1',
      description='An application to query different registries and repos to run analytics on Docker Containers.',
      author='Ethan Hansen & Mick Tarsel',
      packages=find_packages(),
      zip_safe=False)
