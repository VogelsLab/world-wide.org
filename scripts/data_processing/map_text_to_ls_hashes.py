import sys,json,time,hashlib,pickle
from pprint import pprint
from pathlib import Path

from datasketch import MinHash, MinHashLSH
from nltk import ngrams
import pandas as pd

def get_row_ids(this_df, xyz_col, this_value):
	return this_df[this_df[xyz_col] == this_value].index.tolist()

def get_unique_hash(text):
	bytes_to_digest=bytes(text.encode())
	unique_hash=hashlib.sha256(bytes_to_digest).hexdigest()
	return unique_hash

def get_ngram_set(text):
	return ngrams(text,3)

def convert_text_to_set_and_get_minhash_object(text):
	
	my_minhash = MinHash(num_perm=128)
	for this_ngram in get_ngram_set(text):
		my_minhash.update(''.join(this_ngram).encode('utf-8'))

	return my_minhash

def get_all_different_versions_of_ww_text_stored_in_the_pd_frame(ww_text_df):

	# Make a list of 'joined_title_abstract' and 'joined_title_abstract_minus_middle_third' values if the respective 'seminar_abstract' value is not None

	ww_text_list=[]
	for index,row in ww_text_df.iterrows():
		if row['seminar_abstract'] is not None:
			ww_text_list.append(row['joined_title_abstract'])

	ww_text_list=[x for x in ww_text_list if len(x)>=120]
	return set(ww_text_list)

def update_ww_text_to_hash_dict(ww_text_set):

	# Try to load the 'ww_text_to_hash_dict' from the pickle file, otherwise create it

	try:
		if reset:
			foo=non_existing_foo
		with open(scripts_dir+'ww_text_to_hash_dict.pkl','rb') as f:
			ww_text_to_hash_dict=pickle.load(f)
	except:
		ww_text_to_hash_dict=dict()

	# Get a unique hash for each new TEXT item in ww_text_set

	new_ww_text_to_process=ww_text_set.difference(set(ww_text_to_hash_dict.keys()))

	for text in new_ww_text_to_process:
		unique_hash=get_unique_hash(text)
		ww_text_to_hash_dict[text]=unique_hash

	return ww_text_to_hash_dict

def try_and_load_uhash_to_original_uhash_or_create_it():

	try:
		if reset:
			foo=non_existing_foo
		with open(scripts_dir+'uhash_to_original_uhash.pkl','rb') as f:
			uhash_to_original_uhash=pickle.load(f)
	except:
		uhash_to_original_uhash=dict()

	return uhash_to_original_uhash

def try_and_load_ww_text_lsh_or_create_it():

	try:
		if reset:
			foo=non_existing_foo
		with open(scripts_dir+'ww_text_lsh.pkl','rb') as f:
			ww_text_lsh=pickle.load(f)
	except:
		ww_text_lsh=MinHashLSH(threshold=param, num_perm=128)

	return ww_text_lsh

'''
THIS FILE MAPS UNIQUE_HASHES_TO_ORIGINAL UNIQUE_HASHES
--> ESSENTIALY, IT IS A WAY TO PROCESS (NLPU) ONLY THE ORIGINAL TEXT FROM A BUCKET OF VERY SIMILAR TO EACH OTHER TEXTS
'''

try:
	param=float(sys.argv[1])
except:
	param=0.875

reset=False

working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'
scripts_dir=working_dir+'python_scripts/'

#pd.set_option('display.max_rows', 1000)
#pd.options.display.width = 0

#ww_text_df=pd.read_pickle(scripts_dir+'ww_text_df.pkl')
ww_text_df=pd.read_json(scripts_dir+'ww_text_df.json')

#print(ww_text_df.sample(100))

#sys.exit()

ww_text_set=get_all_different_versions_of_ww_text_stored_in_the_pd_frame(ww_text_df)
ww_text_to_hash_dict=update_ww_text_to_hash_dict(ww_text_set)

uhash_to_seminar_id=dict()
uhash_to_UTC_datetime=dict()
my_status=False
for index,row in ww_text_df.iterrows():
	
	unique_hash=row['unique_hash']

	if unique_hash!=None:
		uhash_to_seminar_id[unique_hash]=index

	if row['joined_title_abstract'] in ww_text_set:
		this_ww_text=row['joined_title_abstract']
		this_uhash=ww_text_to_hash_dict[this_ww_text]
		uhash_to_UTC_datetime[this_uhash]=row['utc_datetime']

# pickle save
with open(scripts_dir+'uhash_to_seminar_id.pkl','wb') as f:
	pickle.dump(uhash_to_seminar_id,f)
# json save
with open(scripts_dir+'uhash_to_seminar_id.json','w') as f:
	json.dump(uhash_to_seminar_id,f)

#pprint(uhash_to_UTC_datetime)

#sys.exit()

uhash_to_original_uhash=try_and_load_uhash_to_original_uhash_or_create_it()

