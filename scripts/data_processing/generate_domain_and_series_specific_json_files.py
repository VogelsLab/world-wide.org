import os,sys,re,pickle,json,datetime,pytz,math,random,boto3,time,copy
from unidecode import unidecode
from dateutil.parser import parse
from pprint import pprint
from pathlib import Path
from collections import Counter,OrderedDict
from deepdiff import DeepDiff

import numpy as np

from icalendar import Calendar, Event

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
		items=[dynamoDB_data_to_be_put[x] for x in primary_keys]
		items=[json.loads(json.dumps(x), parse_float=Decimal) for x in items]
		return items
	else:
		item=dynamoDB_data_to_be_put[primary_keys]
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

def open_and_read_reference_json_file(ref_fname):

	try:
		with open(ref_fname,'r') as f:
			example_json=json.load(f)
	except:
		return None

	return example_json

def myround(x,base):
	return float(base*round(x/base))

def if_json_file_is_not_the_same(ref_fname, target_json):
	
	example_json=open_and_read_reference_json_file(ref_fname)
	if example_json==None:
		return True

	different_variables=len(DeepDiff(example_json, target_json, ignore_order=True))

	if different_variables==0:
		return False
	else:
		different_variables=parseJSON(example_json, target_json)
		#print('different_variables:',different_variables)
		#print(DeepDiff(example_json, target_json, ignore_order=True))
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

def new_parse_date(seminar_date,seminar_time,seminar_timezone,seminar_duration):

	seminar_timezone=pytz.timezone(seminar_timezone)

	start_datetime=parse(seminar_date + ' ' + seminar_time, fuzzy=True)
	end_datetime=start_datetime+datetime.timedelta(minutes=seminar_duration)

	start_datetime = seminar_timezone.localize(start_datetime).astimezone(pytz.UTC)
	end_datetime = seminar_timezone.localize(end_datetime).astimezone(pytz.UTC)
	
	return start_datetime,end_datetime

def upcoming_num_or_archived_num_is_changed(json_fname,upcoming_num,archived_num):
	try:
		with open(json_fname,'r') as f:
			old_json_data=json.load(f)

		if old_json_data[1][0]!=upcoming_num or old_json_data[1][1]!=archived_num:
			return True
		else:
			return False
	except:
		return True

def if_ics_file_is_not_the_same_or_doesnt_exist(ics_fname,new_ics_string):
	try:
		with open(ics_fname,'r') as f:
			old_ics_string=f.read()

		if sorted(old_ics_string.splitlines())!=sorted(new_ics_string.splitlines()):
			return True
		else:
			return False
	except:
		return True

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
	
'''def split_trim(x):
	x=[i.strip() for i in x.split(',')]
	x=[i for i in x if i!='']
	return x'''

def get_top_topic_tags_if_they_exist():
	return None

def get_topic_tags_to_colors(domain_seminar_data):
	
	topic_tags=[x['topic_tags'] for x in domain_seminar_data.values()]
	topic_tags=sorted([item for sublist in topic_tags for item in sublist])
	topic_tags_counter=Counter(topic_tags)
	
	topic_tags=sorted(topic_tags_counter.items(), key=lambda item: (-item[1], item[0]))
	#topic_tags=[[k,v] for k,v in topic_tags_counter.items()]
	topic_tags=sorted(topic_tags, key = lambda x: x[1], reverse=True)
	topic_tags=[x[0] for x in topic_tags]
		
	top_topic_tags_to_colors = dict()
	number_of_topic_tags_to_show=34

	if len(topic_tags)<=number_of_topic_tags_to_show:
		number_of_topic_tags_to_show=len(topic_tags)

	step = len(topics_colormap) / number_of_topic_tags_to_show
	
	non_eq_add=0.00000001
	for i in range(number_of_topic_tags_to_show):

		top_topic_tags_to_colors[topic_tags[i]]=dict()
		top_topic_tags_to_colors[topic_tags[i]]['noc']=topic_tags_counter[topic_tags[i]]-non_eq_add
		non_eq_add+=0.00000001
		top_topic_tags_to_colors[topic_tags[i]]['color']=topics_colormap[math.floor(i*step)]
							
	top_topic_tags_to_colors['all']=dict()
	top_topic_tags_to_colors['all']['noc']=99999999
	top_topic_tags_to_colors['all']['color']='#c9c9c9'

	if 'Spanish 🗣️' in topic_tags_counter:

		top_topic_tags_to_colors['Spanish 🗣️']=dict()
		top_topic_tags_to_colors['Spanish 🗣️']['noc']=99000000
		top_topic_tags_to_colors['Spanish 🗣️']['color']='#ff8e75'

	topic_tags_to_colors = dict()
	number_of_topic_tags_to_show=len(topic_tags)

	step = len(topics_colormap) / number_of_topic_tags_to_show
	
	non_eq_add=0.00000001
	for i in range(len(topic_tags)):

		topic_tags_to_colors[topic_tags[i]]=dict()
		topic_tags_to_colors[topic_tags[i]]['noc']=topic_tags_counter[topic_tags[i]]-non_eq_add
		non_eq_add+=0.00000001
		topic_tags_to_colors[topic_tags[i]]['color']=topics_colormap[math.floor(i*step)]

	if 'Spanish 🗣️' in topic_tags_counter:

		topic_tags_to_colors['Spanish 🗣️']=dict()
		topic_tags_to_colors['Spanish 🗣️']['noc']=99000000
		topic_tags_to_colors['Spanish 🗣️']['color']='#ff8e75'

	top_topic_tags_to_colors=OrderedDict(sorted(top_topic_tags_to_colors.items(), key=lambda k : k))
	topic_tags_to_colors=OrderedDict(sorted(topic_tags_to_colors.items(), key=lambda k : k))

	return top_topic_tags_to_colors,topic_tags_to_colors

