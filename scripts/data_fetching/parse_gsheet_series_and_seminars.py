import os,sys,re,gspread,pickle,json,datetime,uuid,pytz,hashlib,time,random,shutil,markdown,boto3
from dateutil.parser import parse
from deepdiff import DeepDiff
from pprint import pprint
from pathlib import Path
from unidecode import unidecode
from collections import Counter

from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

from icalendar import Calendar, Event
from collections import OrderedDict

from decimal import Decimal

def get_batches(l, batch_size):

	for i in range(0, len(l), batch_size):
		yield l[i:i + batch_size]

def get_all_seminar_ids_in_dynamoDB_table(table):

	# scan until last page
	
	try:
		
		# scan until last page
		seminar_ids = []
		last_evaluated_key = None
		while True:
			if last_evaluated_key:
				response = table.scan(ExclusiveStartKey=last_evaluated_key)
			else:
				response = table.scan()
			my_seminar_ids=[item['seminar_id'] for item in response['Items']]
			seminar_ids.extend(my_seminar_ids)
			last_evaluated_key = response.get('LastEvaluatedKey')
			if not last_evaluated_key:
				break
		
		seminar_ids = [int(x) for x in seminar_ids]
		seminar_ids = list(set(seminar_ids))

		return seminar_ids
		
	except Exception as e:
		
		print(e)
		print("Error: Could not get partition keys from dynamoDB")
		
		sys.exit()

def get_partition_key(primary_key):

	partition_key={'partition_key': str(primary_key)}

	return partition_key

def prepare_items_for_dynamoDB(primary_keys):

	# if item is a list
	if isinstance(primary_keys, list):
		items=[seminars[int(x)] for x in primary_keys]
		items=[json.loads(json.dumps(x), parse_float=Decimal) for x in items]
		return items
	else:
		item=seminars[int(primary_keys)]
		item=json.loads(json.dumps(item), parse_float=Decimal)
		return item

def put_item_in_dynamoDB_table(primary_key,table):

	item=prepare_items_for_dynamoDB(primary_key)

	try:
		
		table.put_item(Item=item)
		return True
	except Exception as e:
		print(e)
		print("Error: Could not put item in dynamoDB")
		return False

def put_batch_in_dynamoDB_table(primary_keys,table):

	items=prepare_items_for_dynamoDB(primary_keys)
	batch=[{'PutRequest': {'Item': item}} for item in items]

	try:
		dynamodb.batch_write_item(
			RequestItems={
				table.name: batch
			}
		)
		return True
	except Exception as e:
		print(e)
		print("Error: Could not put batch in dynamoDB")
		return False

def delete_item_in_dynamoDB_table(primary_key,table):

	partition_key=get_partition_key(primary_key)

	try:
		table.delete_item(Key=partition_key)

	except Exception as e:
		print(e)
		print("Error: Could not delete item in dynamoDB")
		return False

	return True

def delete_batch_in_dynamoDB_table(primary_keys,table):


	batch=[{'DeleteRequest': {'Key': get_partition_key(primary_key)}} for primary_key in primary_keys]

	try:
		dynamodb.batch_write_item(
			RequestItems={
				table.name: batch
			}
		)
		return True

	except Exception as e:
		print(e)
		print("Error: Could not delete batch in dynamoDB")
		return False

def get_item_from_dynamoDB_table(primary_key,table):

	partition_key=get_partition_key(primary_key)

	try:
		response = table.get_item(Key=partition_key)
		item = response['Item']
		return item
	except Exception as e:
		print(e)
		print("Error: Could not get item from dynamoDB")
		return False

def get_batch_from_dynamoDB_table(primary_keys,table):

	partition_keys=[get_partition_key(primary_key) for primary_key in primary_keys]

	print(partition_keys)

	try:
		response = dynamodb.batch_get_item(RequestItems={
			table.name: {
				'Keys': partition_keys
			}
		})
		items = response['Responses'][table.name]
		return items
	except Exception as e:
		print(e)
		print("Error: Could not get batch from dynamoDB")
		return False

def put_to_dynamoDB(primary_keys,table):

	if isinstance(primary_keys, list):
		pass
	else:
		primary_keys=[primary_keys]

	batches=get_batches(primary_keys,batch_size)

	for primary_keys_batch in batches:

		if len(primary_keys_batch)>1:
			status=put_batch_in_dynamoDB_table(primary_keys_batch,table)
		else:
			status=put_item_in_dynamoDB_table(primary_keys_batch[0],table)

		if status==False:
			print('Error: Could not put items in dynamoDB')
			print('These are the primary keys that were not updated: ' + str(keys))
			sys.exit()
		else:
			pass

def delete_from_dynamoDB(primary_keys,table):

	if isinstance(primary_keys, list):
		pass
	else:
		primary_keys=[primary_keys]

	batches=get_batches(primary_keys,batch_size)

	for primary_keys_batch in batches:

		if len(primary_keys_batch)>1:
			status=delete_batch_in_dynamoDB_table(primary_keys_batch,table)
		else:
			status=delete_item_in_dynamoDB_table(primary_keys_batch[0],table)

		if status==False:
			print('Error: Could not delete items in dynamoDB')
			print('These are the primary keys that were not deleted: ' + str(keys))
			sys.exit()
		else:
			pass

def get_from_dynamoDB(primary_keys,table):

	t1=time.time()

	if isinstance(primary_keys, list):
		pass
	else:
		primary_keys=[primary_keys]

	batches=get_batches(primary_keys,batch_size)

	items=[]

	for primary_keys_batch in batches:

		t11=time.time()

		if len(primary_keys_batch)>1:
			items+=get_batch_from_dynamoDB_table(primary_keys_batch,table)
		else:
			item=get_item_from_dynamoDB_table(primary_keys_batch[0],table)
			items.appen(item)
		
		t22=time.time()

		print('Time to get batch of ' + str(len(primary_keys_batch)) + ' items from dynamoDB: ' + str(t22-t11))

		if items==False:
			print('Error: Could not get items from dynamoDB')
			print('These are the primary keys that were not found: ' + str(keys))
			sys.exit()
		else:
			pass
	
	t2=time.time()
	dt=t2-t1
	print('Time to get all ' + str(len(primary_keys)) + ' items from dynamoDB: ' + str(dt))

	return items

def ensure_cross_sheet_compatibility(this_dict):

	new_dict=dict()
	for k,v in this_dict.items():

		if k in cross_sheet_dict:
			k=cross_sheet_dict[k]

		new_dict[k]=v

	return new_dict

def img_is_hosted_on_gdrive(img_url):
	if 'https://drive.google.com/' in img_url:
		return True
	else:
		return False

def img_is_hosted_on_twitter(img_url):
	#https://pbs.twimg.com/media/FD7jt3JXIAoTKQu
	if 'https://pbs.twimg.com/media/' in img_url:
		return True
	else:
		return False
	
def get_file_id_from_gdrive_url(gdrive_url):
	try:
		# https://drive.google.com/file/d/1DtxNJaJFglKGRn1MJnIgn0fKzuZZFyka/view
		file_id=re.search('(?<=file/d/).*(?=/view)',gdrive_url).group(0)
	except:
		return None

	return file_id

def check_if_domain_tags_and_colors_are_loaded_otherwise_load_them(seminar_domain):

	for sd in seminar_domain:

		if sd in tags_and_colors:

			pass

		else:

			with open(working_dir + world_wide_domains[sd]['domain_alias'] + '/tags_and_colors.json','r') as f:
				sd_tags_and_colors_data=json.load(f)

			topic_tags_to_noc_color=sd_tags_and_colors_data[1]
			series_tags_to_noc_color=sd_tags_and_colors_data[3]

			sd_tags_colors=dict()
			sd_tags_colors['topic_info']=topic_tags_to_noc_color
			sd_tags_colors['series_info']=series_tags_to_noc_color

			tags_and_colors[sd]=sd_tags_colors

def add_automatically_extracted_keywords(unique_hash):
	fname=curated_keyphrases_dir+unique_hash+'.pkl'
	try:
		if os.path.isfile(fname):
			with open(fname,'rb') as f:
				data=pickle.load(f)
			auto_keywords=data[1]
		else:
			auto_keywords=[]
	except:
		return []

	return auto_keywords

def kp_is_EI_balance(x):

	x=x.lower()

	if x.endswith('balance') and 'inhibi' in x:
		if x.startswith('excit'):
			return True
	elif x=='e-i balance':
		return True
	elif x=='e/i balance':
		return True
	elif x=='e&i balance':
		return True
	elif x=='e - i balance':
		return True
	elif x=='e / i balance':
		return True
	elif x=='e & i balance':
		return True
	elif x=='ei balance':
		return True
	elif x=='e i balance':
		return True
	else:
		return False