'''uhash_to_ww_text_dict={unique_hash:text for text,unique_hash in ww_text_to_hash_dict.items()}

test_dict=dict()
for k,v in uhash_to_original_uhash.items():
	test_dict.setdefault(v, []).append(k)

from collections import Counter

for k,v in test_dict.items():
	
	if not len(v)>=2:
		continue

	row_ids=get_row_ids(ww_text_df,'joined_title_abstract',uhash_to_ww_text_dict[k])

	print('=='*45)
	print()
	print('>>>')
	print()
	print('unique_hash:',k)
	print(uhash_to_ww_text_dict[k])
	print('seminar_ids:',row_ids)
	for r in row_ids:
		print('https://www.world-wide.org/seminar/'+r)
	
	for x in v:
		
		print('***')
		print('unique_hash:',x)
		print(uhash_to_ww_text_dict[x])
		
		row_ids=get_row_ids(ww_text_df,'joined_title_abstract',uhash_to_ww_text_dict[x])

		print('seminar_ids:',row_ids)
		for r in row_ids:
			print('https://www.world-wide.org/seminar/'+r)
		print('***')

	print()
	print()
	print('=='*45)

sys.exit()'''

# Check if there are any unique hashes stored as values in 'ww_text_to_hash_dict' that are not contained found as keys in 'uhash_to_original_uhash'
unseen_ww_text_hashes=set(ww_text_to_hash_dict.values()).difference(set(uhash_to_original_uhash.keys()))

if len(unseen_ww_text_hashes)>=1:
	pass
else:
	sys.exit()

print('> There are '+ str(len(unseen_ww_text_hashes)) + ' unseen_ww_text_hashes -- I will process it / them now !')

# This uhash_to_ww_text_dict is needed below when text is needed to create minhashes
unseen_uhash_to_ww_text_dict={unique_hash:text for text,unique_hash in ww_text_to_hash_dict.items() if unique_hash in unseen_ww_text_hashes}

# Try to load the MinHashLSH named 'ww_text_lsh' and insert the values of hash_to_ww_text_dict

ww_text_lsh=try_and_load_ww_text_lsh_or_create_it()

#print('='*80)
#print(uhash_to_ww_text_dict.keys())
#print()

for unique_hash,text in unseen_uhash_to_ww_text_dict.items():

	#print('>',unique_hash)

	my_minhash=convert_text_to_set_and_get_minhash_object(text)
	result = ww_text_lsh.query(my_minhash)

	if len(result)==0:
		ww_text_lsh.insert(unique_hash,my_minhash)
		uhash_to_original_uhash[unique_hash]=unique_hash
	elif len(result)==1:
		print('\nThere is a text item: '+result[0]+' very similar to that (see line below)\n--> '+unique_hash+' already existing in the MinHash\n')
		uhash_to_original_uhash[unique_hash]=result[0]
	else:
		print('\nThere is a text item: '+result[0]+' very similar to more than one items (see line below)\n--> '+unique_hash+' already existing in the MinHash\n')
		uhash_to_original_uhash[unique_hash]=result[0]

with open(scripts_dir+'uhash_to_original_uhash.pkl','wb') as f:
	pickle.dump(uhash_to_original_uhash,f)

# invert uhash_to_original_uhash dictionary
original_uhash_to_uhashes=dict()
for k,v in uhash_to_original_uhash.items():
	# use default append
	original_uhash_to_uhashes.setdefault(v,[]).append(k)

with open(scripts_dir+'original_uhash_to_uhashes.pkl','wb') as f:
	pickle.dump(original_uhash_to_uhashes,f)

with open(scripts_dir+'ww_text_to_hash_dict.pkl','wb') as f:
	pickle.dump(ww_text_to_hash_dict,f)

uhash_to_ww_text_dict={unique_hash:text for text,unique_hash in ww_text_to_hash_dict.items()}

with open(scripts_dir+'uhash_to_ww_text_dict.pkl','wb') as f:
	pickle.dump(uhash_to_ww_text_dict,f)

all_original_uhashes=list(set(uhash_to_original_uhash.values()))

original_uhash_to_UTC_datetime={unique_hash:uhash_to_UTC_datetime[unique_hash] for original_unique_hash in all_original_uhashes}

with open(scripts_dir+'original_uhash_to_UTC_datetime.pkl','wb') as f:
	pickle.dump(original_uhash_to_UTC_datetime,f)

with open(scripts_dir+'ww_text_lsh.pkl','wb') as f:
	pickle.dump(ww_text_lsh,f)

# Create a dict with ww_text_df uhash as key and ww_text_df index as value

original_uhash_to_corresponding_uhashes_and_seminar_ids=dict()
for x in all_original_uhashes:
	try:
		original_uhash_to_corresponding_uhashes_and_seminar_ids[x]=dict()
		my_ori_uh2uh=original_uhash_to_uhashes[x]
		my_ori_ih2sids=[uhash_to_seminar_id[i] for i in my_ori_uh2uh]
		original_uhash_to_corresponding_uhashes_and_seminar_ids[x]['uhashes']=my_ori_uh2uh
		original_uhash_to_corresponding_uhashes_and_seminar_ids[x]['seminar_ids']=my_ori_ih2sids
	#except any error, print it
	except Exception as e:
		pass

# save it as pickle
with open(scripts_dir+'original_uhash_to_corresponding_uhashes_and_seminar_ids.pkl','wb') as f:
	pickle.dump(original_uhash_to_corresponding_uhashes_and_seminar_ids,f)
# save it as json
with open(scripts_dir+'original_uhash_to_corresponding_uhashes_and_seminar_ids.json','w') as f:
	json.dump(original_uhash_to_corresponding_uhashes_and_seminar_ids,f)

sys.exit()

'''
already_seen=[]
for unique_hash,text in seminar_text_data.items():
if 'addiction neuroscience in this' in text.lower():
	continue
if 'learning salon' in text.lower():
	continue
if 'disciplinary collaborations have resulte' in text.lower():
	continue
if 'putational neuroscience from my point of view com' in text.lower():
	continue
'''