def get_series_tags_to_colors(domain_seminar_series_data):
	
	sorted_scored_seminar_series=rank_seminar_series(domain_seminar_series_data)
	series_score_dict={ k:v for k,v in sorted_scored_seminar_series}
	series_tags=[x[0] for x in sorted_scored_seminar_series]

	top_series_tags_to_colors = dict()
	number_of_series_tags_to_show=18

	if len(series_tags)<=number_of_series_tags_to_show:
		number_of_series_tags_to_show=len(series_tags)

	step = len(series_colormap) / number_of_series_tags_to_show
			
	for i in range(number_of_series_tags_to_show):

		top_series_tags_to_colors[series_tags[i]]=dict()
		top_series_tags_to_colors[series_tags[i]]['score']=float(myround(series_score_dict[series_tags[i]],0.0005)) 
		top_series_tags_to_colors[series_tags[i]]['color']=series_colormap[math.floor(i*step)]

	series_tags_to_colors=dict()
	number_of_series_tags_to_show=len(series_tags)
	step = len(series_colormap) / number_of_series_tags_to_show
			
	for i in range(number_of_series_tags_to_show):
		series_tags_to_colors[series_tags[i]]=dict()
		series_tags_to_colors[series_tags[i]]['score']=float(myround(series_score_dict[series_tags[i]],0.0005))
		series_tags_to_colors[series_tags[i]]['color']=series_colormap[math.floor(i*step)]

	#top_series_tags_to_colors=OrderedDict(sorted(top_series_tags_to_colors.items(), key=lambda k : k))
	#series_tags_to_colors=OrderedDict(sorted(series_tags_to_colors.items(), key=lambda k : k))

	return top_series_tags_to_colors,series_tags_to_colors

def future_ok_but_past_with_stream_available(v):

	if v['hosted_by']=='Ad hoc':
		return False

	if get_seminar_datetime(v)>datetime_now:
		return True
	else:
		if len(v['video_on_demand'])>5:
			return True
		else:
			return False

def create_topic_tag_pages(topic_tags_to_colors,series_name):

	past_seminars=[[x,get_seminar_datetime(x)] for x in domain_seminar_data.values()]
	past_seminars_topic_tags=[[x,x[0]['topic_tags']] for x in past_seminars if x[1] <= datetime_now and future_ok_but_past_with_stream_available(x[0])]

	topic_tags_for_pages=[]
	for k,v in topic_tags_to_colors.items():
		if v['noc']>=3 and len([True for x in past_seminars_topic_tags if k in x[1]])>=2:
			if k.lower() not in [domain_name.lower(),domain_nickname.lower()] and 'Spanish' not in k:
				topic_tags_for_pages.append(k)

	topic_tag_related_seminar_data=dict()

	if if_json_file_is_not_the_same(domain_dir+'/topic_tags_with_pages.json',topic_tags_for_pages):

		with open(domain_dir+'/topic_tags_with_pages.json','w') as f:
			json.dump(topic_tags_for_pages,f)

		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'topic_tags_with_pages.json s3://www.world-wide.org/'+domain_alias+'/topic_tags_with_pages.json')

	topic_aliases=dict()
	for k in topic_tags_for_pages:

		topic_tag_alias=k.lower().replace(' ','-')
		topic_tag_alias=topic_tag_alias.replace("'",'')
		topic_tag_alias=topic_tag_alias.replace("/",'-')
		topic_tag_alias=topic_tag_alias.replace('&','and')

		if k!=topic_tag_alias:
			topic_aliases[k]=topic_tag_alias

	if if_json_file_is_not_the_same(domain_dir+'/topic_aliases.json',topic_aliases):

		with open(domain_dir+'/topic_aliases.json','w') as f:
			json.dump(topic_aliases,f)

		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'topic_aliases.json s3://www.world-wide.org/'+domain_alias+'/topic_aliases.json')

	for x in topic_tags_for_pages:

		sdata={k:v for k,v in domain_seminar_data.items() if x in v['topic_tags'] and future_ok_but_past_with_stream_available(v)}

		my_matching_seminars=list(set([i['calendar_event_hash'] for i in sdata.values()]))
		matching_seminars=[]
		for i in my_matching_seminars:
			try:
				matching_seminars.append(seminars_matching_data[i]['matching_seminars'])
			except:
				pass
		matching_seminars=[[ii['url'].split('/')[-1] for ii in i] for i in matching_seminars]
		matching_seminars=list(set([item for sublist in matching_seminars for item in sublist]))
		matching_seminars=[i for i in matching_seminars if i not in sdata.keys()]
		matching_seminars={i:seminar_data[i] for i in matching_seminars if get_seminar_datetime(seminar_data[i])<datetime_now}
		
		topic_tag_related_seminar_data[x]=[sdata,matching_seminars]

	for k,v in topic_tag_related_seminar_data.items():

		topic_tag_alias=k.lower().replace(' ','-')
		topic_tag_alias=topic_tag_alias.replace("'",'')
		topic_tag_alias=topic_tag_alias.replace("/",'-')
		topic_tag_alias=topic_tag_alias.replace('&','and')

		about_this_topic=dict()
		about_this_topic['topic_tag_name']=k
		about_this_topic['topic_tag_alias']=topic_tag_alias
		about_this_topic['seminars_num']=len(v[0])
		about_this_topic['matching_seminars_num']=len(v[1])
		about_this_topic['domain_name']=domain_name
		about_this_topic['domain_alias']=domain_alias

		topic_tag_dir=domain_dir+'topic/'+topic_tag_alias+'/'
		topic_tag_dir_wo_domain_dir='topic/'+topic_tag_alias+'/'

		if not os.path.exists(topic_tag_dir):
			os.makedirs(topic_tag_dir)

		if if_json_file_is_not_the_same(topic_tag_dir+'about_this_topic.json',about_this_topic):

			with open(topic_tag_dir+'about_this_topic.json','w') as f:
				json.dump(about_this_topic,f)
			
			os.system('/usr/local/bin/aws s3 cp ' + topic_tag_dir + 'about_this_topic.json s3://www.world-wide.org/'+domain_alias+'/'+topic_tag_dir_wo_domain_dir+'about_this_topic.json')

		if if_json_file_is_not_the_same(topic_tag_dir+'seminar_data.json',v[0]):

			with open(topic_tag_dir+'seminar_data.json','w') as f:
				json.dump(v[0],f)
			
			os.system('/usr/local/bin/aws s3 cp ' + topic_tag_dir + 'seminar_data.json s3://www.world-wide.org/'+domain_alias+'/'+topic_tag_dir_wo_domain_dir+'seminar_data.json')

		if if_json_file_is_not_the_same(topic_tag_dir+'matching_seminars.json',v[1]):

			with open(topic_tag_dir+'matching_seminars.json','w') as f:
				json.dump(v[1],f)
			
			os.system('/usr/local/bin/aws s3 cp ' + topic_tag_dir + 'matching_seminars.json s3://www.world-wide.org/'+domain_alias+'/'+topic_tag_dir_wo_domain_dir+'matching_seminars.json')

		if not os.path.exists(topic_tag_dir+'/index.html'):
			with open(topic_tag_dir+'/index.html','w') as f:
				f.write(topic_page_template)
			os.system('/usr/local/bin/aws s3 cp ' + topic_tag_dir+'/index.html s3://www.world-wide.org/'+domain_alias+'/'+topic_tag_dir_wo_domain_dir+'index.html')