def decapitalize_seminar_tags(seminar_tags,auto_keywords,seminar_domain):

	if len(seminar_tags)>0 or len(auto_keywords)>0:
		seminar_tags=[x.strip() for x in re.split(r'[,;]',seminar_tags)]
		seminar_tags=[x for x in seminar_tags if len(x)>0]
		all_seminar_tags=[]

		auto_keywords_lower=[x.lower() for x in auto_keywords]
		for stag in seminar_tags:
			if stag.lower() not in auto_keywords_lower:
				all_seminar_tags.append(stag)

		for stag in auto_keywords:
			if not stag in all_seminar_tags:
				all_seminar_tags.append(stag)

		seminar_tags=list(set(all_seminar_tags))
		decapitalized=[]
		for x in seminar_tags:
			if x[0].isupper() and x not in ['Alzheimer\'s','Dravet\'s','Parkinson\'s','Dravet']:
				status=True
				if any([i.isupper() for i in x[1:]]):
					status=False
				if status:
					x=x.lower()
			if len(x.split())<4 and x not in ['neuroscience','low-cost lamp','tasks','task','challenges','challenge','patherns','neural mechanism','neural mechanisms','tutorial','project','projects','neurology','object','objects','systems','system','brain','essentialism in psychology']:
				if 'successf' not in x.lower() or 'approaches' not in x.lower():
					decapitalized.append(x)
		decapitalized=['Alzheimer\'s' if x in ['AD','alzheimer\'s','alzheimer','Alzheimer'] else x for x in decapitalized]
		decapitalized=['Alzheimer\'s' if 'alzheimer' in x.lower()  else x for x in decapitalized]
		decapitalized=['Parkinson\'s' if x in ['PD','parkinson\'s','parkinsons','Parkinsons'] else x for x in decapitalized]
		decapitalized=['Parkinson\'s' if 'parkinson' in x.lower()  else x for x in decapitalized]
		decapitalized=['Spanish 🗣️' if x.lower() in ['spanish','español'] else x for x in decapitalized]
		decapitalized=['behaviour' if x=='behavior' else x for x in decapitalized]
		decapitalized=['haltere' if x=='halteres' else x for x in decapitalized]
		decapitalized=['computational neuroscience' if x=='computational' else x for x in decapitalized]
		decapitalized=['interneurons' if x=='inhibition' else x for x in decapitalized]
		decapitalized=['epilepsy' if x=='epilepsy neuroscience' else x for x in decapitalized]
		decapitalized=['reward learning' if x in ['reward','rewards'] else x for x in decapitalized]
		decapitalized=['orbitofrontal cortex' if x.lower()=='ofc' else x for x in decapitalized]
		decapitalized=['vision' if x in ['visual science','visual'] else x for x in decapitalized]
		decapitalized=['invertebrates' if x in ['invertebrate'] else x for x in decapitalized]
		decapitalized=['cognition' if 'cognitive' in x.lower()  else x for x in decapitalized]
		decapitalized=['fMRI' if x.lower()=='fmri' else x for x in decapitalized]
		decapitalized=['Python' if x.lower()=='python' else x for x in decapitalized]
		decapitalized=['circuits' if x.lower()=='circuit' else x for x in decapitalized]
		decapitalized=['neural circuits' if x.lower()=='circuits' else x for x in decapitalized]
		decapitalized=['calcium imaging' if x.lower()=='ca2+ imaging' else x for x in decapitalized]
		decapitalized=['calcium imaging' if x.lower()=='ca2 imaging' else x for x in decapitalized]
		decapitalized=['calcium imaging' if x.lower()=='ca imaging' else x for x in decapitalized]
		decapitalized=['EEG' if x.lower()=='eeg' else x for x in decapitalized]
		decapitalized=['V1' if x.lower()=='v1' else x for x in decapitalized]
		decapitalized=['LAMP' if x.lower()=='lamp' else x for x in decapitalized]
		decapitalized=['vagus nerve' if x.lower()=='vagus' else x for x in decapitalized]
		decapitalized=['C. elegans' if 'elegans' in x.lower() else x for x in decapitalized]
		decapitalized=['neurodegenerative diseases' if 'neurodegenerative dis' in x.lower() else x for x in decapitalized]
		decapitalized=['COVID-19' if 'covid' in x.lower() else x for x in decapitalized]
		decapitalized=['COVID-19' if 'sars co' in x.lower() else x for x in decapitalized]
		decapitalized=['machine learning' if 'ml'==x.lower() else x for x in decapitalized]
		decapitalized=['artificial intelligence' if 'ai'==x.lower() else x for x in decapitalized]
		decapitalized=['reinforcement learning' if 'rl'==x.lower() else x for x in decapitalized]
		decapitalized=['machine learning' if 'machine learning'==x.lower() else x for x in decapitalized]
		decapitalized=['E/I balance' if kp_is_EI_balance(x) else x for x in decapitalized]
		decapitalized=['artificial intelligence' if 'artificial intelligence'==x.lower() else x for x in decapitalized]
		decapitalized=['reinforcement learning' if 'reinforcement learning'==x.lower() else x for x in decapitalized]
		decapitalized=[x.replace('.','') for x in decapitalized]
		decapitalized=[x.replace(',','') for x in decapitalized]
		decapitalized=[x.replace('behavior','behaviour') for x in decapitalized]
		decapitalized=[x.replace('modelling','modeling') for x in decapitalized]
		decapitalized=[x.replace('birdsong','bird-song') for x in decapitalized]
		decapitalized=[x.replace('song-bird','bird-song') for x in decapitalized]
		decapitalized=[x.replace('songbird','bird-song') for x in decapitalized]
		decapitalized=[x.replace('decision making','decision-making') for x in decapitalized]
		decapitalized=[x.replace('3d','3D') for 	x in decapitalized]
		decapitalized=[x.replace('2-photon','two-photon') for x in decapitalized]
		decapitalized=['deep learning' if 'deep learning'==x.lower() else x for x in decapitalized]
		decapitalized=['inhibition' if 'inhibitory interneurons'==x.lower() else x for x in decapitalized]
		decapitalized=[x.replace('LGBT Right','LGBT Rights') for x in decapitalized]
		decapitalized=list(set(decapitalized))
		decapitalized=sorted(decapitalized)

		decapitalized=sort_based_on_domain_specific_noc(decapitalized,seminar_domain)
		
		return decapitalized
	else:
		return []

def sort_based_on_domain_specific_noc(topic_tags_to_be_sorted,seminar_domain):

	topic_tags_to_noc=[]
	topic_tags_with_no_noc_info=[]

	for t in topic_tags_to_be_sorted:

		my_status=False
		for sd in seminar_domain:
			if t in tags_and_colors[sd]['topic_info']:
				topic_tags_to_noc.append([t,tags_and_colors[sd]['topic_info'][t]['noc']])
				my_status=True
		if my_status==False:
			topic_tags_with_no_noc_info.append(t)

	'''print()
	print()
	print()
	print()
	print(topic_tags_to_be_sorted,topic_tags_with_no_noc_info)'''
	topic_tags_to_noc=sorted(topic_tags_to_noc, key = lambda x: (x[1],x[0]), reverse=True)
	ntopic_tags_to_be_sorted=[t[0] for t in topic_tags_to_noc] + list(sorted(topic_tags_with_no_noc_info))

	used=[]
	topic_tags_to_be_sorted=[]

	for t in ntopic_tags_to_be_sorted:
		if t not in used:
			topic_tags_to_be_sorted.append(t)
			used.append(t)
	#print(topic_tags_to_be_sorted)
	#print()

	return topic_tags_to_be_sorted

def get_series_color(seminar_series_name,seminar_domain):

	for sd in seminar_domain:
		if seminar_series_name in tags_and_colors[sd]['series_info']:
			return tags_and_colors[sd]['series_info'][seminar_series_name]['color']
	return None

def if_json_file_is_not_the_same_or_doesnt_exist(json_fname,new_json_data,str_status):
	with open(json_fname,'r') as f:
		old_json_data=json.load(f)

	try:
		ddiff = DeepDiff(old_json_data, new_json_data)
		if len(ddiff)>0:
			'''print(old_json_data['topic_tags'])
			print(new_json_data['topic_tags'])
			for tt in new_json_data['topic_tags']:

				tt_sd=new_json_data['domain'][0]
				print(tt,tt_sd,tags_and_colors[tt_sd]['topic_info'][tt]['noc'])'''

			# EXAMPLE 
			'''
			{'values_changed': {"root['timestamp']": {'new_value': 1623956400,
										  'old_value': 1623949200}}}
			'''

			# if values_changed is only timestamp, then it is not a big deal
			if 'values_changed' in ddiff:
				if len(ddiff['values_changed'])==1 and 'root[\'timestamp\']' in ddiff['values_changed']:
					return False

			print('='*100)
			print()
			pprint(new_json_data['seminar_id'])
			pprint(ddiff)
			print()
			print('='*100)
	except:
		pass

	if isinstance(new_json_data,dict):
		new_json_data=OrderedDict(sorted(new_json_data.items(), key=lambda k : k))
		old_json_data=OrderedDict(sorted(old_json_data.items(), key=lambda k : k))
	elif str_status:
		new_json_data=str(sorted(list(str(new_json_data))))
		old_json_data=str(sorted(list(str(old_json_data))))

	if new_json_data!=old_json_data:
		return True
	else:
		return False
	
def parse_date(seminar_date,seminar_time,seminar_timezone):

	seminar_timezone=pytz.timezone(seminar_timezone)

	start_datetime=parse(seminar_date + ' ' + seminar_time, fuzzy=True)
	end_datetime=start_datetime+datetime.timedelta(hours=1)

	start_datetime = seminar_timezone.localize(start_datetime).astimezone(pytz.UTC)
	end_datetime = seminar_timezone.localize(end_datetime).astimezone(pytz.UTC)

	start_datetime=start_datetime.strftime("%Y%m%dT%H%M%S")
	end_datetime=end_datetime.strftime("%Y%m%dT%H%M%S")
	
	return start_datetime,end_datetime

def new_parse_date(seminar_date,seminar_time,seminar_timezone,seminar_duration):

	seminar_timezone=pytz.timezone(seminar_timezone)

	start_datetime=parse(seminar_date + ' ' + seminar_time, fuzzy=True)
	end_datetime=start_datetime+datetime.timedelta(minutes=seminar_duration)

	start_datetime = seminar_timezone.localize(start_datetime).astimezone(pytz.UTC)
	end_datetime = seminar_timezone.localize(end_datetime).astimezone(pytz.UTC)
	
	return start_datetime,end_datetime

