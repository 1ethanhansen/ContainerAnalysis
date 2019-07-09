# The Container Analysis Project
An application to gather information about images and containers on DockerHub and output this helpful info into a CSV file.  
[![Build Status](https://travis-ci.org/EthanHans3n/ContainerAnalysis.svg?branch=master)](https://travis-ci.org/EthanHans3n/ContainerAnalysis)

## NOTE: currently only supports dockerhub repository
 
# How to Run it

Tested with Python 2.7

```bash
pip install -r requirements.txt
python get-image-info.py 
```
After execution is complete, you can view the [results.csv](https://github.com/mtarsel/ContainerAnalysis/blob/master/docs/results.pdf) file

A new directory called Applications/ will exist with more info about the Applications and Images.

Please note this script may not print out every result... or correctly. values.yaml are specific to each Application and so they are all written differently.

# Specify Logging

By default, WARNING level logging is enabled. Otherwise run:

```bash
python get-image-info.py --help
```

Output is saved to a file called container-output.log in same directory as [get-image-info.py](./get-image-info.py). 


# How To Gather Info on dockerhub.com

Utilizing DockerHub v2 API this will send an HTTP request to a registry like hub.docker.com and
receive a JSON file in return. Read about it [here.](https://docs.docker.com/registry/spec/api/)

This example has no tags for an image
https://hub.docker.com/v2/repositories/ppc64le/couchdb/tags/?page_size=100

This example has 1 tag for an image
https://hub.docker.com/v2/repositories/ppc64le/elk/tags/?page_size=100

This example is the most detailed information we can get for a specific image
tag
https://hub.docker.com/v2/repositories/ppc64le/ibmjava/tags/sdk/

# Contributing

[Read the guide here.](https://github.com/mtarsel/ContainerAnalysis/blob/master/docs/CONTRIBUTING.md)

# License
The Container Analysis Project uses the [Apache License Version 2.0](https://github.com/mtarsel/ContainerAnalysis/blob/master/docs/LICENSE) software license.
