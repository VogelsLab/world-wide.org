import sys,json,time,spacy,pickle,datetime,pytz,hashlib
from pprint import pprint
from pathlib import Path
from dateutil.parser import parse

import pandas as pd

# pd.set_option('display.max_colwidth', None)

def get_unique_hash(text):
	if len(text)<120:
		return None
	else:
		bytes_to_digest=bytes(text.encode())
		unique_hash=hashlib.sha256(bytes_to_digest).hexdigest()
		return unique_hash

def remove_quotes(s):
	try:
		while s[0] in "\"'":
			s = s[1:]
		while s[-1] in "\"'":
			s = s[:-1]
	except:
		pass

	return s

def join_strings(first, second):

	first=first.strip()
	first=remove_quotes(first)
	first=first.strip()

	second=second.strip()
	second=remove_quotes(second)
	second=second.strip()

	try:
		if first[-1] in "!.?":
			first = first[:-1]
	except:
		pass

	if len(first)>=7:
		joined='. '.join([first,second])
	else:
		joined=second

	return joined.strip()

# Write a function that get rids of the middle 3rd of the text and returns the first and last third joined together

def get_rid_of_the_middle(text):
	print('hello')
	# Split the paragraph into sentences
	doc = nlp(text)
	sentences = [sent.text for sent in doc.sents]
	if len(sentences)>3:
	
		# Get the middle third of the text
		middle_third = int(len(sentences)/3)
		middle_third_sentences = sentences[middle_third:middle_third*2]
		
		# Get the start and end of the text
		start_of_text = sentences[:middle_third]
		end_of_text = sentences[middle_third*2:]
		
		# Join the text back together
		text_except_middle_third = start_of_text + end_of_text
		text_except_middle_third_string = ' '.join(text_except_middle_third)
		
		return text_except_middle_third_string

	else:

		return text

def updated_in_the_past_N_minutes(N_minutes):

	with open('last_updated.pkl', 'rb') as f:
		last_updated = pickle.load(f)

	diff=datetime.datetime.utcnow() - last_updated
	diff=diff.total_seconds()
	
	if diff < 60*N_minutes-120:
		return True
	else:
		return False

def get_utc_datetime(seminar_date,seminar_time,seminar_timezone):
	
	seminar_timezone=pytz.timezone(seminar_timezone)
	datetime_obj=parse(seminar_date + ' ' + seminar_time, fuzzy=True)
	datetime_in_UTC = seminar_timezone.localize(datetime_obj).astimezone(pytz.UTC)

	return datetime_in_UTC

def video_on_demand_link_available(vid_url):
	video_on_demand_platforms=['crowdcast','youtu','vimeo']
	if any([True for i in video_on_demand_platforms if i in vid_url]):
		return True
	else:
		return None

if updated_in_the_past_N_minutes(30):
	pass
else:
	pass
	#sys.exit()

nlp = spacy.load('en_core_web_lg')

working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'
scripts_dir=working_dir+'python_scripts/'

with open(working_dir+'seminar_data.json','r') as json_file:
	seminar_data = json.load(json_file)

# Keep the fields 'seminar_title', 'seminar_abstract', 'topic_tags' and put them in a Pandas dataframe

ww_text_df = pd.DataFrame(columns=['seminar_id','seminar_title','seminar_abstract','topic_tags','utc_datetime','video_on_demand']) #,'unique_hash'])
ww_text_df = ww_text_df.set_index('seminar_id')

for k,v in seminar_data.items():
	seminar_id=k
	seminar_title=v['seminar_title']
	seminar_abstract=v['seminar_abstract']
	if seminar_abstract.startswith('Host:') or any(True for x in ['Denis Jabaudon'] if x in seminar_abstract):
		seminar_abstract=''
	topic_tags=v['topic_tags']
	utc_datetime=get_utc_datetime(v['seminar_date'],v['seminar_time'],v['timezone'])
	if 'video_on_demand' in v:
		video_on_demand=video_on_demand_link_available(v['video_on_demand'].lower())
	else:
		video_on_demand=None
	ww_text_df.loc[seminar_id]=[seminar_title,seminar_abstract,topic_tags,utc_datetime,video_on_demand]

# Join the seminar title and the seminar abstract together in a column named 'joined_title_abstract'

ww_text_df['joined_title_abstract']=ww_text_df.apply(lambda x: join_strings(x['seminar_title'],x['seminar_abstract']),axis=1)

# Create a column 'unique_hash' with input from the 'joined_title_abstract' column

ww_text_df['unique_hash']=ww_text_df.apply(lambda x: get_unique_hash(x['joined_title_abstract']),axis=1)

# Get rid of the middle text of the 'joined_title_abstract' column

# ww_text_df['joined_title_abstract_minus_middle_third'] = ww_text_df.apply(lambda x: get_rid_of_the_middle(x['joined_title_abstract']),axis=1)

# Replace all values with string length less than 7 with None

for column in ['seminar_title','seminar_abstract','joined_title_abstract']:

	ww_text_df[column] = ww_text_df[column].apply(lambda x: None if len(x)<7 else x)

# For all those rows where unique_hash is not None make a dictionary with keys the unique_hash column and values the utc_datetime column

uhash_to_UTC_datetime=dict()
uhash_to_ww_text=dict()

for index,row in ww_text_df.iterrows():
	if row['unique_hash'] is not None:
		uhash_to_UTC_datetime[row['unique_hash']]=row['utc_datetime']
		uhash_to_ww_text[row['unique_hash']]=row['joined_title_abstract']

with open('uhash_to_ww_text.pkl', 'wb') as f:
	pickle.dump(uhash_to_ww_text, f)

with open('uhash_to_UTC_datetime.pkl', 'wb') as f:
	pickle.dump(uhash_to_UTC_datetime, f)

pd.set_option('display.max_rows', 1000)
pd.options.display.width = 0

ww_text_df.to_json(scripts_dir+'ww_text_df.json')
#ww_text_df=pd.read_json(working_dir+'ww_text_df.json', orient='records', encoding='utf-8')

#ww_text_df.to_pickle(scripts_dir+'ww_text_df.pkl')