def add_unix_timestamp(item):

	seminar_date=item['seminar_date']
	seminar_time=item['seminar_time']
	seminar_timezone=item['timezone']

	'''
	
	EXAMPLE
	
	'seminar_date': 'Fri, Sep 18, 2020',
	'seminar_time': '15:00',
	'timezone': 'Europe/London'

	'''

	# Convert the date and time to a datetime object
	seminar_datetime = parse(seminar_date + ' ' + seminar_time, fuzzy=True)
	
	# Localize the datetime object to the timezone specified
	seminar_datetime = seminar_datetime.astimezone(pytz.timezone(seminar_timezone))
	seminar_datetime = seminar_datetime.replace(tzinfo=datetime.timezone.utc)
	
	# Convert the datetime object to a unix timestamp
	unix_timestamp = int(seminar_datetime.timestamp())

	item['timestamp'] = unix_timestamp

	return item

def use_this_row(x,post_column_idx):

	if x[post_column_idx].strip().lower()=='yes':
		return True
	else:
		return False

def open_graph_title(content,x):
	content=re.sub(r'<meta property="og:title" content=".*?">','<meta property="og:title" content="World Wide | '+x+'">',content)
	return content

def open_graph_description(content,x):
	content=re.sub(r'<meta name="description" content=".*?">','<meta name="description" content="Discover and attend scientific events or advertise your own 🔆">',content)
	return content

def open_graph_image_card(content,domain_alias,x):
	content=re.sub(r'<meta property="og:image" content=".*?">','<meta property="og:image" content="https://www.world-wide.org/'+domain_alias+'/meta_cards/'+x+'">',content)
	return content

def open_graph_url(content,x):
	content=re.sub(r'<meta property="og:url" content=".*?">','<meta property="og:url" content="https://www.world-wide.org/seminar/'+str(x)+'">',content)
	return content

def make_the_necessary_substitutions_to_the_template(seminar_id,seminar_domain):

	domain_name=world_wide_domains[seminar_domain]['domain_name']
	domain_alias=world_wide_domains[seminar_domain]['domain_alias']
	domain_nickname=world_wide_domains[seminar_domain]['domain_nickname']

	try:
		meta_cards_dir=working_dir+domain_alias+'/meta_cards/'
		meta_cards=[x for x in os.listdir(meta_cards_dir) if x[0]!='.']
		image_card=random.choice(meta_cards)
	except:
		image_card='https://www.world-wide.org/banner.jpg'

	speaker_title_name=seminars[seminar_id]['speaker_title']+' '+seminars[seminar_id]['seminar_speaker']
	speaker_title_name=speaker_title_name.strip()

	head_seminar_page_template=open_graph_title(seminar_page_template,domain_name)
	head_seminar_page_template=open_graph_description(head_seminar_page_template,x)
	head_seminar_page_template=open_graph_image_card(head_seminar_page_template,domain_alias,image_card)
	head_seminar_page_template=open_graph_url(head_seminar_page_template,seminar_id)
	
	return head_seminar_page_template

def create_the_seminar_index_page(seminar_id):

	seminar_domain=seminars[seminar_id]['domain'][0]

	head_seminar_page_template=make_the_necessary_substitutions_to_the_template(seminar_id,seminar_domain)

	seminar_index_path_fname=working_dir+'seminar/' + str(seminar_id) + '/index.html'

	with open(seminar_index_path_fname,'w') as f:
		f.write(head_seminar_page_template)

	os.system('/usr/local/bin/aws s3 cp ' + seminar_index_path_fname + ' s3://www.world-wide.org/seminar/' + str(seminar_id) + '/index.html')

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

def create_ical_file(my_dict,unique_hash):

	seminar_date=my_dict['seminar_date']
	seminar_time=my_dict['seminar_time']

	try:

		seminar_timezone=my_dict['timezone']
		seminar_duration=int(my_dict['Event Duration'])

	except:

		pprint(my_dict)

	start_datetime,end_datetime=new_parse_date(seminar_date,seminar_time,seminar_timezone,seminar_duration)

	speaker_title=my_dict['speaker_title']
	seminar_speaker=my_dict['seminar_speaker']
	speaker_affil=my_dict['speaker_affil']

	seminar_title=my_dict['seminar_title']
	hosted_by=my_dict['hosted_by']
	ww_seminar_url='https://www.world-wide.org/seminar/' + str(my_dict['seminar_id'])

	event_summary=speaker_title+' '+seminar_speaker+''

	event_description='This is a World Wide seminar\n\n'
	event_description+='Speaker: '
	if speaker_title!='':
		event_description+=speaker_title + ' '
	event_description+=seminar_speaker 
	if speaker_affil!='':
		event_description+=' | ' + speaker_affil
	event_description+='\n\n'
	if event_description!='':
		event_description+='Seminar Title: "' + seminar_title + '"' + '\n\n'
	event_description+='Link: ' + ww_seminar_url

	cal = Calendar()
	event = Event()

	event.add('uid', unique_hash)
	event.add('summary', event_summary)
	event.add('description', event_description)
	event.add('dtstart',start_datetime)
	event.add('dtend',end_datetime)
	# let's add DTSTAMP too
	now = datetime.datetime.now()
	event.add('dtstamp',now)

	cal.add_component(event)
	# we need to add prodid to make it a valid ical file
	cal.add('prodid', '-//My calendar product//www.world-wide.org//')
	# now, we need to add version to make it a valid ical file
	cal.add('version', '2.0')

	ical_event_string=str(cal.to_ical(),'utf-8').strip()
	
	return ical_event_string,event

def check_if_calendar_file_exists_and_is_unchanged(ical_event_string,seminar_id):

	just_generated_ical_string=re.sub(r'\s','',ical_event_string,flags=re.DOTALL)
	just_generated_ical_string=re.sub(r'DTSTAMP;VALUE=DATE-TIME:.*?UID','',just_generated_ical_string,flags=re.DOTALL)

	try:
		with open(working_dir +'seminar/'+str(seminar_id)+'/seminar_event.ics','r') as f:
			file_line=f.read()
		
		file_line=re.sub(r'\s','',file_line,flags=re.DOTALL)
		file_line=re.sub(r'DTSTAMP;VALUE=DATE-TIME:.*?UID','',file_line,flags=re.DOTALL)
		
		if file_line==just_generated_ical_string:
			return 'same'
		else:
			return 'different'
	except:
		return 'different'

def get_seminar_series_data(seminar_series_data):

	regex=r'((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*'

	my_dict=dict(zip(seminar_series_data[2],seminar_series_data[3]))

	pop_these_out=[]
	for k in my_dict.keys():
		if k not in ['Series Name','Organized by','Banner Image','About this Series']:
			pop_these_out.append(k)
	for k in pop_these_out:
		my_dict.pop(k, None)

	banner_image=my_dict['Banner Image']
	my_re=re.search(r'(.*?)\.(jpg|jpeg|bmp|gif|png)$',banner_image,re.IGNORECASE)
	if not my_re:
		my_dict['Banner Image']=''

	seminar_series_name=unidecode(my_dict['Series Name'])
	seminar_series_name=re.sub(r'[^A-Za-z0-9-& ]',' ',seminar_series_name)
	seminar_series_name=re.sub(r'\s\s+',' ',seminar_series_name)
	my_dict['Series Name']=seminar_series_name.strip()

	about_this_series=my_dict['About this Series']
	about_this_series=about_this_series.strip('"')

	if 'Seminar in Chronobiology & Visual Neuroscience** is organised by' in about_this_series:
		about_this_series = markdown.markdown(about_this_series)
	email_matches=re.findall(r'[\w\.-]+@[\w\.-]+',about_this_series)
	email_matches=list(set(email_matches))
	for email_match in email_matches:
		enrich_email_match_with_href='📧 <a href="mailto:'+email_match+'">'+email_match+'</a>'
		about_this_series=about_this_series.replace(email_match,enrich_email_match_with_href)
		
	my_dict['About this Series']=about_this_series

	try:
		organized_by=[i.strip() for i in my_dict['Organized by'].split(';')]
		org_links=[]
		for i in organized_by:
			s=re.search(regex,i).span()
			text=i[0:s[0]].strip()
			url=i[s[0]:s[1]]
			org_links.append({'text':text,'url':url})
		my_dict['Organized by']=org_links
	except:
		my_dict['Organized by']=''

	return my_dict

def what_is_the_header_row_number(seminar_events_data):

	for i,x in enumerate(seminar_events_data):

		if 'Seminar Link' in x and 'Topic Tags' in x:
			return i

	return None

def get_seminar_rows(seminar_events_data,header_row_number,post_column_idx):

	seminar_rows=[[str(i)]+[y.strip() for y in x] for i,x in enumerate(seminar_events_data[header_row_number+1:]) if use_this_row(x,post_column_idx)]
	seminar_rows=[['' if y.lower()=='tba' else y for y in x] for x in seminar_rows]

	return seminar_rows

def make_redirection_old_seminar_ids_to_new_ones(old_seminar_id,seminar_id):

	html_string='<!DOCTYPE html><html lang="en"><head><meta http-equiv="refresh" content="0; URL=https://www.world-wide.org/seminar/'+str(seminar_id)+'/"></head></html>'

	old_seminar_html_dir=working_dir+'seminar/'+str(old_seminar_id)+'/index.html'

	if if_html_file_is_not_the_same_or_doesnt_exist(old_seminar_html_dir,html_string):

		with open(old_seminar_html_dir,'w') as f:
			f.write(html_string)

		os.system('/usr/local/bin/aws s3 cp ' + old_seminar_html_dir + ' s3://www.world-wide.org/seminar/' + str(old_seminar_id) + '/index.html')

		print(old_seminar_id,seminar_id)