def get_seminar_datetime(x):
	seminar_timezone=pytz.timezone(x['timezone'])
	start_datetime=parse(x['seminar_date'] + ' ' + x['seminar_time'], fuzzy=True)	
	start_datetime = seminar_timezone.localize(start_datetime).astimezone(pytz.UTC)
	return start_datetime

def get_series_seminars(x):
	this_series_seminars=[v for v in seminar_data.values() if v['hosted_by']==x]
	return this_series_seminars

def score_seminar_series(series_name):

	series_seminars=get_series_seminars(series_name)

	if len(series_seminars)==0:
		return None

	seminar_datetimes=[get_seminar_datetime(x) for x in series_seminars]
	past_seminar_datetimes=sorted([x for x in seminar_datetimes if x <= datetime_now], reverse=True)
	future_seminar_datetimes=sorted([x for x in seminar_datetimes if x > datetime_now], reverse=True)

	time_since=[get_seminar_datetime(x)-datetime_now for x in series_seminars]
	try:
		days_since_first_seminar=-1*sorted([(x.days) for x in time_since])[0]
	except:
		days_since_first_seminar=None

	try:
		days_since_last_seminar=datetime_now-past_seminar_datetimes[0]
		days_since_last_seminar=days_since_last_seminar.days
	except:
		days_since_last_seminar=-365

	longest_past_streak=0
	for i in range(len(past_seminar_datetimes)-1):
		time_diff=past_seminar_datetimes[i]-past_seminar_datetimes[i+1]
		if time_diff.days<=98:
			longest_past_streak+=time_diff.days
		else:
			break
	
	number_of_future_seminars=len([x for x in seminar_datetimes if x > datetime_now])
	number_of_past_seminars=len([x for x in seminar_datetimes if x <= datetime_now])
	number_of_total_seminars=len(seminar_datetimes)

	open_stream_platforms=['zoom.us','crowdcast.io','youtu','webex','vimeo']

	past_series_seminars=[x for x in series_seminars if get_seminar_datetime(x) <= datetime_now]
	past_seminar_links=len(past_series_seminars)
	open_seminar_links=len([x for x in past_series_seminars if any([True for i in open_stream_platforms if i in x['seminar_link'].lower()])])

	try:
		open_stream_score=open_seminar_links/past_seminar_links
	except:
		open_stream_score=0

	try:
		rewatch_score=len([x for x in past_series_seminars if len(x['video_on_demand'])>5])/past_seminar_links
	except:
		rewatch_score=0

	try:
		abstract_availability_score=len([x for x in past_series_seminars if len(x['seminar_abstract'])>150])/past_seminar_links
	except:
		abstract_availability_score=0

	return series_name,days_since_first_seminar,days_since_last_seminar,longest_past_streak,number_of_past_seminars,number_of_future_seminars,number_of_total_seminars,open_stream_score,rewatch_score,abstract_availability_score

