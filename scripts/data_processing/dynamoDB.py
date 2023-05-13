import sys,os,re,boto3,json,time,datetime,pytz,random
from dateutil.parser import parse
from pprint import pprint
from pathlib import Path
from decimal import Decimal

# SEMINAR DATA VALUE EXAMPLE
'''
{'Event Duration': 70.000025,
 'biorxiv_rec': True,
 'calendar_event_hash': 'dbac26a4c16448c85ac40f7132ee5038d63390cb7e8b2d997255ecf4256f2d33',
 'domain': ['Physics of Life'],
 'hosted_by': 'Imperial College Physics of Life Network Seminars',
 'matching_data': {'matching_employers': [{'affiliation': 'Rutgers University',
										   'employer_name': 'Prof Ian '
															'Oldenburg',
										   'job_type': ['MSc',
														'PhD',
														'Post-Doc',
														'Lab Technician',
														'Research Assistant',
														'Research Fellow',
														'Data Scientist'],
										   'matching_score': 0.613,
										   'url': 'https://www.world-wide.org/jobs/e/cIn2M70ZOWty6j'},
										  {'affiliation': 'Riken ',
										   'employer_name': 'Terufumi Fujiwara',
										   'job_type': ['Post-Doc',
														'PhD',
														'Research Assistant'],
										   'matching_score': 0.6075,
										   'url': 'https://www.world-wide.org/jobs/e/N5ctbKRzrhAZGm'}],
				   'matching_seminars': [{'matching_score': 0.8165,
										  'seminar_speaker': 'Hannah Yevick',
										  'seminar_title': 'Making '
														   'connections: how '
														   'epithelial tissues '
														   'guarantee folding',
										  'speaker_affil': 'MIT',
										  'speaker_title': 'Dr',
										  'url': 'https://www.world-wide.org/seminar/7478'},
										 {'matching_score': 0.8145,
										  'seminar_speaker': 'Veronica '
															 'Ciocanel',
										  'seminar_title': 'Modeling and '
														   'topological data '
														   'analysis for '
														   'biological ring '
														   'channels',
										  'speaker_affil': 'Duke University',
										  'speaker_title': 'Dr.',
										  'url': 'https://www.world-wide.org/seminar/6272'},
										 {'matching_score': 0.786,
										  'seminar_speaker': 'Margaret Gardel',
										  'seminar_title': 'Design Principles '
														   'of Living Matter',
										  'speaker_affil': 'University of '
														   'Chicago',
										  'speaker_title': 'Prof',
										  'url': 'https://www.world-wide.org/seminar/6757'}]},
 'password': '',
 'posted': 'yes',
 'seminar_abstract': 'My lab studies the design principles of cytoskeletal '
					 'materials the drive cellular morphogenesis, with a focus '
					 'on contractile machinery in adherent cells. In addition '
					 'to force generation, a key feature of these materials '
					 'are distributed force sensors which allow for rapid '
					 'assembly, adaptation, repair and disintegration. Here I '
					 'will describe how optogenetic control of RhoA GTPase is '
					 'a powerful and versatile force spectroscopy approach of '
					 'cytoskeletal assemblies and its recent use to probe '
					 'repair response in actomyosin stress fibers. I will also '
					 'describe our recent identification of 18 proteins from '
					 'the zyxin, paxillin, Tes and Enigma families with '
					 'mechanosensitive LIM (Lin11, Isl- 1 & Mec-3) domains '
					 'that bind exclusively to mechanically stressed actin '
					 'filaments. Our results suggest that the evolutionary '
					 'emergence of contractile F-actin machinery coincided '
					 'with, or required, proteins that could report on the '
					 'stresses present there to maintain homeostasis of '
					 'actively stressed networks.',
 'seminar_date': 'Fri, Sep 18, 2020',
 'seminar_id': 6897,
 'seminar_link': 'https://www.imperial.ac.uk/events/122152/prof-margaret-gardel/',
 'seminar_speaker': 'Margaret Gardel',
 'seminar_time': '15:00',
 'seminar_title': 'Mechanical Homeostasis of the Actin Cytoskeleton',
 'speaker_affil': 'University of Chicago',
 'speaker_title': '',
 'speaker_twitter': '',
 'speaker_website': '',
 'time_of_addition': 'Mon, May 31, 2021 12:25',
 'timezone': 'Europe/London',
 'topic_tags': ['physics of life',
				'actin cytoskeleton',
				'contractile machinery',
				'paxillin',
				'zyxin',
				'cytoskeletal assemblies'],
 'video_on_demand': 'https://youtu.be/vw1NIXQwFpM'}
'''

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
		items=[seminar_data[str(x)] for x in primary_keys]
		items=[json.loads(json.dumps(x), parse_float=Decimal) for x in items]
		return items
	else:
		item=seminar_data[str(primary_keys)]
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

# ARN
# arn:aws:dynamodb:eu-west-1:661529993212:table/world-wide-seminars

# endpoint
# https://dynamodb.eu-west-1.amazonaws.com

