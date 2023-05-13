import os,sys,re,pickle,json,shutil
from unidecode import unidecode
from dateutil.parser import parse
from pprint import pprint
from pathlib import Path

def meta_name_description(content,x):
	return re.sub(r'<meta name="description" content=".*?">','<meta name="description" content="World Wide '+x+'">',content,flags=re.DOTALL)

def page_title(content,x):
	return re.sub(r'<title>World Wide .*?</title>','<title>World Wide '+x+'</title>',content,flags=re.DOTALL)

def open_graph_title(content,x):
	content=re.sub(r'<meta name="twitter:title" content=".*?">','<meta name="twitter:title" content="World Wide | '+x+'">',content)
	return re.sub(r'<meta property="og:title" content=".*?">','<meta property="og:title" content="World Wide | '+x+'">',content)

def open_graph_title_for_series(content,x):
	content=re.sub(r'<meta name="twitter:title" content=".*?">','<meta name="twitter:title" content="'+x+'">',content)
	return re.sub(r'<meta property="og:title" content=".*?">','<meta property="og:title" content="'+x+'">',content)

def open_graph_image_card(content,x):
	content=re.sub(r'<meta name="twitter:image" content=".*?">','<meta name="twitter:image" content="'+x+'">',content)
	return re.sub(r'<meta property="og:image" content=".*?">','<meta property="og:image" content="'+x+'">',content)

def open_graph_url(content,x):
	return re.sub(r'<meta property="og:url" content=".*?">','<meta property="og:url" content="https://www.world-wide.org/'+x+'/index.html">',content)

def open_graph_description(content,x):
	return re.sub(r'<meta property="og:description" content=".*?">','<meta property="og:description" content="Discover and attend scientific events or advertise your own 🔆">',content)

def open_graph_description_for_series(content,series_name,domain_nickname):
	return re.sub(r'<meta property="og:description" content=".*?">','<meta property="og:description" content="Discover and attend scientific events organized by ' + series_name + ' on World Wide ' +  domain_nickname + ' 🔆">',content)

def make_the_necessary_substitutions_to_the_domain_template(about_this_domain,head_domain_page_template):

	domain_name=about_this_domain['domain_name']
	domain_nickname=about_this_domain['domain_nickname']
	domain_alias=about_this_domain['domain_alias']

	try:
		domain_banner=about_this_domain['banner_image']
		if domain_banner=='':
			domain_banner='https://www.world-wide.org/banner.jpg'
	except:
		domain_banner='https://www.world-wide.org/banner.jpg'
	
	head_domain_page_template=meta_name_description(head_domain_page_template,domain_name)
	head_domain_page_template=open_graph_title(head_domain_page_template,domain_name)
	head_domain_page_template=page_title(head_domain_page_template,domain_nickname)
	head_domain_page_template=open_graph_description(head_domain_page_template,domain_name)

	head_domain_page_template=open_graph_image_card(head_domain_page_template,domain_banner)
	head_domain_page_template=open_graph_url(head_domain_page_template,domain_alias)
	
	return head_domain_page_template

def make_the_necessary_substitutions_to_the_series_template(about_this_domain,about_this_series,head_series_page_template):

	domain_name=about_this_domain['domain_name']
	domain_nickname=about_this_domain['domain_nickname']
	domain_alias=about_this_domain['domain_alias']

	series_name=about_this_series['Series Name']
	series_alias=about_this_series['series_alias']
	
	try:
		series_banner=about_this_series['Banner Image']
		if series_banner=='':
			meta_cards_dir=domain_directory+'/meta_cards/'
			meta_cards=[x for x in os.listdir(meta_cards_dir) if x[0]!='.']
			series_banner=random.choice(meta_cards)
	except:
		series_banner='https://www.world-wide.org/banner.jpg'
	
	head_series_page_template=meta_name_description(head_series_page_template,domain_name)
	head_series_page_template=open_graph_title_for_series(head_series_page_template,series_name)
	head_series_page_template=page_title(head_series_page_template,domain_nickname)
	head_series_page_template=open_graph_description_for_series(head_series_page_template,series_name,domain_nickname)

	head_series_page_template=open_graph_image_card(head_series_page_template,series_banner)
	head_series_page_template=open_graph_url(head_series_page_template,domain_alias)

	return head_series_page_template

def if_html_file_is_not_the_same_or_doesnt_exist(html_fname_copy,html_source):
	try:
		with open(html_fname_copy,'r') as f:
			html_copy=f.read()

		if html_copy!=html_source:
			return True
		else:
			return False
	except:
		return True

working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'
working_dir_python_code=str(Path.home()) + '/Dropbox/websites/world-wide.org/python_scripts/'

with open(working_dir+'/python_scripts/html_templates/domain_page.html','r') as f:
	domain_page_template = f.read()