def normalize_between_zero_and_one(arr):
	arr=np.array(arr)
	max_min_subtraction=np.max(arr) - np.min(arr)
	if max_min_subtraction!=0:
		norm_arr=list((arr - np.min(arr)) / ( max_min_subtraction ))
	else:
		norm_arr=[0 for z in arr]
	return norm_arr

def calculate_series_score(x):

	a=x['days_since_first_seminar']*7
	b=x['days_since_last_seminar']*9
	c=x['longest_past_streak']*10
	d=x['number_of_past_seminars']*5
	e=x['number_of_future_seminars']*5
	f=x['number_of_total_seminars']*7
	g=x['open_stream_score']*14
	h=x['rewatch_score']*11
	i=x['abstract_availability_score']*6

	return a+b+c+d+e+f+g+h+i

def rank_seminar_series(domain_seminar_series_data):

	if len(domain_seminar_series_data)==1:
		return [[list(domain_seminar_series_data.keys())[0],1]]
	if len(domain_seminar_series_data)==0:
		return [[None,None]]

	metrics=[score_seminar_series(x) for x in domain_seminar_series_data]
	metrics=[x for x in metrics if x!=None]
	
	days_since_first_seminar_scores=normalize_between_zero_and_one([x[1] for x in metrics])
	days_since_last_seminar_scores=normalize_between_zero_and_one([1/(x[2]+1) for x in metrics])
	longest_past_streak_scores=normalize_between_zero_and_one([x[3] for x in metrics])
	number_of_past_seminars_scores=normalize_between_zero_and_one([x[4] for x in metrics])
	number_of_future_seminars_scores=normalize_between_zero_and_one([x[5] for x in metrics])
	number_of_total_seminars_scores=normalize_between_zero_and_one([x[6] for x in metrics])

	domain_seminar_series_metrics=dict()

	for i in range(len(metrics)):
		
		my_dict=dict()

		my_dict['days_since_first_seminar']=days_since_first_seminar_scores[i]
		my_dict['days_since_last_seminar']=days_since_last_seminar_scores[i]
		my_dict['longest_past_streak']=longest_past_streak_scores[i]
		my_dict['number_of_past_seminars']=number_of_past_seminars_scores[i]
		my_dict['number_of_future_seminars']=number_of_future_seminars_scores[i]
		my_dict['number_of_total_seminars']=number_of_total_seminars_scores[i]
		my_dict['open_stream_score']=metrics[i][7]
		my_dict['rewatch_score']=metrics[i][8]
		my_dict['abstract_availability_score']=metrics[i][9]

		domain_seminar_series_metrics[metrics[i][0]]=my_dict

	scored_seminar_series=[[k,calculate_series_score(v)] for k,v in domain_seminar_series_metrics.items()]
	sorted_scored_seminar_series=sorted(scored_seminar_series, key=lambda x:x[1], reverse=True)

	return sorted_scored_seminar_series

def get_N_immediately_upcoming_domain_seminars(domain_seminar_data):

	mini_num=21

	mini_domain_seminar_data=[[k,v] for k,v in domain_seminar_data.items() if get_seminar_datetime(v)>=datetime_an_hour_ago]
	mini_domain_seminar_data=sorted(mini_domain_seminar_data, key=lambda x:get_seminar_datetime(x[1]))[:mini_num]
	mini_domain_seminar_data={x[0]:x[1] for x in mini_domain_seminar_data}

	if len(mini_domain_seminar_data)<mini_num:
		mini_domain_seminar_data=[[k,v] for k,v in domain_seminar_data.items()]
		mini_domain_seminar_data=sorted(mini_domain_seminar_data, key=lambda x:get_seminar_datetime(x[1]),reverse=True)[:mini_num]
		mini_domain_seminar_data={x[0]:x[1] for x in mini_domain_seminar_data}
		
	return mini_domain_seminar_data

def get_how_many_upcoming_archived(domain_seminar_data):

	upcoming_num=len([k for k,v in domain_seminar_data.items() if get_seminar_datetime(v)>=datetime_an_hour_ago])
	archived_num=len([k for k,v in domain_seminar_data.items() if get_seminar_datetime(v)<datetime_an_hour_ago])

	#print(domain_name,upcoming_num,archived_num)
	
	return [upcoming_num,archived_num]

def create_ical_file(my_dict):

	unique_hash=my_dict['calendar_event_hash']

	seminar_date=my_dict['seminar_date']
	seminar_time=my_dict['seminar_time']

	seminar_timezone=my_dict['timezone']
	seminar_duration=int(my_dict['Event Duration'])

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

	event = Event()

	event['uid']=unique_hash
	event.add('summary', event_summary)
	event.add('description', event_description)
	event.add('dtstart',start_datetime)
	event.add('dtend',end_datetime)
	
	return event