def get_unique_hash(my_dict):
	
	old_string_to_digest=my_dict['Row Number'] + my_dict['seminar_speaker'] + ' ' + my_dict['hosted_by'] + my_dict['sheet_id']
	old_bytes_to_digest=bytes(old_string_to_digest.encode())
	old_unique_hash=hashlib.sha256(old_bytes_to_digest).hexdigest()

	#st_1=False
	if old_unique_hash in already_added_unique_hashes:
		old_seminar_id=seminar_speaker_unique_hash_to_seminar_id_and_date_added[old_unique_hash][0]
	#	st_1=True
	else:
		old_seminar_id=None

	string_to_digest=my_dict['seminar_speaker'] + my_dict['sheet_id'] + my_dict['seminar_date'] + my_dict['seminar_time']

	bytes_to_digest=bytes(string_to_digest.encode())
	unique_hash=hashlib.sha256(bytes_to_digest).hexdigest()

	'''st_2=False

	if my_dict['seminar_speaker']=='Valerio Mante' and my_dict['hosted_by']=='NeuroLeman Network':
		print('old_string_to_digest')
		print(old_string_to_digest)
		print('old_bytes_to_digest')
		print(old_bytes_to_digest)
		print('old_unique_hash')
		print(old_unique_hash)
		print('is old_unique_hash in already_added_unique_hashes?')
		print(st_1)
		print('Let\'s move on to the new unique hash method')
		print('string_to_digest')
		print(string_to_digest)
		print('bytes_to_digest')
		print(bytes_to_digest)
		print('unique_hash')
		print(unique_hash)
		st_2=True'''

	if unique_hash in already_added_unique_hashes:

		seminar_id=seminar_speaker_unique_hash_to_seminar_id_and_date_added[unique_hash][0]
		time_of_addition=seminar_speaker_unique_hash_to_seminar_id_and_date_added[unique_hash][1]

		#st_3=False
		if old_seminar_id!=None:

			#st_3=True

			make_redirection_old_seminar_ids_to_new_ones(old_seminar_id,seminar_id)

		'''if st_2:
			print('unique_hash is already in already_added_unique_hashes')
			print('seminar_id',seminar_id)
			print('time_of_addition',time_of_addition)

			if st_3:
				print('I had to make a redirection for this seminar')

			print('\n'*3)
			print('>'*20)
			print('\n'*3)'''
		
		return unique_hash,seminar_id,time_of_addition

	else:

		'''if st_2:
			print('unique_hash is not in already_added_unique_hashes')
			print('\n'*3)
			print('>'*20)
			print('\n'*3)'''

		return unique_hash,None,None

def what_spreadsheets_should_I_fetch(time_window_in_seconds):

	regex=r'spreadsheets/d/([a-zA-Z0-9-_]+)'
	

	with open(working_dir_python_code+'world_wide_gsheets.pkl','rb') as f:
		world_wide_gsheets=pickle.load(f)

	google_sheets_list=[x['Google Sheet'] for x in world_wide_gsheets]
	google_sheets_list=[re.search(regex,x).group(1) for x in google_sheets_list]

	workshop_sheets_list=[x['Google Sheet'] for x in world_wide_gsheets if x['Workshop'].lower()=='yes']
	workshop_sheets_list=[re.search(regex,x).group(1) for x in workshop_sheets_list]

	gsheets_dict={re.search(regex,x['Google Sheet']).group(1):x for x in world_wide_gsheets}

	random.shuffle(google_sheets_list)

	# If modifying these scopes, delete the file token.pickle.
	scope = ['https://www.googleapis.com/auth/drive.metadata.readonly']
	credentials = ServiceAccountCredentials.from_json_keyfile_name(working_dir_python_code+'imposing-timer-196815-615db1a19785.json', scope)
	service = build('drive', 'v3', credentials=credentials)
	
	# Call the Drive v3 API
	results = service.files().list(
		pageSize=300, fields="nextPageToken, files(id, modifiedTime)").execute()
	items = results.get('files', [])

	mod_time_gsheets={ item['id'] : parse(item['modifiedTime']) for item in items }

	#with open(working_dir_python_code + 'mod_time.pkl','rb') as f:
	#	mod_time_local=pickle.load(f)

	datetime_now = datetime.datetime.utcnow()
	datetime_now = datetime_now.replace(tzinfo=pytz.utc) 

	fetch_these_gsheets=[]

	for gsheet_id in google_sheets_list:
		try:
			time_difference = datetime_now - mod_time_gsheets[gsheet_id]
			total_seconds = time_difference.total_seconds()
			#if gsheet_id=='1Z9fpdLPC8mj7NWPt3Zj0bXO83gdDz315h8FHLV_KmFM':
			#	total_seconds=100

			#print(gsheet_id,total_seconds)
			#print(gsheet_id,'%d hours, %d minutes, %d seconds' % (total_seconds//3600, total_seconds%3600//60, total_seconds%60))
			if total_seconds > 0 and total_seconds <= time_window_in_seconds:
				print('This was modified over the past',int(time_window_in_seconds/60),'minutes:',gsheet_id,'-- to be exact:',int(total_seconds),'seconds ago')
				fetch_these_gsheets.append(gsheet_id)
		except:
			pass

	mod_time_local=mod_time_gsheets
	#with open(working_dir_python_code + 'mod_time.pkl','wb') as f:
	#	pickle.dump(mod_time_local,f)

	return gsheets_dict,google_sheets_list,fetch_these_gsheets,workshop_sheets_list

def sync_all_edited_once_again_just_in_case(at_this_hour_every_day):

	dt = datetime.datetime.now()
	if dt.hour%at_this_hour_every_day==0:
		dt_hour = dt.replace(minute=0, second=0, microsecond=0) # Returns a copy
		time_difference=dt-dt_hour
		total_seconds = time_difference.total_seconds()
		
		if total_seconds<=300:
			return True
		else:
			return False
	else:
		return False

def get_spreadsheet(google_sheet_id):

	credentials = ServiceAccountCredentials.from_json_keyfile_name(working_dir_python_code+'imposing-timer-196815-245fab6211ac.json', scope)
	gc = gspread.authorize(credentials)
	spreadsheet = gc.open_by_key(google_sheet_id)

	fetched_status=True

	print('Just fetched this Google Sheet:',google_sheet_id)
	current_date_time=str(datetime.datetime.now())
	print(current_date_time)

	return spreadsheet,fetched_status

def get_seminar_sheet_data(spreadsheet):

	worksheets=spreadsheet.worksheets()
	worksheet_titles=[ws.title for ws in worksheets]

	if 'Seminar Events' in worksheet_titles:
		seminar_events_sheet=spreadsheet.worksheet('Seminar Events')
	elif 'Accepted' in worksheet_titles:
		seminar_events_sheet=spreadsheet.worksheet('Accepted')
	
	seminar_events_data=seminar_events_sheet.get_all_values()

	seminar_series_sheet=spreadsheet.worksheet('Seminar Series')
	seminar_series_data=seminar_series_sheet.get_all_values()

	with open(working_dir_python_code+'series_gsheets/'+google_sheet_id+'.pkl','wb') as f:
		pickle.dump([seminar_events_data,seminar_series_data],f)

	return seminar_events_data,seminar_series_data

def get_workshop_sheet_data(spreadsheet):
	
	event_program_sheet=spreadsheet.worksheet('Event Program')
	event_program_data=event_program_sheet.get_all_values()

	event_info_sheet=spreadsheet.worksheet('Event Info')
	event_info_data=event_info_sheet.get_all_values()

	with open(working_dir_python_code+'workshop_gsheets/'+google_sheet_id+'.pkl','wb') as f:
		pickle.dump([event_program_data,event_info_data],f)

	return event_program_data,event_info_data

def parse_session_data(event_program_data):

	headers_set=set(['Date','Time','Timezone','Session Title','Session Link','Password','Session Duration (in minutes)'])
	headers_indices_start=[i for i,e in enumerate(event_program_data) if headers_set == set(e)]
	headers_indices_stop=[i-1 for i in headers_indices_start]

	session_indices=[]
	for i in range(len(headers_indices_start)):
		si_START=headers_indices_start[i]
		try:
			si_STOP=headers_indices_start[i+1]
		except:
			si_STOP=len(event_program_data)-1
		session_indices.append((si_START,si_STOP))

	workshop_sessions=[event_program_data[i[0]:i[1]] for i in session_indices]
	workshop_sessions=[[ii for ii in i if len(''.join([str(iii) for iii in ii]))>3] for i in workshop_sessions]
	workshop_sessions=transform_workshop_sessions(workshop_sessions)

	return workshop_sessions

def transform_workshop_sessions(workshop_sessions):

	session_data=[]
	for session in workshop_sessions:

		session_dict=dict()

		headers_A=session[0]
		session_info=dict(zip(headers_A,session[1]))
		session_info=ensure_cross_sheet_compatibility(session_info)

		session_dict['Session Info']=session_info

		headers_B=session[2]
		session_details=[]
		for i in session[3:]:
			session_dt=dict(zip(headers_B,i))
			session_dt=ensure_cross_sheet_compatibility(session_dt)
			session_details.append(session_dt)
		session_dict['Session Details']=session_details

		session_data.append(session_dict)

	return session_data

def parse_workshop_info(event_info_data):

	headers=event_info_data[2]
	workshop_info=dict(zip(headers,event_info_data[3]))

	return workshop_info

def open_and_read_reference_json_file(ref_fname):

	try:
		with open(ref_fname,'r') as f:
			example_json=json.load(f)
	except:
		return None

	return example_json

