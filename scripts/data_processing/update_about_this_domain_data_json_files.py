import os,sys,re,pickle,json,datetime,pytz,tweepy
from unidecode import unidecode
from dateutil.parser import parse
from pprint import pprint
from pathlib import Path

def if_json_file_is_not_the_same_or_doesnt_exist(json_fname,new_json_data):
	try:
		with open(json_fname,'r') as f:
			old_json_data=json.load(f)

		if new_json_data!=old_json_data:
			return True
		else:
			return False
	except:
		return True

working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'

with open(working_dir+'world_wide_domains.json', 'r') as f:
	domains_data=json.load(f)

old_domains_data=domains_data

#domains_data['Physics of Life']['banner_image']

'''if domains_data!=old_domains_data:
	print(1)
	pass
else:
	print(2)
	sys.exit()'''

#if if_json_file_is_not_the_same_or_doesnt_exist(working_dir+'world_wide_domains.json',domains_data):

with open(working_dir+'world_wide_domains.json', 'w') as f:
	json.dump(domains_data,f)

os.system('/usr/local/bin/aws s3 cp ' + working_dir + 'world_wide_domains.json s3://www.world-wide.org')

for domain in domains_data:

	domain_dir=working_dir+domains_data[domain]['domain_alias']+'/'

	dir_list=['','upcoming','archive']

	for subdir in dir_list:
		if not os.path.exists(domain_dir+subdir):
			os.makedirs(domain_dir+subdir)

	if if_json_file_is_not_the_same_or_doesnt_exist(domain_dir+'about_this_domain.json',domains_data[domain]):
		
		with open(domain_dir+'about_this_domain.json', 'w') as f:
			json.dump(domains_data[domain],f)
		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'about_this_domain.json s3://www.world-wide.org/'+domains_data[domain]['domain_alias']+'/about_this_domain.json')

	if if_json_file_is_not_the_same_or_doesnt_exist(domain_dir+'upcoming/about_this_domain.json',domains_data[domain]):
		
		with open(domain_dir+'upcoming/about_this_domain.json', 'w') as f:
			json.dump(domains_data[domain],f)
		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'upcoming/about_this_domain.json s3://www.world-wide.org/'+domains_data[domain]['domain_alias']+'/upcoming/about_this_domain.json')

	if if_json_file_is_not_the_same_or_doesnt_exist(domain_dir+'archive/about_this_domain.json',domains_data[domain]):
		
		with open(domain_dir+'archive/about_this_domain.json', 'w') as f:
			json.dump(domains_data[domain],f)
		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'archive/about_this_domain.json s3://www.world-wide.org/'+domains_data[domain]['domain_alias']+'/archive/about_this_domain.json')