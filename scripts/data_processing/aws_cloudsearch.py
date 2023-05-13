'''
Prepare and upload seminar data to Amazon Cloudsearch
'''

import os,sys,json,boto3,re,datetime,pytz
from dateutil.parser import parse
from pprint import pprint

from pathlib import Path

def fields_to_text_string(seminar_data):
	seminar_title=seminar_data['seminar_title']
	seminar_abstract=seminar_data['seminar_abstract']
	topic_tags=', '.join(seminar_data['topic_tags'])
	series=seminar_data['hosted_by']
	seminar_speaker=seminar_data['seminar_speaker']
	speaker_affil=seminar_data['speaker_affil']
	speaker_twitter=seminar_data['speaker_twitter']
	text_string='{} {} {} {} {} {}'.format(seminar_title,seminar_abstract,topic_tags,series,seminar_speaker,speaker_affil,speaker_twitter)
	return text_string

def strip_all_quotes(text_string):

	### " " ### ' ' ### “ ” ### ‘ ’ ### « » ### „ “ ### » « ###  

	text_string=text_string.replace('"','')
	text_string=text_string.replace("'",'')
	text_string=text_string.replace('“','')
	text_string=text_string.replace('”','')
	text_string=text_string.replace('’','')
	text_string=text_string.replace('‘','')
	text_string=text_string.replace('«','')
	text_string=text_string.replace('»','')
	text_string=text_string.replace('„','')

	return text_string

def multiple_whitespaces_to_single_space(text_string):
	text_string = re.sub(r'\s+', ' ', text_string)
	return text_string

def char_validation(text_string):

	'''
	Both JSON and XML batches can only contain UTF-8 characters that are valid in XML. Valid characters are the control characters tab (0009), carriage return (000D), and line feed (000A), and the legal characters of Unicode and ISO/IEC 10646. FFFE, FFFF, and the surrogate blocks D800–DBFF and DC00–DFFF are invalid and will cause errors. (For more information, see Extensible Markup Language (XML) 1.0 (Fifth Edition).) You can use the following regular expression to match invalid characters so you can remove them: /[^\u0009\u000a\u000d\u0020-\uD7FF\uE000-\uFFFD]/ .

	When formatting your data in JSON, quotes (") and backslashes (\) within field values must be escaped with a backslash.
	'''

	# remove invalid characters
	text_string = re.sub(r'[^\u0009\u000a\u000d\u0020-\uD7FF\uE000-\uFFFD]', '', text_string)

	# escape quotes and backslashes
	text_string = re.sub(r'(["\\])', r'\\\1', text_string)

	return text_string

def get_unique_ids_from_text_data(text_data):
	unique_ids=[]
	for item in text_data:
		unique_ids.append(item['id'])
	return unique_ids

def parse_seminar_date_time_tz(seminar_data):

	seminar_date=seminar_data['seminar_date']
	seminar_time=seminar_data['seminar_time']
	seminar_timezone=seminar_data['timezone']

	seminar_timezone=pytz.timezone(seminar_timezone)
	seminar_datetime=parse(seminar_date + ' ' + seminar_time, fuzzy=True)
	seminar_datetime = seminar_timezone.localize(seminar_datetime).astimezone(pytz.UTC)

	# Dates and times are specified in UTC (Coordinated Universal Time) according to IETF RFC3339: yyyy-mm-ddTHH:mm:ss.SSSZ.
	
	seminar_datetime=seminar_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
	
	return seminar_datetime

cloudsearch_domain_name='world-wide'

working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'
python_scripts_dir=working_dir + 'python_scripts/'

# download the search index data from amazon in a json file
cloudsearch_domain_endpoint='doc-{}-qh6t3a5hkir3zr5po7la6otfza.eu-west-1.cloudsearch.amazonaws.com'.format(cloudsearch_domain_name)
cloudsearch_domain_region='us-west-1'
cloudsearch_domain_endpoint_url='https://{}'.format(cloudsearch_domain_endpoint)