def get_series_specific_calendar(series_dir,aws_s3_series_dir,series_specific_seminar_data):

	series_ical=Calendar()

	for this_seminar in series_specific_seminar_data.values():
		this_event=create_ical_file(this_seminar)
		series_ical.add_component(this_event)

	icalendar=str(series_ical.to_ical(),'utf-8').strip()

	try:
		with open(series_dir +'seminars_ical.ics','r') as f:
			old_icalendar=f.read()

		if sorted(old_icalendar.splitlines())!=sorted(icalendar.splitlines()):

			with open(series_dir +'seminars_ical.ics','w') as f:
				f.write(icalendar)

			os.system('/usr/local/bin/aws s3 cp ' + series_dir + 'seminars_ical.ics ' + aws_s3_series_dir + 'seminars_ical.ics')

	except:
		with open(series_dir +'seminars_ical.ics','w') as f:
			f.write(icalendar)

		os.system('/usr/local/bin/aws s3 cp ' + series_dir + 'seminars_ical.ics ' + aws_s3_series_dir + 'seminars_ical.ics')


def get_domain_specific_calendar(domain_name,domain_seminar_data):

	domain_ical=Calendar()

	for this_seminar in domain_seminar_data.values():

		this_event=create_ical_file(this_seminar)
		domain_ical.add_component(this_event)

	icalendar=str(domain_ical.to_ical(),'utf-8').strip()

	try:
		with open(domain_dir +'seminars_ical.ics','r') as f:
			old_icalendar=f.read()

		if sorted(old_icalendar.splitlines())!=sorted(icalendar.splitlines()):

			with open(domain_dir +'seminars_ical.ics','w') as f:
				f.write(icalendar)

			os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'seminars_ical.ics s3://www.world-wide.org/'+domain_alias+'/seminars_ical.ics')

			if domain_alias=='Neuro':
				os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'seminars_ical.ics s3://www.worldwideneuro.com/seminars_ical.ics')

	except:
		with open(domain_dir +'seminars_ical.ics','w') as f:
			f.write(icalendar)

		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'seminars_ical.ics s3://www.world-wide.org/'+domain_alias+'/seminars_ical.ics')

		if domain_alias=='Neuro':
			os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'seminars_ical.ics s3://www.worldwideneuro.com/seminars_ical.ics')

def pick_random_meta_card_and_save_it_in_the_newly_created_series_directory():

	try:
		meta_cards_dir=domain_dir+'/meta_cards/'
		meta_cards=[x for x in os.listdir(meta_cards_dir) if x[0]!='.']
		random_meta_card=random.choice(meta_cards)
		series_banner='https://www.world-wide.org/'+domain_alias+'/meta_cards/'+random_meta_card
		print(domain_alias)
	except:
		series_banner='https://www.world-wide.org/banner.jpg'

	return series_banner

def get_domain_upcoming_and_archive_seminar_data(domain_alias,domain_seminar_data):

	upcoming_seminar_data=[[k,v] for k,v in domain_seminar_data.items() if get_seminar_datetime(v)>=datetime_an_hour_ago]
	upcoming_seminar_data=sorted(upcoming_seminar_data, key=lambda x:get_seminar_datetime(x[1]))
	upcoming_seminar_ids=[x[0] for x in upcoming_seminar_data]

	paginated_upcoming_seminar_ids=paginate_seminar_ids(domain_alias,'upcoming',upcoming_seminar_ids,20)

	upcoming_seminar_data={x[0]:x[1] for x in upcoming_seminar_data}
		
	archive_seminar_data=[[k,v] for k,v in domain_seminar_data.items() if get_seminar_datetime(v)<datetime_an_hour_ago]
	archive_seminar_data=[asd for asd in archive_seminar_data if 'video_on_demand' in asd[1]]
	archive_seminar_data=[asd for asd in archive_seminar_data if len(asd[1]['video_on_demand'])>4]
	archive_seminar_data=sorted(archive_seminar_data, key=lambda x:get_seminar_datetime(x[1]), reverse=True)
	archive_seminar_ids=[x[0] for x in archive_seminar_data]
	
	paginated_archive_seminar_ids=paginate_seminar_ids(domain_alias,'archive',archive_seminar_ids,20)

	paginated_seminar_ids={}
	paginated_seminar_ids.update(paginated_upcoming_seminar_ids)
	paginated_seminar_ids.update(paginated_archive_seminar_ids)

	archive_seminar_data={x[0]:x[1] for x in archive_seminar_data}

	return upcoming_seminar_data,archive_seminar_data,paginated_seminar_ids

def paginate_seminar_ids(domain_alias,upcoming_or_archive,sids,n):

	paginated_seminar_ids={}

	my_idx=0
	for i in range(0,len(sids),n):
		my_idx+=1

		
		partition_key=domain_alias+'_'+upcoming_or_archive+'_page_'+str(my_idx)
		this_paginated_ids=sids[i:i+n]

		dynamoDB_item={
				'partition_key': partition_key,
				'seminar_ids': this_paginated_ids
			}

		paginated_seminar_ids[partition_key]=dynamoDB_item

	max_page_idx_partition_key=domain_alias+'_'+upcoming_or_archive+'_max_page_idx'
	dynamoDB_item={
			'partition_key': max_page_idx_partition_key,
			'max_page': my_idx
		}

	paginated_seminar_ids[max_page_idx_partition_key]=dynamoDB_item

	return paginated_seminar_ids

def total_number_of_upcoming_archive_seminars(upcoming_num,archive_num):

	total_num_of_seminars={}

	partition_key=domain_alias+'_total_upcoming_num'
	dynamoDB_item={
			'partition_key': partition_key,
			'total_upcoming_num': upcoming_num
		}
	
	total_num_of_seminars[partition_key]=dynamoDB_item

	partition_key=domain_alias+'_total_archive_num'
	dynamoDB_item={
			'partition_key': partition_key,
			'total_archive_num': archive_num
		}

	total_num_of_seminars[partition_key]=dynamoDB_item

	return total_num_of_seminars