def if_json_file_is_not_the_same(ref_fname, target_json):
	
	example_json=open_and_read_reference_json_file(ref_fname)
	if example_json==None:
		return True

	different_variables=len(DeepDiff(example_json, target_json, ignore_order=True))

	if different_variables==0:
		return False
	else:
		different_variables=parseJSON(example_json, target_json)
		return different_variables!=0

def parseJSON(reference, target):
	different_variables=0
	# the case that the inputs is a dict (i.e. json dict)  
	try:
		if isinstance(reference, dict):
			ddiff = DeepDiff(json.dumps(reference), json.dumps(target), ignore_order=True)
			if len(ddiff)!=0:
				different_variables+=1
		# the case that the inputs is a list/tuple
		elif isinstance(reference, list) or isinstance(reference, tuple):
			for index, v in enumerate(reference):
					target_v=target[index]
					if isinstance(v, dict):
						ddiff = DeepDiff(json.dumps(v), json.dumps(target_v), ignore_order=True)
						if len(ddiff)!=0:
							different_variables+=1
					else:
						if v!=target_v:
							different_variables+=1
		# the actual comparison about the value, if they are not the same, record it
		elif reference != target:
			different_variables+=1
	except:
		different_variables+=1

	return different_variables

def strip_quotes(x):

	x=x.strip('"')
	x=x.strip('“')
	x=x.strip('”')

	return x

def remove_excess_newlines(x):

	try:

		number_of_newlines=re.findall('\n',x)
		number_of_newlines=len(number_of_newlines)

		if number_of_newlines>7:
			# replace all newlines with a single space
			x=re.sub('\n',' ',x)
			x=re.sub('\s+',' ',x)

		return x
	
	except:

		return x

def transform_github_urls(x):

	# remove everything after question mark
	if '?' in x:
		x=x.split('?')[0]

	if 'github.com' in x:
		# https://github.com/mainmeeting/main2021/blob/main/assets/img/main_2021_banner.jpg
		# https://raw.githubusercontent.com/mainmeeting/main2021/main/assets/img/main_2021_banner.jpg
		x=x.replace('github','raw.githubusercontent.com')

	return x

def parse_X_argument(sync_all_edits_over_the_past_X):
	# convert X to seconds (int type)
	# if X is followed by hr or h, interpret as hours and convert to seconds
	# if X is followed by min or m, interpret as minutes and convert to seconds

	if 'hr' in sync_all_edits_over_the_past_X:
		sync_all_edits_over_the_past_X=int(sync_all_edits_over_the_past_X.split('hr')[0])*3600
	elif 'h' in sync_all_edits_over_the_past_X:
		sync_all_edits_over_the_past_X=int(sync_all_edits_over_the_past_X.split('h')[0])*3600
	elif 'min' in sync_all_edits_over_the_past_X:
		sync_all_edits_over_the_past_X=int(sync_all_edits_over_the_past_X.split('min')[0])*60
	elif 'm' in sync_all_edits_over_the_past_X:
		sync_all_edits_over_the_past_X=int(sync_all_edits_over_the_past_X.split('m')[0])*60
	else:
		sync_all_edits_over_the_past_X=int(sync_all_edits_over_the_past_X)
	
	return sync_all_edits_over_the_past_X

def convert_total_seconds_to_human_readable_hrs_minutes(x):
	x_hr=x//3600
	x_min=(x%3600)//60
	return x_hr, x_min

def increase_or_decrease_write_capacity_and_is_it_time_to_sync_all_seminars_dynamoDB():

	# if it is within 5 minutes past 3am or 3pm we should increase the write capacity of dynamoDB and sync all seminars to dynamoDB
	# if it is within 5 minutes past 3.40am or 3.40pm we should decrease the write capacity of dynamoDB, no need to sync all seminars to dynamoDB we did that 40 minutes ago

	now=datetime.datetime.now()
	if now.hour==3 and now.minute<5:
		print('1. Increasing write capacity of dynamoDB table and syncing all seminars to dynamoDB')
		return 'increase', True
	elif now.hour==15 and now.minute<5:
		print('2. Increasing write capacity of dynamoDB table and syncing all seminars to dynamoDB')
		return 'increase', True
	elif now.hour==3 and now.minute>40:
		print('3. Decreasing write capacity of dynamoDB table and no need to sync all seminars to dynamoDB')
		return 'decrease', False
	elif now.hour==15 and now.minute>40:
		print('4. Decreasing write capacity of dynamoDB table and no need to sync all seminars to dynamoDB')
		return 'decrease', False
	else:
		print('5. No change to write capacity of dynamoDB table and no need to sync all seminars to dynamoDB')
		return 'no change', False

def update_dynamoDB_table_write_capacity(increase_or_decrease_dynamoDB_write_capacity):

	sleep_seconds=2

	my_t1 = time.time()

	if increase_or_decrease_dynamoDB_write_capacity=='no change':
		return

	time.sleep(sleep_seconds)
	table_description = dynamodb_client.describe_table(TableName='world-wide-seminars')
	while table_description["Table"]["TableStatus"] != "ACTIVE":
		time.sleep(sleep_seconds)
		table_description = dynamodb_client.describe_table(TableName='world-wide-seminars')

	# what is the tables current write capacity?
	current_max_dynamo_db_write_capacity=table_description["Table"]["ProvisionedThroughput"]["WriteCapacityUnits"]

	try:

		if current_max_dynamo_db_write_capacity<99 and increase_or_decrease_dynamoDB_write_capacity=='increase':

			print("Updating table write capacity to 99")
			dynamodb_client.update_table(
					TableName='world-wide-seminars',
					ProvisionedThroughput={
						"ReadCapacityUnits": 10,
						"WriteCapacityUnits": 99
					}
				)
		
		elif current_max_dynamo_db_write_capacity>33 and increase_or_decrease_dynamoDB_write_capacity=='decrease':

			print("Updating table write capacity to 33")
			dynamodb_client.update_table(
				TableName='world-wide-seminars',
				ProvisionedThroughput={
					"ReadCapacityUnits": 10,
					"WriteCapacityUnits": 33
				}
			)
		
		else:

			print("No need to update table write capacity")

	except botocore.exceptions.ClientError as e:

		if e.response['Error']['Code'] == 'ValidationException':
			print("The provisioned throughput for the table will not change. The requested value equals the current value.")
		elif e.response['Error']['Code'] == 'LimitExceededException':
			print("Subscriber limit exceeded: Provisioned throughput decreases are limited within a given UTC day. After the first 4 decreases, each subsequent decrease in the same UTC day can be performed at most once every 3600 seconds. Number of decreases today: 4. Last decrease at Monday, February 13, 2023 at 10:25:39 AM Coordinated Universal Time. Next decrease can be made at Monday, February 13, 2023 at 11:25:39 AM Coordinated Universal Time")
		else:
			raise e

	time.sleep(sleep_seconds)
	table_description = dynamodb_client.describe_table(TableName='world-wide-seminars')
	while table_description["Table"]["TableStatus"] != "ACTIVE":
		time.sleep(sleep_seconds)
		table_description = dynamodb_client.describe_table(TableName='world-wide-seminars')
	
	# perfect, good to go

	my_t2 = time.time()
	print()
	print('Time to update dynamoDB table write capacity: ', my_t2-my_t1)
	print()

try:
	force_argument=sys.argv[1]
	sync_all_edits_over_the_past_X=sys.argv[2]

	if force_argument=='force':
		sync_all_edits_over_the_past_X=parse_X_argument(sync_all_edits_over_the_past_X)
except:
	force_argument='no_force'

current_time=datetime.datetime.now()

print()
print('='*50)
print()
print('Running parse_gsheet_series_and_seminars.py')
# now let's print in a human readable format the current date and time
print('Current date and time is: ', current_time.strftime("%Y-%m-%d %H:%M:%S"))
print()

# every day at 3am and 3pm we will increase the write capacity of the dynamoDB table to 99 and then sync all of the seminars from the seminar_data.json file to the dynamoDB table
increase_or_decrease_dynamoDB_write_capacity,time_to_sync_all_seminars_to_dynamoDB_boolean=increase_or_decrease_write_capacity_and_is_it_time_to_sync_all_seminars_dynamoDB()

cross_sheet_dict={
	"Date":"seminar_date",
	"Time":"seminar_time",
	"Timezone":"timezone",
	"Time Zone":"timezone",
	"Post":"posted",
	'Publish':'posted',
	"Seminar Link":"seminar_link",
	"Password":"password",
	"Watch Again":"video_on_demand",
	"Title":"speaker_title",
	"Speaker Name":"seminar_speaker",
	"Speaker Name(s)":"seminar_speaker",
	"Virtual event / Seminar Title":"seminar_title",
	"Abstract / Descriptive Summary":"seminar_abstract",
	"Affiliation":"speaker_affil",
	"Twitter":"speaker_twitter",
	"Website":"speaker_website",
	"Topic Tags":"topic_tags",
	"Seminar Title":"seminar_title",
	"Abstract":"seminar_abstract",
	"Seminar Series":"hosted_by",
	"Duration":"Event Duration",
	"Session Duration (in minutes)":"Session Duration",
	"Title (Prof, Dr, etc)":"speaker_title"
}

working_dir_python_code=str(Path.home()) + '/Dropbox/websites/world-wide.org/python_scripts/'
working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'
working_dir_ics_files=str(Path.home()) + '/Dropbox/websites/world-wide.org/ics_files/'
curated_keyphrases_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/keyphrases/seminars/curated/'

with open(working_dir_python_code+'html_templates/seminar_page.html','r') as f:
	seminar_page_template = f.read()

with open(working_dir+'world_wide_domains.json') as json_file:
	world_wide_domains = json.load(json_file)