# Get the service resource
dynamodb = boto3.resource(
		'dynamodb',
		###
	)

ww_seminars_table = dynamodb.Table('world-wide-seminars')
batch_size=25

#ll=[7298, 7300, 7302, 7305, 7306, 7307, 7308, 7309, 7312, 7313, 7314, 7315, 7316, 7317, 7318, 7319, 7320, 7321, 7322, 7323, 7325, 7326, 7327, 7328, 7331, 7332, 7333, 7334, 7335, 7336, 7337, 7339, 7340, 7342, 7343, 7344, 7345, 7347, 7348, 7349, 7350, 7351, 7352, 7353, 7355, 7356, 7357, 7360, 7361, 7362, 7364, 7365, 7367, 7368, 7370, 7371, 7373, 7374, 7375, 7376, 7377, 7378, 7379, 7380, 7381, 7382, 7383, 7384, 7385, 7387, 7388, 7389, 7390, 7392, 7395, 7400, 7402, 7403, 7404, 7405, 7406, 7410, 7416, 7417, 7418, 7419, 7420, 7421, 7422, 7423, 7424, 7425, 7427, 7428, 7429, 7430, 7431, 7432, 7433, 7434, 7435, 7436, 7437, 7438, 7440, 7442, 7445, 7446, 7448, 7449, 7450, 7451, 7452, 7455, 7457, 7458, 7459, 7460, 7461, 7462, 7463, 7464, 7465, 7466, 7467, 7468, 7469, 7470, 7471, 7472, 7473, 7475, 7476, 7477, 7478, 7479, 7480, 7481, 7482, 7483, 7484, 7488, 7490, 7491, 7492, 7493, 7495, 7496, 7497, 7499, 7501, 7503, 7505, 7507, 7508, 7509, 7511, 7512, 7513, 7514, 7515, 7516, 7517, 7518, 7519, 7520, 7521, 7523, 7525, 7526, 7527, 7529, 7530, 7532, 7533, 7534, 7535, 7536, 7537, 7538, 7539, 7540, 7541, 7542, 7544, 7545, 7546, 7547, 7548, 7549, 7550, 7551, 7552, 7553, 7554, 7555, 7556, 7558, 7559, 7560, 7561, 7562, 7563, 7564, 7566, 7567, 7569, 7570, 7571, 7572, 7574, 7575, 7576, 7577, 7578, 7579, 7580, 7581, 7582, 7583, 7584, 7586, 7588, 7589, 7590, 7591, 7593, 7594, 7595, 7596, 7597, 7598, 7599, 7600, 7601, 7602, 7603, 7604, 7605, 7607, 7608, 7609, 7610, 7611, 7612, 7613, 7614, 7615, 7616, 7618, 7619, 7620, 7621, 7631, 7633, 7634, 7635, 7636, 7637, 7638, 7639, 7640, 7641, 7642]
#items=get_from_dynamoDB(ll,ww_seminars_table)

#print(len(ll))
#print(len(items))

working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'

with open(working_dir+'world_wide_domains.json') as json_file:
	world_wide_domains = json.load(json_file)

with open(working_dir+'seminar_data.json') as json_file:
	seminar_data = json.load(json_file)

# all seminar_id keys in the local json file
all_seminar_ids=[x['seminar_id'] for x in seminar_data.values()]

t1=time.time()
# all seminar_id keys in the dynamoDB table
all_seminar_ids_in_dynamoDB=get_all_seminar_ids_in_dynamoDB_table(ww_seminars_table)
t2=time.time()
dt=t2-t1

seminar_ids_not_in_dynamoDB=list(set(all_seminar_ids)-set(all_seminar_ids_in_dynamoDB))
seminar_ids_not_in_local_json=list(set(all_seminar_ids_in_dynamoDB)-set(all_seminar_ids))

print('Number of seminars in the local json file: ' + str(len(all_seminar_ids)))
print('Number of seminars in the dynamoDB table: ' + str(len(all_seminar_ids_in_dynamoDB)))
print('Time taken to get all seminar ids from dynamoDB: ' + str(dt))
print('\n')
print('Number of seminars not in the dynamoDB table: ' + str(len(seminar_ids_not_in_dynamoDB)))
print('\n')
print('Number of seminars not in the local json file: ' + str(len(seminar_ids_not_in_local_json)))
print('\n')

if len(seminar_ids_not_in_dynamoDB)>0:
	print('These are the seminar ids not in the dynamoDB table: ' + str(seminar_ids_not_in_dynamoDB))
	put_to_dynamoDB(seminar_ids_not_in_dynamoDB,ww_seminars_table)
	print('I just put these seminars from the dynamoDB table\n')

if len(seminar_ids_not_in_local_json)>0:
	print('These are the seminar ids not in the local json file: ' + str(seminar_ids_not_in_local_json))
	delete_from_dynamoDB(seminar_ids_not_in_local_json,ww_seminars_table)
	print('I just deleted these seminars from the dynamoDB table\n')