cloudsearch_text_data_request='curl -X GET {}/2013-01-01/documents/search?q=* --header "Content-Type:application/json"'.format(cloudsearch_domain_endpoint_url)
#print(cloudsearch_text_data_request)
cloudsearch_text_data_json=os.popen(cloudsearch_text_data_request).read()

#pprint(cloudsearch_text_data_json)

try:
	with open(working_dir+'python_scripts/cloudsearch_text_data.json','r') as json_file:
		old_cloudsearch_text_data = json.load(json_file)
except:
	print('Error reading text data file. Perhaps, cloudsearch_text_data.json does not exist?')
	old_cloudsearch_text_data=[]

already_existing_ids=get_unique_ids_from_text_data(old_cloudsearch_text_data)

with open(working_dir+'seminar_data.json','r') as json_file:
	seminars = json.load(json_file)

seminar_fields=['seminar_speaker','seminar_abstract','seminar_title','speaker_affil','topic_tags','speaker_twitter']

new_cloudsearch_text_data=[]

seminar_ids_to_be_deleted=[k for k in already_existing_ids if k not in seminars.keys()]
#seminar_ids_to_be_deleted=[str(i) for i in range(1,10000)]
for unique_id in seminar_ids_to_be_deleted:
	search_dict_item={'type':'delete','id':unique_id}
	new_cloudsearch_text_data.append(search_dict_item)

for k,v in seminars.items():
	unique_id=k

	if unique_id not in already_existing_ids or True:
		
		seminar_data=v

		text_string=fields_to_text_string(seminar_data)
		text_string=strip_all_quotes(text_string)
		text_string=multiple_whitespaces_to_single_space(text_string)
		text_string=char_validation(text_string)
		
		item_type=seminar_data['item_type']
		seminar_datetime=parse_seminar_date_time_tz(seminar_data)

		domains=seminar_data['domains']
		series=seminar_data['hosted_by']

		topics=seminar_data['topic_tags']

		try:
			if len(seminar_data['video_on_demand'])>5:
				video_on_demand=1
			else:
				video_on_demand=0
		except:
			video_on_demand=0

		# if topics is an empty list, then don't add it to the search index
		if len(topics)==0:
			topics=None

		if topics!=None:
			search_dict_item={
					'type':'add',
					'id':unique_id,
					'fields':{
								'text':text_string,
								'item_type':item_type,
								'date':seminar_datetime,
								'domains':domains,
								'series':series,
								'topics':topics,
								'video_on_demand':video_on_demand
							}
				}
		else:
			search_dict_item={
					'type':'add',
					'id':unique_id,
					'fields':{
								'text':text_string,
								'item_type':item_type,
								'date':seminar_datetime,
								'domains':domains,
								'series':series,
								'video_on_demand':video_on_demand
							}
				}
		
		new_cloudsearch_text_data.append(search_dict_item)

print(len(new_cloudsearch_text_data))

#pprint(new_cloudsearch_text_data)
#with open(working_dir+'python_scripts/tmp.json','w') as json_file:
#	json.dump(new_cloudsearch_text_data,json_file)

#sys.exit()

# UPLOAD TEXT DATA TO CLOUDSEARCH

with open(working_dir+'python_scripts/cloudsearch_text_data.json','w') as json_file:
	json.dump(new_cloudsearch_text_data,json_file)

cloudsearch_domain_endpoint='doc-{}-qh6t3a5hkir3zr5po7la6otfza.eu-west-1.cloudsearch.amazonaws.com'.format(cloudsearch_domain_name)
cloudsearch_domain_region='us-west-1'
cloudsearch_domain_endpoint_url='https://{}'.format(cloudsearch_domain_endpoint)

# CURL COMMAND
#curl -X POST --upload-file movie-data-2013.json doc-movies-123456789012.us-east-1.cloudsearch.amazonaws.com/2013-01-01/documents/batch --header "Content-Type:application/json"

curl_command='curl -X POST --upload-file {}cloudsearch_text_data.json {}/2013-01-01/documents/batch --header "Content-Type:application/json"'.format(python_scripts_dir,cloudsearch_domain_endpoint_url)
print('I just ran aws_cloudsearch.py')
print(curl_command)
os.system(curl_command)