working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'

datetime_now = datetime.datetime.utcnow()
datetime_now = datetime_now.replace(tzinfo=pytz.utc)

datetime_an_hour_ago = datetime.datetime.utcnow()+datetime.timedelta(hours=-1.25)
datetime_an_hour_ago = datetime_an_hour_ago.replace(tzinfo=pytz.utc)

with open(working_dir+'/python_scripts/html_templates/topic_page.html','r') as f:
	topic_page_template = f.read()

with open(working_dir+'seminar_data.json','r') as json_file:
	seminar_data = json.load(json_file)

all_hosted_by_as_seen_in_seminars_assigned_across_across_ww=[v['hosted_by'] for v in seminar_data.values()]
all_hosted_by_as_seen_in_seminars_assigned_across_across_ww_counter=Counter(all_hosted_by_as_seen_in_seminars_assigned_across_across_ww)

with open(working_dir+'seminars_matching_data.json','r') as json_file:
	seminars_matching_data = json.load(json_file)

unique_hash_to_seminar_id_dict={ v['calendar_event_hash']:k for k,v in seminar_data.items() }
seminar_id_to_unique_hash_dict={ k:v['calendar_event_hash'] for k,v in seminar_data.items() }

with open(working_dir+'seminar_series_data.json','r') as json_file:
	seminar_series_data = json.load(json_file)

with open(working_dir+'world_wide_domains.json', 'r') as f:
	domains_data=json.load(f)

try:
	with open(working_dir+'all_domains_series_banners.json', 'r') as f:
		series_banners=json.load(f)
except:
	series_banners=dict()

try:
	with open(working_dir+'series_colors.json', 'r') as f:
		old_series_colors=json.load(f)
except:
	old_series_colors=dict()

def auto_assign_series_to_domain(domain_seminar_data):

	all_hosted_by_as_seen_in_seminars_assigned_within_this_domain=[v['hosted_by'] for v in domain_seminar_data.values()]
	all_hosted_by_as_seen_in_seminars_assigned_within_this_domain_counter=Counter(all_hosted_by_as_seen_in_seminars_assigned_within_this_domain)

	for hstb in all_hosted_by_as_seen_in_seminars_assigned_within_this_domain_counter:
		try:
			print(domain,hstb,all_hosted_by_as_seen_in_seminars_assigned_within_this_domain_counter[hstb]/all_hosted_by_as_seen_in_seminars_assigned_across_across_ww_counter[hstb])
		except:
			print('!!!',domain,hstb,all_hosted_by_as_seen_in_seminars_assigned_within_this_domain_counter[hstb],all_hosted_by_as_seen_in_seminars_assigned_across_across_ww_counter[hstb])


topics_colormap=['#41588a','#40598a','#405a8b','#3f5b8b','#3f5c8b','#3e5d8c','#3e5e8c','#3d5f8c','#3d608d','#3c618d','#3c628d','#3b638e','#3b648e','#3a658f','#3a668f','#39678f','#396890','#386990','#386a90','#376b90','#376c91','#366d91','#366e92','#356e92','#356f92','#347092','#337193','#337293','#337393','#327494','#327594','#317694','#317795','#307895','#307995','#2f7a96','#2f7b96','#2e7c96','#2e7c97','#2d7d97','#2d7e97','#2c7f98','#2c8098','#2b8198','#2b8299','#2a8399','#2a8499','#29859a','#29869a','#28879a','#28889b','#27889b','#27899b','#268a9b','#268b9c','#258c9c','#258d9c','#248e9d','#248f9d','#23909d','#23919e','#22929e','#22929e','#21939f','#21949f','#20959f','#2096a0','#1f97a0','#1f98a0','#1f99a1','#1e9aa1','#1e9ba1','#1d9ba1','#1d9ca2','#1c9da2','#1c9ea2','#1b9fa3','#1ba0a3','#1aa1a3','#1aa2a4','#19a3a4','#19a4a4','#18a5a5','#18a5a5','#17a6a5','#17a7a6','#16a8a6','#16a9a6','#15aaa7','#15aba7','#14aca7','#14ada7','#13aea8','#13afa8','#12afa8','#12b0a9','#11b1a9','#11b2a9','#10b3aa','#10b4aa']
series_colormap=["#ff8b79","#ff8c78","#ff8d77","#ff8e76","#ff8e75","#ff8f74","#ff9072","#ff9171","#ff9270","#ff936f","#ff936e","#ff946d","#ff956c","#ff966b","#ff976a","#ff9769","#ff9868","#ff9967","#ff9a66","#ff9b65","#ff9b64","#ff9c63","#ff9d62","#ff9e61","#ff9e60","#ff9f5f","#ffa05e","#ffa15d","#ffa15c","#ffa25b","#ffa35a","#ffa459","#ffa458","#ffa557","#ffa656","#ffa755","#ffa754","#ffa853","#ffa952","#ffaa51","#ffaa50","#ffab50","#ffac4f","#ffad4e","#ffad4d","#ffae4c","#ffaf4b","#ffaf4a","#ffb049","#ffb148","#ffb147","#ffb246","#ffb345","#ffb444","#ffb444","#ffb543","#ffb642","#ffb641","#ffb740","#ffb83f","#ffb83e","#ffb93d","#ffba3c","#ffba3c","#ffbb3b","#ffbc3a","#ffbc39","#ffbd38","#ffbe37","#ffbe36","#ffbf36","#ffc035","#ffc034","#ffc133","#ffc232","#ffc231","#ffc330","#ffc430","#ffc42f","#ffc52e","#ffc62d","#ffc62c","#ffc72b","#ffc82a","#ffc82a","#ffc929","#ffca28","#ffca27","#ffcb26","#ffcc25","#ffcc24","#ffcd24","#ffce23","#ffce22","#ffcf21","#ffcf20","#ffd01f","#ffd11f","#ffd11e","#ffd21d"]

