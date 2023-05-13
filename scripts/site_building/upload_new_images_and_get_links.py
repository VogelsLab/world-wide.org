'''
Write a script that when it runs it detects new image files saved in a folder and uploads them to AWS S3. Then it appends the image links to 'S3_image_urls.txt'
Afterwards, update the Google Sheet 'Image Links' by putting S3_image_urls.txt list in the first column
'''

import os,sys

from pprint import pprint
from pathlib import Path

working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'
scripts_dir=working_dir+'python_scripts/'

# Check already uploaded images by opening S3_image_urls.txt and parsing the basenames
url_basenames = []
with open(scripts_dir+'S3_image_urls.txt', 'r') as f:
	for line in f:
		url_basenames.append(line.split('/')[-1].strip())

working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'
working_dir_python_code=str(Path.home()) + '/Dropbox/websites/world-wide.org/python_scripts/'

# Get the list of files in the folder
files = os.listdir(working_dir+'images')

# Upload new images to S3 and append the urls to S3_image_urls.txt
for file in files:
	if file not in url_basenames:
		os.system('/usr/local/bin/aws s3 cp ' + working_dir +'images/' + file + ' s3://www.world-wide.org/images/')
		with open(scripts_dir+'S3_image_urls.txt', 'a') as f:
			f.write('https://www.world-wide.org/images/' + file + '\n')

sys.exit()

# Update Google Sheet 'Image Links' with the S3_image_urls.txt list
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
			'https://spreadsheets.google.com/feeds',
			'https://www.googleapis.com/auth/drive'
		]

credentials = ServiceAccountCredentials.from_json_keyfile_name(working_dir_python_code+'imposing-timer-196815-245fab6211ac.json', scope)
gc = gspread.authorize(credentials)

gsheet_id='1DHjajTp-xkN0YPOxeu3UV89_zFvw1Ic3UXCCuHZ2G7g'
gc = gspread.authorize(credentials)
spreadsheet = gc.open_by_key(gsheet_id)
wks=spreadsheet.worksheet('Image URLs')

# Get the list of image links from S3_image_urls.txt
with open('S3_image_urls.txt', 'r') as f:
	S3_image_urls = list(reversed(f.read().splitlines()))

# Update the Google Sheet 'Image Links'
for i in range(len(S3_image_urls)):
	wks.update_cell(i+1, 1, S3_image_urls[i])