with open(working_dir+'seminars_matching_data.json') as json_file:
	seminars_matching_data = json.load(json_file)

try:
	with open(working_dir_python_code+'gdrive_img_urls_to_world_wide_path.pkl', 'rb') as f:
		gdrive_img_urls_to_world_wide_path = pickle.load(f)
except:
	gdrive_img_url_to_world_wide_path=dict()

tags_and_colors=dict()

world_wide_gsheets_id='18r8rVWZQpvxM10hygsJq4-4wR17i4Xld7PQFI1QVPAI'

scope = ['https://www.googleapis.com/auth/drive.metadata.readonly']
credentials = ServiceAccountCredentials.from_json_keyfile_name(working_dir_python_code+'imposing-timer-196815-615db1a19785.json', scope)
service = build('drive', 'v3', credentials=credentials)

# Call the Drive v3 API
results = service.files().get(fileId=world_wide_gsheets_id, fields="modifiedTime").execute()
world_wide_gsheets_mod_time=parse(results['modifiedTime'])

datetime_now = datetime.datetime.utcnow()
datetime_now = datetime_now.replace(tzinfo=pytz.utc) 

time_difference = datetime_now - world_wide_gsheets_mod_time
total_seconds = time_difference.total_seconds()

if total_seconds > 0 and total_seconds <= 300:

	# REQUEST AND HOPEFULLY GET ACCESS TO THE PARTICULAR SERIES GOOGLE SHEET DATA

	try: 
		scope = ['https://spreadsheets.google.com/feeds']
		credentials = ServiceAccountCredentials.from_json_keyfile_name(working_dir_python_code+'imposing-timer-196815-245fab6211ac.json', scope)
		gc = gspread.authorize(credentials)
		spreadsheet = gc.open_by_key(world_wide_gsheets_id)
		world_wide_gsheets=spreadsheet.worksheet('Gsheet Info')
		world_wide_gsheets_data=world_wide_gsheets.get_all_values()

		headers=world_wide_gsheets_data[0]
		rows=world_wide_gsheets_data[1:]

		world_wide_gsheets=[]

		for x in rows:
			my_dict=dict(zip(headers,x))
			my_dict['domain']=[i.strip() for i in my_dict['Domain'].split(';')]
			world_wide_gsheets.append(my_dict)

		with open(working_dir_python_code+'world_wide_gsheets.pkl','wb') as f:
			pickle.dump(world_wide_gsheets,f)

	except Exception as e:

		pass

scope = ['https://spreadsheets.google.com/feeds']

if force_argument=='force':

	sync_hr,sync_min=convert_total_seconds_to_human_readable_hrs_minutes(sync_all_edits_over_the_past_X)

	print()
	print('I will sync all gsheet edits over the past '+str(sync_hr)+' hours and '+str(sync_min)+' minutes')
	print()

	gsheets_dict,google_sheets_list,fetch_these_gsheets,workshop_sheets_list=what_spreadsheets_should_I_fetch(sync_all_edits_over_the_past_X)

elif sync_all_edited_once_again_just_in_case(1):
	gsheets_dict,google_sheets_list,fetch_these_gsheets,workshop_sheets_list=what_spreadsheets_should_I_fetch(3450)
else:
	gsheets_dict,google_sheets_list,fetch_these_gsheets,workshop_sheets_list=what_spreadsheets_should_I_fetch(330)

seminar_series=dict()
workshop_data=dict()

all_seminar_entries=[]

ii=0
for google_sheet_id in google_sheets_list:

	fetched_status=False

	ii+=1

	if google_sheet_id in fetch_these_gsheets:

		print('>>>> Now this:',google_sheet_id)
		time.sleep(random.randint(30,80))
		try:
			spreadsheet,fetched_status=get_spreadsheet(google_sheet_id)

		except Exception as e:

			print('>',ii,'- I couldn\'t fetch this sheet so I will try again:',google_sheet_id)
			time.sleep(random.randint(30,40))
			try:
				spreadsheet,fetched_status=get_spreadsheet(google_sheet_id)
			except:
				pass

	else:
		pass

	if fetched_status:
		if google_sheet_id in workshop_sheets_list:
			event_program_data,event_info_data=get_workshop_sheet_data(spreadsheet)
			with open(working_dir_python_code+'workshop_gsheets/'+google_sheet_id+'.pkl','wb') as f:
				pickle.dump([event_program_data,event_info_data],f)
		else:
			seminar_events_data,seminar_series_data=get_seminar_sheet_data(spreadsheet)
			with open(working_dir_python_code+'series_gsheets/'+google_sheet_id+'.pkl','wb') as f:
				pickle.dump([seminar_events_data,seminar_series_data],f)

	else:

		if google_sheet_id in workshop_sheets_list:
			with open(working_dir_python_code+'workshop_gsheets/'+google_sheet_id+'.pkl','rb') as f:
				[event_program_data,event_info_data]=pickle.load(f)
		else:
			with open(working_dir_python_code+'series_gsheets/'+google_sheet_id+'.pkl','rb') as f:
				[seminar_events_data,seminar_series_data]=pickle.load(f)
			
			# seminar_events_data,seminar_series_data=get_seminar_sheet_data(spreadsheet)
			# with open(working_dir_python_code+'series_gsheets/'+google_sheet_id+'.pkl','wb') as f:
			# 	pickle.dump([seminar_events_data,seminar_series_data],f)

	# PARSE THE SEMINAR SERIES INFORMATION DATA

	if google_sheet_id in workshop_sheets_list:
		workshop_sessions=parse_session_data(event_program_data)
		workshop_info=parse_workshop_info(event_info_data)
		
		bytes_to_digest=bytes(google_sheet_id.encode())
		unique_hash=hashlib.sha256(bytes_to_digest).hexdigest()

		workshop_dict=dict()
		workshop_dict['Sessions']=workshop_sessions
		workshop_dict['Info']=workshop_info
		workshop_dict['unique_hash']=unique_hash
		workshop_dict['domain']=gsheets_dict[google_sheet_id]['domain']

		workshop_data[unique_hash]=workshop_dict

		continue

	try:
		seminar_series_data=get_seminar_series_data(seminar_series_data)
		domain=gsheets_dict[google_sheet_id]['domain']
		seminar_series_data['domain']=domain

		seminar_series_name=seminar_series_data['Series Name'].strip()
		if seminar_series_name=='':
			continue

		series_alias=seminar_series_name.replace(' ','-')
		series_alias=series_alias.replace('&','and')
		seminar_series_data['series_alias']=series_alias

		seminar_series[seminar_series_name]=seminar_series_data
	except:
		continue

	if fetched_status:                                                                                           
		print('>>>',seminar_series_name)

	# PARSE THE SEMINAR DATA OF THIS PARTICULAR SERIES

	header_row_number=what_is_the_header_row_number(seminar_events_data)

	if header_row_number==None:
		print('*\n'*5)
		print('!!! PANOS, I CAN\'T FIND THE HEADERS FOR THIS SPREADSHEET !!! PLEASE HAVE A LOOK : ',google_sheet_id)
		print('*\n'*5)
		continue

	headers=seminar_events_data[header_row_number]
	try:
		post_column_idx=headers.index('Post')
	except:
		try:
			post_column_idx=headers.index('Publish')
		except Exception as e:
			print('>>>Series:', seminar_series_name, ' | There is no Post or Publish column !!!', )
			pprint(e)
			continue

	headers=['Row Number']+headers
	headers.append('Seminar Series')

	seminar_rows=get_seminar_rows(seminar_events_data,header_row_number,post_column_idx)

	for x in seminar_rows:

		x.append(seminar_series_name)
		my_dict=dict(zip(headers,x))
		my_dict['sheet_id']=google_sheet_id
		my_dict['domain']=domain

		all_seminar_entries.append(my_dict)
	
	if 'McGill' in seminar_series_name and 'Neuro' in seminar_series_name:
		with open(working_dir_python_code+'scrape_utils/killam_seminar_data/seminar_data.json','r') as f:
			scraped_seminars=json.load(f)
	
		scraped_idx=0
		for x in scraped_seminars:
			scraped_idx+=1
			my_dict=x
			my_dict['hosted_by']=seminar_series_name
			my_dict['sheet_id']='SCRAPED---NO-SHEET-ID'
			my_dict['Row Number']=str(scraped_idx)
			all_seminar_entries.append(my_dict)
			#print(len(all_seminar_entries))

if if_json_file_is_not_the_same(working_dir+'/workshop_data.json',workshop_data):

	with open(working_dir+'/workshop_data.json','w') as f:
		json.dump(workshop_data,f)

	os.system('/usr/local/bin/aws s3 cp ' + working_dir + 'workshop_data.json s3://www.world-wide.org')

def kp_is_EI_balance_ab(x_title,x_abstract):

	x=x_title+' '+x_abstract
	x=x.lower()

	if 'e-i balance' in x:
		return True
	elif 'e/i balance' in x:
		return True
	elif 'excitatory / inhibitory balance' in x:
		return True
	elif 'excitation / inhibition balance' in x:
		return True
	elif 'excitatory/inhibitory balance' in x:
		return True
	elif 'excitation/inhibition balance' in x:
		return True
	elif 'excitatory & inhibitory balance' in x:
		return True
	elif 'excitation & inhibition balance' in x:
		return True
	elif 'excitatory & inhibitory balance' in x:
		return True
	elif 'excitation & inhibition balance' in x:
		return True
	elif 'excitatory - inhibitory balance' in x:
		return True
	elif 'excitation - inhibition balance' in x:
		return True
	elif 'excitatory-inhibitory balance' in x:
		return True
	elif 'excitation-inhibition balance' in x:
		return True
	elif 'e&i balance' in x:
		return True
	elif 'e - i balance' in x:
		return True
	elif 'e / i balance' in x:
		return True
	elif 'e & i balance' in x:
		return True
	elif 'ei balance' in x:
		return True
	elif 'e i balance' in x:
		return True
	else:
		return False