series_colors=dict()

dynamoDB_data_to_be_put=dict()

for domain in domains_data:

	domain_seminar_data={k:v for k,v in seminar_data.items() if domain in v['domain']}
	domain_seminar_series_data={k:v for k,v in seminar_series_data.items() if domain in v['domain']}

	#auto_assign_series_to_domain(domain_seminar_data)

	domain_alias=domains_data[domain]['domain_alias']
	domain_nickname=domains_data[domain]['domain_nickname']
	domain_name=domains_data[domain]['domain_name']
	domain_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/' + domain_alias + '/'

	for this_path in ['','upcoming','archive']:
		if not os.path.exists(domain_dir+this_path):
			os.makedirs(domain_dir+this_path)

	if if_json_file_is_not_the_same(domain_dir+'seminar_data.json',domain_seminar_data):

		with open(domain_dir+'seminar_data.json','w') as f:
			json.dump(domain_seminar_data,f)
		
		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'seminar_data.json s3://www.world-wide.org/'+domain_alias+'/seminar_data.json')

	# if operating system is macos
	if sys.platform=='darwin':
		os.system('/usr/local/bin/node ' + working_dir + 'python_scripts/create_the_index.js ' + domain_alias)
	else:
		os.system('/usr/bin/node ' + working_dir + 'python_scripts/create_the_index.js ' + domain_alias)

	upcoming_seminar_data,archive_seminar_data,paginated_seminar_ids=get_domain_upcoming_and_archive_seminar_data(domain_alias,domain_seminar_data)

	dynamoDB_data_to_be_put.update(paginated_seminar_ids)

	if if_json_file_is_not_the_same(domain_dir+'upcoming/seminar_data.json',upcoming_seminar_data):

		with open(domain_dir+'upcoming/seminar_data.json','w') as f:
			json.dump(upcoming_seminar_data,f)

		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'upcoming/seminar_data.json s3://www.world-wide.org/'+domain_alias+'/upcoming/seminar_data.json')

	domain_seminar_data_changed_status=False
	if if_json_file_is_not_the_same(domain_dir+'archive/seminar_data.json',archive_seminar_data):

		domain_seminar_data_changed_status=True

		with open(domain_dir+'archive/seminar_data.json','w') as f:
			json.dump(archive_seminar_data,f)

		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'archive/seminar_data.json s3://www.world-wide.org/'+domain_alias+'/archive/seminar_data.json')

	mini_domain_seminar_data=get_N_immediately_upcoming_domain_seminars(domain_seminar_data)
	[upcoming_num,archived_num]=get_how_many_upcoming_archived(domain_seminar_data)

	total_num_of_seminars=total_number_of_upcoming_archive_seminars(upcoming_num,archived_num)
	dynamoDB_data_to_be_put.update(total_num_of_seminars)

	mini_seminar_data=[mini_domain_seminar_data,[upcoming_num,archived_num]]
	if if_json_file_is_not_the_same(domain_dir + 'mini_seminar_data.json', mini_seminar_data) or domain_seminar_data_changed_status:
	
		with open(domain_dir+'mini_seminar_data.json','w') as f:
			json.dump(mini_seminar_data,f)
		
		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'mini_seminar_data.json s3://www.world-wide.org/'+domain_alias+'/mini_seminar_data.json')
	
	if if_json_file_is_not_the_same(domain_dir+'seminar_series_data.json',domain_seminar_series_data):
		with open(domain_dir+'seminar_series_data.json','w') as f:
			json.dump(domain_seminar_series_data,f)

		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'seminar_series_data.json s3://www.world-wide.org/'+domain_alias+'/seminar_series_data.json')
	
		domain_ical=get_domain_specific_calendar(domain_name,domain_seminar_data)

	if len(domain_seminar_data)>0:

		top_topic_tags_to_colors,topic_tags_to_colors=get_topic_tags_to_colors(domain_seminar_data)
		top_series_tags_to_colors,series_tags_to_colors=get_series_tags_to_colors(domain_seminar_series_data)

		series_colors[domain]=series_tags_to_colors

		create_topic_tag_pages(topic_tags_to_colors,domain)

		tags_and_colors=[top_topic_tags_to_colors,topic_tags_to_colors,top_series_tags_to_colors,series_tags_to_colors]
	
		if if_json_file_is_not_the_same(domain_dir+'tags_and_colors.json',tags_and_colors):
			with open(domain_dir+'tags_and_colors.json','w') as f:
				json.dump(tags_and_colors,f)

		os.system('/usr/local/bin/aws s3 cp ' + domain_dir + 'tags_and_colors.json s3://www.world-wide.org/'+domain_alias+'/tags_and_colors.json')

	caltech_status=False
	seminar_series_list=list(set([i['hosted_by'] for i in seminar_data.values()]))

	if domain not in series_banners:
		series_banners[domain]=dict()

	for series in seminar_series_list:
		caltech_status=False

		try:
			if domain not in seminar_series_data[series]['domain']:
				continue
		except:
			continue
		
		series_specific_seminar_data={k:v for k,v in seminar_data.items() if v['hosted_by']==series and domain in v['domain']}
		for k,v in seminar_series_data.items():
			if v['Series Name']==series and domain in v['domain']:
				about_this_series=v
				about_this_series['domain_alias']=domain_alias

				series_banner_image=about_this_series['Banner Image']

				#if 'meta_cards' in series_banner_image:
				#	series_banner_image=''

				#print()
				#print('!!!',series,series_banner_image)

				if series not in series_banners[domain]:
					if series_banner_image=='':	
						#print(11)
						series_banner=pick_random_meta_card_and_save_it_in_the_newly_created_series_directory()
						series_banners[domain][series]=series_banner
					elif series_banner_image.split('.')[-1] not in ['jpg','png','gif','webp','tiff','bmp','heif','jpeg','svg']:
						#print(22)
						series_banner=pick_random_meta_card_and_save_it_in_the_newly_created_series_directory()
						series_banners[domain][series]=series_banner
					else:
						#print(33)
						series_banners[domain][series]=series_banner_image
				else:
					if series_banner_image!='':
						if series_banner_image.split('.')[-1] in ['jpg','png','gif','webp','tiff','bmp','heif','jpeg','svg'] and series_banner_image!='https://www.world-wide.org/banner.jpg':
							series_banners[domain][series]=series_banner_image
						
				#print(66)
				#print('!!>>@',series,series_banner_image)

				about_this_series['Banner Image']=series_banners[domain][series]



		domain_specific_seminar_data={k:v for k,v in seminar_series_data.items() if domain in v['domain']}

		series_alias=series.replace(' ','-')
		series_alias=series_alias.replace('&','and')

		dynamoDB_series_alias=domain_alias+'/'+series_alias
		
		series_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/' + domain_alias + '/' + series_alias + '/'
		aws_s3_series_dir= 's3://www.world-wide.org/' + domain_alias + '/' + series_alias + '/'
		
		if not os.path.exists(series_dir):

			os.makedirs(series_dir)

		series_seminar_ids=list(series_specific_seminar_data.keys())
		
		caltech_status=True
		if if_json_file_is_not_the_same(series_dir+'seminar_data.json',series_specific_seminar_data):

			with open(series_dir+'seminar_data.json','w') as f:
				json.dump(series_specific_seminar_data,f)

			os.system('/usr/local/bin/aws s3 cp ' + series_dir + 'seminar_data.json ' + aws_s3_series_dir + 'seminar_data.json')

			dynamoDB_series_key=dynamoDB_series_alias+'/seminar_ids'
			dynamoDB_item={
				'partition_key': dynamoDB_series_key,
				'seminar_ids': series_seminar_ids
			}

			dynamoDB_data_to_be_put[dynamoDB_series_key]=dynamoDB_item

		caltech_status=False
		if if_json_file_is_not_the_same(series_dir+'about_this_series.json',about_this_series):

			with open(series_dir+'about_this_series.json','w') as f:
				json.dump(about_this_series,f)
			
			os.system('/usr/local/bin/aws s3 cp ' + series_dir + 'about_this_series.json ' + aws_s3_series_dir + 'about_this_series.json')

			dynamoDB_series_key=dynamoDB_series_alias+'/about_this_series'
			dynamoDB_item=copy.deepcopy(about_this_series)
			dynamoDB_item['partition_key']=dynamoDB_series_key

			dynamoDB_data_to_be_put[dynamoDB_series_key]=dynamoDB_item

		get_series_specific_calendar(series_dir,aws_s3_series_dir,series_specific_seminar_data)

