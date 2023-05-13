import os,sys,re,pickle,json,time,shutil,boto3
from pprint import pprint
from pathlib import Path

ww_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'
scripts_dir=ww_dir+'python_scripts/'
html_templates_dir=scripts_dir+'html_templates/'
seminar_pages_dir=ww_dir+'seminar/'

# load the seminar_data.json file
with open(ww_dir+'seminar_data.json','r') as json_file:
	seminar_data=json.load(json_file)

# load the template seminar page html
with open(html_templates_dir+'seminar_page.html','r') as f:
	seminar_template=f.read()

new_body_string=seminar_template.split('</head>')[1] # split always splits on the first instance of the string


# the keys of the seminar_data dictionary are the active seminar listings
seminar_keys=list(seminar_data.keys())

# let's loop through them and update the html files
for seminar_key in seminar_keys:

	# let's load the html page
	seminar_page_dir=ww_dir+'seminar/'+seminar_key+'/'
	with open(seminar_page_dir+'index.html','r') as html_file:
		html_string=html_file.read()

	old_head_string=html_string.split('</head>')[0]
	new_html_string=old_head_string + '</head>' + new_body_string

	# let's write the new html file
	print(seminar_page_dir+'index.html')
	with open(seminar_page_dir+'index.html','w') as html_file:
		html_file.write(new_html_string)
	
	# upload the new html file to s3
	# let's refactor this os.system('/usr/local/bin/aws s3 cp ' + working_dir + 'seminar_series_data.json s3://www.world-wide.org')
	cmd='/usr/local/bin/aws s3 cp ' + seminar_page_dir + 'index.html s3://www.world-wide.org/seminar/' + seminar_key + '/'
	os.system(cmd)