with open(working_dir+'/python_scripts/html_templates/domain_upcoming_page.html','r') as f:
	domain_upcoming_page_template = f.read()

with open(working_dir+'/python_scripts/html_templates/domain_archive_page.html','r') as f:
	domain_archive_page_template = f.read()

with open(working_dir+'/python_scripts/html_templates/series_page.html','r') as f:
	series_page_template = f.read()

with open(working_dir+'/python_scripts/html_templates/topic_page.html','r') as f:
	topic_page_template = f.read()

with open(working_dir+'world_wide_domains.json') as json_file:
	world_wide_domains = json.load(json_file)

for domain in world_wide_domains:

	domain_alias=world_wide_domains[domain]['domain_alias']

	domain_directory=working_dir + domain_alias
	aws_s3_domain_directory= 's3://www.world-wide.org/' + domain_alias

	head_domain_page_template=make_the_necessary_substitutions_to_the_domain_template(world_wide_domains[domain],domain_page_template)
	head_domain_upcoming_page_template=make_the_necessary_substitutions_to_the_domain_template(world_wide_domains[domain],domain_upcoming_page_template)
	head_domain_archive_page_template=make_the_necessary_substitutions_to_the_domain_template(world_wide_domains[domain],domain_archive_page_template)

	if if_html_file_is_not_the_same_or_doesnt_exist(domain_directory+'/index.html',head_domain_page_template):
		with open(domain_directory+'/index.html','w') as f:
			f.write(head_domain_page_template)
		os.system('/usr/local/bin/aws s3 cp ' + domain_directory+'/index.html ' + aws_s3_domain_directory + '/index.html')

	if if_html_file_is_not_the_same_or_doesnt_exist(domain_directory+'/upcoming/index.html',head_domain_upcoming_page_template):
		with open(domain_directory+'/upcoming/index.html','w') as f:
			f.write(head_domain_upcoming_page_template)
		os.system('/usr/local/bin/aws s3 cp ' + domain_directory+'/upcoming/index.html ' + aws_s3_domain_directory + '/upcoming/index.html')


	if if_html_file_is_not_the_same_or_doesnt_exist(domain_directory+'/archive/index.html',head_domain_archive_page_template):
		with open(domain_directory+'/archive/index.html','w') as f:
			f.write(head_domain_archive_page_template)
		os.system('/usr/local/bin/aws s3 cp ' + domain_directory+'/archive/index.html ' + aws_s3_domain_directory + '/archive/index.html')
	
	with open(working_dir+domain_alias+'/seminar_series_data.json','r') as json_file:
		seminar_series_data = json.load(json_file)

	try:
		with open(working_dir+domain_alias+'/topic_aliases.json','r') as json_file:
			topic_aliases = json.load(json_file)
	except:
		topic_aliases=dict()

	for series in seminar_series_data:

		series_alias=series.replace(' ','-')
		series_alias=series_alias.replace('&','and')

		series_directory=working_dir + domain_alias + '/' + series_alias
		aws_s3_series_directory= 's3://www.world-wide.org/' + domain_alias + '/' + series_alias

		with open(series_directory+'/about_this_series.json','r') as json_file:
			about_this_series = json.load(json_file)

		if not os.path.exists(series_directory):
			continue

		head_series_page_template=make_the_necessary_substitutions_to_the_series_template(world_wide_domains[domain],about_this_series,series_page_template)

		if if_html_file_is_not_the_same_or_doesnt_exist(series_directory+'/index.html',head_series_page_template):
			with open(series_directory+'/index.html','w') as f:
				f.write(head_series_page_template)
			os.system('/usr/local/bin/aws s3 cp ' + series_directory+'/index.html ' + aws_s3_series_directory + '/index.html')
	
	try:
		with open(working_dir+domain_alias+'/topic_tags_with_pages.json','r') as json_file:
			topic_tags_with_pages = json.load(json_file)

		for x in topic_tags_with_pages:

			if x in topic_aliases:
				topic_tag_alias=topic_aliases[x]
			else:
				topic_tag_alias=x

			topic_tag_directory=working_dir + domain_alias + '/topic/' + topic_tag_alias
			aws_s3_topic_tag_directory= 's3://www.world-wide.org/' + domain_alias + '/topic/' + topic_tag_alias

			if if_html_file_is_not_the_same_or_doesnt_exist(topic_tag_directory+'/index.html',topic_page_template):
				shutil.copy(working_dir_python_code+'html_templates/topic_page.html',topic_tag_directory+'/index.html')
				os.system('/usr/local/bin/aws s3 cp ' + working_dir_python_code+'html_templates/topic_page.html ' + aws_s3_topic_tag_directory + '/index.html')
	except:
		pass		