#pprint(dynamoDB_data_to_be_put)

with open(working_dir+'all_domains_series_banners.json', 'w') as f:
	json.dump(series_banners,f)

if if_json_file_is_not_the_same(working_dir+'series_colors.json',series_colors):
	with open(working_dir+'series_colors.json', 'w') as f:
		json.dump(series_colors,f)

	os.system('/usr/local/bin/aws s3 cp ' + working_dir + 'series_colors.json s3://www.world-wide.org/series_colors.json')

dynamoDB_data_to_be_put_keys=list(dynamoDB_data_to_be_put.keys())

if len(dynamoDB_data_to_be_put_keys)>0:
	# Get the service resource
	dynamodb = boto3.resource(
			'dynamodb',
			###
		)

	ww_seminars_table = dynamodb.Table('world-wide-seminars')
	batch_size=25

	'''print()
	print('='*20)
	print('I will put these items in dynamoDB:\n')
	for x in dynamoDB_data_to_be_put_keys:
		print(x)'''

	t1=time.time()
	put_to_dynamoDB(dynamoDB_data_to_be_put_keys,ww_seminars_table)
	t2=time.time()
	dt=t2-t1
	print()
	print('I successfuly put ' + str(len(dynamoDB_data_to_be_put_keys))+ ' items in dynamoDB! It took',dt,'seconds')
	print()
	print('='*20)
	print()

current_date_time=str(datetime.datetime.now())
print(current_date_time)
#pprint(working_dir)