all_seminar_entries=[ensure_cross_sheet_compatibility(my_dict) for my_dict in all_seminar_entries]
all_world_wide_domains=list(set([item for sublist in [x['domain'] for x in all_seminar_entries] for item in sublist]))

last_updated_status=False
seminars=dict()

with open(working_dir_python_code+'seminar_speaker_unique_hash_to_seminar_id_and_date_added.pkl', 'rb') as f:
	seminar_speaker_unique_hash_to_seminar_id_and_date_added=pickle.load(f)

with open(working_dir_python_code+'seminar_ids_with_biorxiv_recommendations.pkl', 'rb') as f:
	seminar_ids_with_biorxiv_recommendations=pickle.load(f)

with open(working_dir_python_code+'seminar_id_to_domains_scores_dict.pkl', 'rb') as f:
	seminar_id_to_domains_scores_dict=pickle.load(f)

already_added_seminar_event_ids=list(seminar_speaker_unique_hash_to_seminar_id_and_date_added.values())
already_added_seminar_event_ids=list(sorted([i[0] for i in already_added_seminar_event_ids]))
already_added_unique_hashes=list(seminar_speaker_unique_hash_to_seminar_id_and_date_added.keys())

put_these_seminars_in_dynamoDB=[]

for seminar_id in already_added_seminar_event_ids:

	seminar_directory=working_dir+'seminar/' + str(seminar_id) + '/'

	if not os.path.exists(seminar_directory):
		os.makedirs(seminar_directory)

individual_ics_files_to_be_uploaded=[]

for my_dict in all_seminar_entries:

	if my_dict['hosted_by']=='IIBCE on Brain Science' and 'channel' in my_dict['seminar_link']:
		my_dict['posted']='no'
		continue

	if my_dict['seminar_speaker']=='':
		continue
	else:
		if ';;' in my_dict['seminar_speaker']:
			speakers_list=my_dict['seminar_speaker'].split(';;')
			speakers_list=[x.strip() for x in speakers_list]
			if ';;' in my_dict['speaker_affil']:
				affiliations_list=my_dict['speaker_affil'].split(';;')
				affiliations_list=[x.strip() for x in affiliations_list]

				if len(speakers_list)==len(affiliations_list):
					multiple_speakers_dict=[]
					for x in range(len(speakers_list)):
						item_dict={}
						item_dict['speaker_name']=speakers_list[x]
						item_dict['speaker_affil']=affiliations_list[x]
						multiple_speakers_dict.append(item_dict)
					my_dict['multiple_speakers']=multiple_speakers_dict


	if my_dict['hosted_by']=='Ad hoc' or my_dict['sheet_id']=='1gFDEaVKJIbB-vAO7_mttCNNDZwoBnKHnycIHWXjUkok':
		invalid_date_format=my_dict['seminar_date']
		try:
			invalid_date_format=datetime.datetime.strptime(invalid_date_format,'%m/%d/%Y')
		except:
			print('-----------> Just encountered this peculiar does not match format error !!!')
			pprint(my_dict)
			continue
		valid_date_format=datetime.datetime.strftime(invalid_date_format, '%a, %b %d, %Y')
		my_dict['seminar_date']=valid_date_format

		invalid_time_format=my_dict['seminar_time']
		am_or_pm=invalid_time_format[-2:]
		if am_or_pm=='AM':
			my_re=re.search(r'(^\d+:\d+)',invalid_time_format)
			valid_time_format=my_re.group(1)
			if len(valid_time_format)==4:
				valid_time_format='0'+valid_time_format
		else:
			my_re_hour=re.search(r'^(\d+):\d+',invalid_time_format)
			hour=my_re_hour.group(1)
			if hour!='12':
				hour=str(int(hour)+12)
			my_re_minutes=re.search(r'^\d+:(\d+)',invalid_time_format)
			minutes=my_re_minutes.group(1)
			valid_time_format=hour+':'+minutes

		my_dict['seminar_time']=valid_time_format

	my_dict['seminar_title']=my_dict['seminar_title'].rstrip('.')

	my_dict['seminar_title']=strip_quotes(my_dict['seminar_title'])
	my_dict['speaker_affil']=strip_quotes(my_dict['speaker_affil'])
	my_dict['seminar_abstract']=strip_quotes(my_dict['seminar_abstract'])
	my_dict['seminar_abstract']=remove_excess_newlines(my_dict['seminar_abstract'])
	
	#my_dict['seminar_abstract']=my_dict['seminar_abstract'].replace(' suggesting competition between cortical areas for functional role. According to ',' suggesting competition between cortical areas for functional role. According to P')
	my_dict['topic_tags']=my_dict['topic_tags'].replace(';',',')

	'''try:
		if 'crowdcast' in my_dict['seminar_link'] and my_dict['video_on_demand']=='':
			my_dict['video_on_demand']=my_dict['seminar_link']
	except:
		pass'''

	unique_hash,seminar_id,time_of_addition=get_unique_hash(my_dict)

	if str(seminar_id)=='1062' and my_dict['seminar_speaker']=='Sara Solla':
		related_material_obj_1=dict()
		related_material_obj_1['title']='Canonical Correlation Analysis (CCA) tutorial'
		related_material_obj_1['url']='https://www.world-wide.org/i/b2cdbc5e-f76e-4e7b-8b8b-541817563a76.pdf'
		related_material_obj_2=dict()
		related_material_obj_2['title']='Github code for the tutorial'
		related_material_obj_2['url']='https://github.com/jbakermans/ManifoldTutorial/'
		my_dict['Related Material']=[related_material_obj_1,related_material_obj_2]

	if time_of_addition==None:

		seminar_id=max(already_added_seminar_event_ids)+1
		already_added_seminar_event_ids.append(seminar_id)
		time_of_addition=str(datetime.datetime.now().strftime("%a, %b %d, %Y %H:%M"))

	seminar_directory=working_dir+'seminar/' + str(seminar_id) + '/'

	my_dict=add_unix_timestamp(my_dict)
	my_dict['partition_key']=str(seminar_id)

	if not os.path.exists(seminar_directory):
		os.makedirs(seminar_directory)

	if not os.path.isfile(working_dir_python_code+'html_templates/seminar_page.html'):
		shutil.copy(working_dir_python_code+'html_templates/seminar_page.html',seminar_directory+'index.html')
		os.system('/usr/local/bin/aws s3 cp ' + seminar_directory + 'index.html s3://www.world-wide.org/seminar/' + str(seminar_id) + '/index.html')

	my_dict['calendar_event_hash']=unique_hash

	seminar_speaker_unique_hash_to_seminar_id_and_date_added[unique_hash]=[seminar_id,time_of_addition]

	if unique_hash in seminars_matching_data:
		my_dict['matching_data']=seminars_matching_data[unique_hash]
	else:
		my_dict['matching_data']=None

	my_dict['seminar_id']=seminar_id

	if seminar_id in seminar_id_to_domains_scores_dict:
		my_dict['domains_scores']=seminar_id_to_domains_scores_dict[seminar_id]
	else:
		my_dict['domains_scores']=[]

	if str(seminar_id)=='6327':
		my_dict['domain']=my_dict['domain']+['Artificial Intelligence']
	my_dict['time_of_addition']=time_of_addition
	speaker_twitter=my_dict['speaker_twitter']
	if 'twitter.com/' in speaker_twitter:
		if '#' not in speaker_twitter:
			speaker_twitter=speaker_twitter.split('twitter.com/')
			speaker_twitter='@'+speaker_twitter[-1]
			my_dict['speaker_twitter']=speaker_twitter
		else:
			speaker_twitter=speaker_twitter.split('twitter.com/')
			speaker_twitter='search?q=%23'+speaker_twitter[-1]
			my_dict['speaker_twitter']=speaker_twitter
	
	auto_keywords=add_automatically_extracted_keywords(unique_hash)

	if 'brain prize' in my_dict['hosted_by'].lower() or 'NeuroPhilosophy of Free Will'==my_dict['hosted_by']:
		auto_keywords=[]

	'''try:
		what_language=detect(seminar_text)
	except:
		what_language=None

	if what_language=='es':
		auto_keywords.append('Spanish 🗣️')'''

	check_if_domain_tags_and_colors_are_loaded_otherwise_load_them(my_dict['domain'])
	
	if kp_is_EI_balance_ab(my_dict['seminar_title'],my_dict['seminar_abstract']):
		my_dict['topic_tags']=['E/I balance']+decapitalize_seminar_tags(my_dict['topic_tags'],auto_keywords,my_dict['domain'])
	else:
		my_dict['topic_tags']=decapitalize_seminar_tags(my_dict['topic_tags'],auto_keywords,my_dict['domain'])

	'''if 'machine learning' in my_dict['topic_tags'] or 'deep learning' in my_dict['topic_tags']:
		
		seminar_domains=my_dict['domain']
		if 'Machine Learning' not in seminar_domains:
			seminar_domains.append('Machine Learning')
			my_dict['domain']=seminar_domains'''
			
	'''try:
		this_series_color=get_series_color(my_dict['hosted_by'],my_dict['domain'])
		if this_series_color!=None:
			my_dict['series_color']=this_series_color
			#print('A',this_series_color,my_dict['hosted_by'])
		else:
			my_dict['series_color']='#ffbc39'
			#print('B',None,my_dict['hosted_by'])
	except:
		my_dict['series_color']='#ffbc39'
		#print('C','error!!!!',my_dict['hosted_by'])'''

	if 'Event Duration' in my_dict:
		if my_dict['Event Duration']!='':
			duration_info=re.findall(r'(\d+)', my_dict['Event Duration'])
			try:
				my_dict['Event Duration']=int(duration_info[0])
			except:
				pass
		else:
			my_dict['Event Duration']=70.000025
	else:
		if my_dict['hosted_by']=='Learning Salon':
			my_dict['Event Duration']=150
		else:
			my_dict['Event Duration']=70.000025

	#my_dict['Event Duration']=float(my_dict['Event Duration'])

	slink=my_dict['speaker_website'].lower().strip()
	if len(slink)>=5 and ' ' not in slink:
		if not slink.startswith('www') and not slink.startswith('http'):
			my_dict['speaker_website']='http://'+my_dict['speaker_website']

	seminar_text=my_dict['seminar_title']+' '+my_dict['seminar_abstract']

	if 'Banner Ad' in my_dict:
		banner_ad=my_dict['Banner Ad']
		if my_dict['hosted_by']=='Neuromatch 4':
			my_dict.pop('Banner Ad', None)
		# if banner ad is not a valid url
		elif not re.match(r'^(?:http|ftp)s?://', banner_ad):
			my_dict.pop('Banner Ad', None)
		else:
			banner_ad=my_dict['Banner Ad']
			if len(banner_ad)>=5:
				if img_is_hosted_on_gdrive(banner_ad):
					try:
						file_id=get_file_id_from_gdrive_url(banner_ad)
						if file_id in gdrive_img_urls_to_world_wide_path:
							banner_ad=gdrive_img_urls_to_world_wide_path[file_id]
							my_dict['Banner Ad']=banner_ad
					except:
						pass
						#print('error',my_dict['Banner Ad'])
				elif img_is_hosted_on_twitter(banner_ad):
					try:
						if '?format=' not in banner_ad:
							banner_ad=banner_ad+'?format=png'
							my_dict['Banner Ad']=banner_ads
					except:
						pass
						#print('error',my_dict['Banner Ad'])
				else:
					try:
						banner_ad=transform_github_urls(banner_ad)
						my_dict['Banner Ad']=banner_ad
					except:
						pass
	
	my_dict.pop('sheet_id', None)
	my_dict.pop('Row Number', None)
	my_dict.pop('Timestamp', None)
	my_dict.pop('Email Address', None)
	my_dict.pop('Email', None)
	my_dict.pop('Contact Address', None)
	my_dict.pop('Review Status', None)
	my_dict.pop('Is there ', None)
	my_dict.pop('', None)
	my_dict['item_type']='seminar'

	my_domains=[]

	try:
		for my_domain in my_dict['domain']:
			my_domains.append(my_domain)
	except:
		pass

	try:
		for my_domain in my_dict['domains_scores']:
			my_domain=my_domain['sci-field']
			if my_domain not in my_domains:
				my_domains.append(my_domain)
	except:
		pass

	my_dict['domains']=my_domains

	if seminar_id in seminar_ids_with_biorxiv_recommendations:
		my_dict['biorxiv_rec']=True
	else:
		my_dict['biorxiv_rec']=False

	ical_event_string,this_event=create_ical_file(my_dict,unique_hash)

	ics_status=check_if_calendar_file_exists_and_is_unchanged(ical_event_string,seminar_id)
	if ics_status!='same':
		ics_fname=seminar_directory + 'seminar_event.ics'
		website_ics_fname='s3://www.world-wide.org/seminar/' + str(seminar_id) + '/seminar_event.ics'
		individual_ics_files_to_be_uploaded.append([ics_fname,website_ics_fname])
		
		with open(ics_fname,'w') as f:
			f.write(ical_event_string)

	try:

		if if_json_file_is_not_the_same_or_doesnt_exist(seminar_directory+'seminar_data.json',my_dict,True):

			put_these_seminars_in_dynamoDB.append(str(seminar_id))

			last_updated_status=True

			print('This seminar is new or has changed and I will upload it:', seminar_id)
			print(my_dict['seminar_speaker'],my_dict['seminar_title'])

			with open(seminar_directory+'seminar_data.json','w') as f:
				json.dump(my_dict,f)

			os.system('/usr/local/bin/aws s3 cp ' + seminar_directory + 'seminar_data.json s3://www.world-wide.org/seminar/' + str(seminar_id) + '/seminar_data.json')

	except:

		print('There seems to be a problem with this seminar:', seminar_id,'so I will try to see if it is due to a problem with the directory ({}) not existing just yet'.format(seminar_directory))

		if not os.path.exists(seminar_directory):
			os.makedirs(seminar_directory)

		put_these_seminars_in_dynamoDB.append(str(seminar_id))

		with open(seminar_directory+'seminar_data.json','w') as f:
			json.dump(my_dict,f)

		os.system('/usr/local/bin/aws s3 cp ' + seminar_directory + 'seminar_data.json s3://www.world-wide.org/seminar/' + str(seminar_id) + '/seminar_data.json')
	
	# put_these_seminars_in_dynamoDB.append(str(seminar_id))
	seminars[seminar_id]=my_dict

