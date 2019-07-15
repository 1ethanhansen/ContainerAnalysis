#!/bin/bash

#test different args to get-image-info
python get-image-info.py user.yaml
python get-image-info.py user.yaml --debug

#gets number of columns in results.csv
#head -l outputs the first row of the file
#sed removes everything expect commas
#wc -c gives the character count (includes \n)
if [ $(head -1 results.csv | sed 's/[^,]//g' | wc -c) != 11 ]; then
echo "Wrong number of columns in results";
exit 1;	#travis build should fail if it get the wrong number of columns
fi