with open(working_dir_python_code+'seminar_speaker_unique_hash_to_seminar_id_and_date_added.pkl', 'wb') as f:
	pickle.dump(seminar_speaker_unique_hash_to_seminar_id_and_date_added,f)

# UPLOAD seminars_data.json & flexsearch_index.json IF SEMINARS DATA HAVE CHANGED

if if_json_file_is_not_the_same(working_dir+'seminar_data.json',seminars):

	with open(working_dir+'seminar_data.json','w') as f:
		json.dump(seminars,f)

	os.system('/usr/local/bin/aws s3 cp ' + working_dir + 'seminar_data.json s3://www.world-wide.org')

# all seminar_id keys in the local json file
all_seminar_ids=[x['seminar_id'] for x in seminars.values()]

# UPLOAD seminars_series_data.json IF SEMINAR SERIES DATA HAVE CHANGED

import botocore

# Get the service resource
dynamodb = boto3.resource(
		'dynamodb',
		###
	)

dynamodb_client = boto3.client(
	'dynamodb',
	###
)

ww_seminars_table = dynamodb.Table('world-wide-seminars')
batch_size=25

update_dynamoDB_table_write_capacity(increase_or_decrease_dynamoDB_write_capacity)

if time_to_sync_all_seminars_to_dynamoDB_boolean:
	print('I will sync all seminars to dynamoDB')
	put_these_seminars_in_dynamoDB=all_seminar_ids

try:
	if len(put_these_seminars_in_dynamoDB)>0:
		print('I will put these seminars in the dynamoDB table: ' + str(put_these_seminars_in_dynamoDB))
		put_to_dynamoDB(put_these_seminars_in_dynamoDB,ww_seminars_table)
except:
	print('I could not put these seminars in the dynamoDB table: ' + str(put_these_seminars_in_dynamoDB))
	print('Please inspect the error message above')
	
def get_seminar_datetime(x):
	seminar_timezone=pytz.timezone(x['timezone'])
	start_datetime=parse(x['seminar_date'] + ' ' + x['seminar_time'], fuzzy=True)
	end_datetime=start_datetime+datetime.timedelta(hours=2136)
	end_datetime = seminar_timezone.localize(end_datetime).astimezone(pytz.UTC)

	return end_datetime

def which_seminar_series_are_still_active(seminar_series):

	for this_series in seminar_series:
		these_seminars=[x for x in seminars.values() if x['hosted_by']==this_series]
		future_seminars=[x for x in these_seminars if get_seminar_datetime(x)>datetime_now]
		if len(future_seminars)==0:
			seminar_series[this_series]['active']=False
		else:
			seminar_series[this_series]['active']=True

	return seminar_series

def which_seminar_series_contain_seminars(seminar_series):

	pop_these_series_out=[]
	for this_series in seminar_series:
		if len([x for x in seminars.values() if x['hosted_by']==this_series])==0:
			pop_these_series_out.append(this_series)

	for this_series in pop_these_series_out:
		seminar_series.pop(this_series, None)
			
	return seminar_series

seminar_series=which_seminar_series_contain_seminars(seminar_series)
seminar_series=which_seminar_series_are_still_active(seminar_series)

try:
	with open(working_dir+'seminar_series_data.json','r') as f:
		old_seminar_series=json.load(f)

	if old_seminar_series!=seminar_series:

		with open(working_dir+'seminar_series_data.json','w') as f:
			json.dump(seminar_series,f)

		os.system('/usr/local/bin/aws s3 cp ' + working_dir + 'seminar_series_data.json s3://www.world-wide.org')
except:
	with open(working_dir+'seminar_series_data.json','w') as f:
			json.dump(seminar_series,f)

	os.system('/usr/local/bin/aws s3 cp ' + working_dir + 'seminar_series_data.json s3://www.world-wide.org')

# UPLOAD INDIVIDUAL CALENDAR FILES THAT HAVE BEEN MARKED AS NEW OR CHANGED

for ifn in individual_ics_files_to_be_uploaded:
	os.system('/usr/local/bin/aws s3 cp ' + ifn[0] + ' ' + ifn[1])

for seminar_id in seminars:

	seminar_directory=working_dir+'seminar/' + str(seminar_id) + '/'

	if not os.path.exists(seminar_directory):
		os.makedirs(seminar_directory)

	if not os.path.isfile(seminar_directory+'index.html'):
		create_the_seminar_index_page(seminar_id)

current_date_time=str(datetime.datetime.now())
print(current_date_time)

if last_updated_status:

	now = datetime.datetime.utcnow()

	with open('last_updated.pkl', 'wb') as f:
		pickle.dump(now,f)
