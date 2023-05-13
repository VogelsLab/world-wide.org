import sys,os,pickle,os,re,time,random,json,lmdb,ast
from pprint import pprint
from collections import Counter
import multiprocessing as mp
from fuzzywuzzy import fuzz
from statistics import mean

def is_plural(list_item):

	[a,b]=list_item

	this=['s']
	x=list(set(a)-set(b))
	y=list(set(b)-set(a))

	if abs(len(a)-len(b))==1:
		if x==this: # a is plural
			return b,a
		elif y==this: # b is plural
			return a,b
		else:
			return None,None
	else:
		return None,None

def hasNumbers(inputString):
	return any(char.isdigit() for char in inputString)

def chunks(l, n):

	for i in range(0, len(l), n):
		yield l[i:i + n]

def multi_function(my_kp_list):

	my_grouped_keyphrases_list=[]

	i,tm,my_ll,mdl=0,[],len(my_kp_list),10
	t1=time.time()

	for w1 in my_kp_list:

		my_group=[[w1,kp_freq_dict[w1]]]

		for w2 in keyphrases_set:

			if w1!=w2:
				fuzzy_score=fuzz.token_sort_ratio(w1,w2)
				if fuzzy_score>=87:
					my_group.append([w2,kp_freq_dict[w2]])

		my_grouped_keyphrases_list.append(my_group)

		i+=1
		if i%mdl==0 and i>3:
				
			t2=time.time()
			tt=t2-t1
			tm.append(tt)
			if len(tm)>=3:
				tt=float(mean(tm))
			eta=float(tt*(my_ll-i)/mdl)
			minutes,seconds = divmod(eta,60)
			#print('>',mp.current_process().name,'\t',i,'/',my_ll,'or',int(100*i/my_ll),'%','\t',int(minutes),'min', int(seconds), 'sec')
			t1=time.time()

	return my_grouped_keyphrases_list

def write_keyphrases_to_file(keyphrases,unique_id):

	with open(curated_keyphrases_dir+unique_id+'.pkl','wb') as f:
		pickle.dump([unique_id,keyphrases],f)


def keyword_checks_outs(x):

	if any(char.isdigit() for char in x):
		my_len=2
	else:
		my_len=6

	if len(x)>=my_len:
		return True
	else:
		return False

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

def get_frequently_used_and_supposedly_meaningful_keyphrases():

	with open(home+'/Dropbox/websites/world-wide.org/seminar_data.json','r') as f:
		seminar_data=json.load(f)

	seminar_data_keywords=[[x for x in v['topic_tags'] if keyword_checks_outs(x)] for v in seminar_data.values()]
	seminar_data_keywords=['E/I balance' for x in seminar_data.values() if kp_is_EI_balance_ab(x['seminar_title'],x['seminar_abstract'])]
	seminar_data_keywords=[item for sublist in seminar_data_keywords for item in sublist]
	keywords_counter=Counter(seminar_data_keywords)
	frequent_processed_and_published_keywords=list(set([x.lower() for x in seminar_data_keywords if keywords_counter[x]>=1]))

	return frequent_processed_and_published_keywords

def process_raw_keyphrase_data(raw_keyphrases):
	
	original=raw_keyphrases[0]
	rank_scores=raw_keyphrases[1]
	aliases=raw_keyphrases[2]

	processed_keyphrases=[]
	for i in range(len(original)):
		#print(rank_scores[i])
		if rank_scores[i]>=0.8:
			processed_keyphrases.append(original[i])
			if len(aliases[i])>0:
				for ii in aliases[i]:
					processed_keyphrases.append(ii)
		elif original[i].lower() in frequent_processed_and_published_keywords and rank_scores[i]>=0.75:
			processed_keyphrases.append(original[i])
			if len(aliases[i])>0:
				for ii in aliases[i]:
					processed_keyphrases.append(ii)
		elif original[i].lower() in mesh_terms and rank_scores[i]>=0.7:
			processed_keyphrases.append(original[i])
			if len(aliases[i])>0:
				for ii in aliases[i]:
					processed_keyphrases.append(ii)
			
	processed_keyphrases=list(set(processed_keyphrases))

	return processed_keyphrases

def get_bad_keywords():

	with open(home+'/Dropbox/various_bits_and_bobs/particularly_bad.pkl','rb') as f:
		bad=pickle.load(f)

	bad+=['essentialism in psychology','account','salon','festival','unique','framework','organizations','sciences','colleague','contributions','contribution','appropriate','usual','unusual','vulnerability','vulnerable','severity','many','severe','researcher','technology','researchers','advantage','disadvantage','change','changes','institutional','crisis','international','consistency','consistent','national','survey','cohort','distinct','basis','research','individual','speaker','conference','idea','ideas','individuality','identical','difference','differences','mechanisms','mechanism','performance','project','operation','patherns','personal','prjects','interdisciplinary','comparative','activity','personal','dsgcs','passionate','journey','neuroscientists','neuroscientist','neurology','scientists','scientist','representation','representations','impairments','impairment','process','processes']
	bad=list(set(bad))

	return bad

def get_lmdb_semantic_scholar_IDs_from_keyphrase(kp):

	try:
		value=lmdb_kp_to_article_ids_txn.get(kp.encode())
		value=value.decode()
		value=eval(value)
	except:
		value=[]

	return value

def get_lmdb_article_title_and_abstracts(this_sem_ids):

	if len(this_sem_ids)>55:
		this_sem_ids=random.sample(this_sem_ids, 25)

	all_text=''
	for sem_id in this_sem_ids:

		item_data=lmdb_article_data_txn.get(sem_id.encode())	
		item_data=item_data.decode()
		item_data=eval(item_data)

		title=item_data[3]
		abstract=item_data[6]

		all_text+=title+' '+abstract

	return all_text

def split_reduce_keyphrase_versions(kp):

	kp_split=kp.split()

	reduced_kp_version_1=' '.join(kp_split[1:])
	reduced_kp_version_2=' '.join(kp_split[:-1])

	return reduced_kp_version_1,reduced_kp_version_2

def split_reduce_keyphrase_versions_5(kp):

	kp_split=kp.split()

	reduced_kp_version_1=' '.join(kp_split[1:])
	reduced_kp_version_2=' '.join(kp_split[2:])
	reduced_kp_version_3=' '.join(kp_split[:-2])
	reduced_kp_version_4=' '.join(kp_split[:-1])

	return reduced_kp_version_1,reduced_kp_version_2,reduced_kp_version_3,reduced_kp_version_4

def get_most_frequent_version_in_the_literature(this_kp,this_sem_ids):

	all_text=get_lmdb_article_title_and_abstracts(this_sem_ids)

	matched_versions=re.findall(re.escape(this_kp), all_text, flags=re.IGNORECASE | re.MULTILINE)

	c=Counter(matched_versions)
	print(c)
	most_freq_kp_version=c.most_common(1)[0][0]
	
	return most_freq_kp_version

from pathlib import Path

home = str(Path.home())
current_dir=os.getcwd()

semantic_scholar_dir=home+'/semantic_scholar/'

t11=time.time()

lmdb_dst_dir_path=semantic_scholar_dir+'lmdb_english_medline_kp_to_semantic_scholar_IDs/'
lmdb_kp_to_article_ids_env = lmdb.open(lmdb_dst_dir_path, map_size=int(1e13))
lmdb_kp_to_article_ids_txn = lmdb_kp_to_article_ids_env.begin()

lmdb_dst_dir_path=semantic_scholar_dir+'lmdb_english_medline_article_data/'
lmdb_article_data_env = lmdb.open(lmdb_dst_dir_path, map_size=int(1e14))
lmdb_article_data_txn = lmdb_article_data_env.begin()

working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/python_scripts/'

with open(home+'/Dropbox/curated_terms/mesh/mesh_terms.pkl','rb') as f:
	mesh_terms=pickle.load(f)

frequent_processed_and_published_keywords=get_frequently_used_and_supposedly_meaningful_keyphrases()
bad=get_bad_keywords()

raw_keyphrases_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/keyphrases/seminars/raw/'
curated_keyphrases_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/keyphrases/seminars/curated/'

files=[raw_keyphrases_dir+x for x in os.listdir(raw_keyphrases_dir) if x.endswith('.pkl')]

processed_keyphrases_dict=dict()

all_keyphrases=['excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','excitatory/inhibitory balance','excitatory/inhibitory balance','excitatory-inhibitory balance','excitatory - inhibitory balance','excitatory / inhibitory balance', 'E/I balance','E / I balance','E-I balance','E - I balance','EI balance','E&I balance','EI balance','E&I balance','EI balance','E&I balance','EI balance','E&I balance','EI balance','E&I balance','EI balance','E&I balance']
for fname in files:

	with open(fname,'rb') as f :
		x=pickle.load(f)

	unique_id=x[0]
	raw_keyphrases=x[1]

	processed_keyphrases=process_raw_keyphrase_data(raw_keyphrases)
	all_keyphrases+=processed_keyphrases

	processed_keyphrases_dict[unique_id]=processed_keyphrases

c=Counter(all_keyphrases)

good_c={k:v for k,v in c.items() if not any(True for i in k.split() if i in bad)}
'''# sort good_c by value
good_c = sorted(good_c.items(), key=lambda x: x[1], reverse=True)
# print all good_c
for k,v in good_c:
	print(k,v)

sys.exit()'''

kp_freq_dict={k:v for k,v in good_c.items() if v>=1}

#l=[[k,v] for k,v in best_c.items()]
#l.sort(key=lambda x: x[1])
#pprint(l)

keyphrases_set=sorted(list(kp_freq_dict))
random.shuffle(keyphrases_set)

num_of_cores=int(mp.cpu_count())-3
chunk_length=int(len(keyphrases_set)/num_of_cores)

#print(len(keyphrases_set),chunk_length)

pool=mp.Pool(processes=num_of_cores)
outputs=pool.map(func=multi_function,iterable=chunks(keyphrases_set,chunk_length))
pool.close()
pool.join()

noc_in_literature_fname=working_dir+'noc_in_literature.pkl'
try:
	with open(noc_in_literature_fname,'rb') as f:
		noc_in_literature_dict=pickle.load(f)
except:
	noc_in_literature_dict=dict()

keyphrase_alias_dict=dict()
tmp_list=[]

final_outputs=[]

ii=0
for out in outputs:

	for list_item in out:
		list_item=sorted(list_item,key=lambda k: k[0])
		list_item=sorted(list_item,key=lambda k: k[1], reverse=True)
		string_item=str(list_item)
		if string_item not in final_outputs:
			final_outputs.append(string_item)

		if 'spike' in str(x):
			print(ii,x)

	ii+=1

outputs=[ast.literal_eval(x) for x in final_outputs]

for list_item in outputs:
	
	list_item=[li[0] for li in list_item]

	if len(list_item)==2:
		singular,plural=is_plural(list_item)

		if 'spike' in str(singular):
			print('sing v plural results:',singular,plural)

		if singular!=None:

			if singular not in noc_in_literature_dict:
				singular_noc=len(get_lmdb_semantic_scholar_IDs_from_keyphrase(singular))
				noc_in_literature_dict[singular]=singular_noc
			else:
				singular_noc=noc_in_literature_dict[singular]

			if plural not in noc_in_literature_dict:
				plural_noc=len(get_lmdb_semantic_scholar_IDs_from_keyphrase(plural))
				noc_in_literature_dict[plural]=plural_noc
			else:
				plural_noc=noc_in_literature_dict[plural]

			if singular_noc>=plural_noc:
				list_item=[singular,plural]
			else:
				list_item=[plural,singular]

			if 'spike' in str(singular):
				print(list_item,singular,singular_noc,plural,plural_noc)

		string_item=str(list_item)
		if string_item not in tmp_list:
			tmp_list.append(string_item)
			if len(list_item)==1:
				keyphrase_alias_dict[list_item[0]]=list_item[0]
			else:
				for i in list_item[1:]:
					keyphrase_alias_dict[i]=list_item[0]

keyphrase_alias_dict['brain']='brain'
keyphrase_alias_dict['brains']='brain'

keyphrase_alias_dict['excitatory-inhibitory balance']='E/I balance'
keyphrase_alias_dict['excitatory/inhibitory balance']='E/I balance'
keyphrase_alias_dict['excitatory - inhibitory balance']='E/I balance'
keyphrase_alias_dict['excitatory / inhibitory balance']='E/I balance'
keyphrase_alias_dict['Excitatory-inhibitory balance']='E/I balance'
keyphrase_alias_dict['Excitatory/inhibitory balance']='E/I balance'
keyphrase_alias_dict['Excitatory - inhibitory balance']='E/I balance'
keyphrase_alias_dict['Excitatory / inhibitory balance']='E/I balance'
keyphrase_alias_dict['Excitatory-Inhibitory balance']='E/I balance'
keyphrase_alias_dict['Excitatory/Inhibitory balance']='E/I balance'
keyphrase_alias_dict['Excitatory - Inhibitory balance']='E/I balance'
keyphrase_alias_dict['Excitatory / Inhibitory balance']='E/I balance'
keyphrase_alias_dict['e/i balance']='E/I balance'
keyphrase_alias_dict['e-i balance']='E/I balance'
keyphrase_alias_dict['e/i balance']='E/I balance'
keyphrase_alias_dict['e&i balance']='E/I balance'
keyphrase_alias_dict['e - i balance']='E/I balance'
keyphrase_alias_dict['e / i balance']='E/I balance'
keyphrase_alias_dict['e & i balance']='E/I balance'
keyphrase_alias_dict['ei balance']='E/I balance'
keyphrase_alias_dict['e i balance']='E/I balance'
keyphrase_alias_dict['E-I balance']='E/I balance'
keyphrase_alias_dict['E/I balance']='E/I balance'
keyphrase_alias_dict['E&I balance']='E/I balance'
keyphrase_alias_dict['E - I balance']='E/I balance'
keyphrase_alias_dict['E / I balance']='E/I balance'
keyphrase_alias_dict['E & I balance']='E/I balance'
keyphrase_alias_dict['EI balance']='E/I balance'
keyphrase_alias_dict['E I balance']='E/I balance'

with open(noc_in_literature_fname,'wb') as f:
	pickle.dump(noc_in_literature_dict,f)

'''for k,v in keyphrase_alias_dict.items():
	if k!=v:
		print(k,'->',v)
		print()'''

files=[raw_keyphrases_dir+x for x in os.listdir(raw_keyphrases_dir) if x.endswith('.pkl')]

all_aliases=list(set(keyphrase_alias_dict.values()))

most_frequent_kp_version_in_the_literature_fname=working_dir+'most_frequent_kp_version_in_the_literature.pkl'
try:
	with open(most_frequent_kp_version_in_the_literature_fname,'rb') as f:
		most_frequent_kp_version_in_the_literature_dict=pickle.load(f)
except:
	most_frequent_kp_version_in_the_literature_dict=dict()

dd=0
for kp in all_aliases:

	if kp in most_frequent_kp_version_in_the_literature_dict:
		continue

	original_kp=kp
	original_sem_ids=get_lmdb_semantic_scholar_IDs_from_keyphrase(kp)

	this_kp=None
	this_sem_ids=original_sem_ids

	if len(original_sem_ids)<=15:
		dd+=1
		kp_split_len=len(kp.split())

		if kp_split_len>=3 and kp_split_len<5:
			reduced_kp_version_1,reduced_kp_version_2=split_reduce_keyphrase_versions(kp)
			
			sem_ids_1=get_lmdb_semantic_scholar_IDs_from_keyphrase(reduced_kp_version_1)
			sem_ids_2=get_lmdb_semantic_scholar_IDs_from_keyphrase(reduced_kp_version_2)

			if len(sem_ids_1)>len(original_sem_ids) or len(sem_ids_2)>len(original_sem_ids):

				if len(sem_ids_1)>=len(sem_ids_2):
					this_kp=reduced_kp_version_1
					this_sem_ids=sem_ids_1
				
				else:
					this_kp=reduced_kp_version_2
					this_sem_ids=sem_ids_2
	
		elif kp_split_len>=5:
			
			reduced_kp_version_1,reduced_kp_version_2,reduced_kp_version_3,reduced_kp_version_4=split_reduce_keyphrase_versions_5(kp)

			sem_ids_1=get_lmdb_semantic_scholar_IDs_from_keyphrase(reduced_kp_version_1)
			sem_ids_2=get_lmdb_semantic_scholar_IDs_from_keyphrase(reduced_kp_version_2)
			sem_ids_3=get_lmdb_semantic_scholar_IDs_from_keyphrase(reduced_kp_version_3)
			sem_ids_4=get_lmdb_semantic_scholar_IDs_from_keyphrase(reduced_kp_version_4)

			sort_split_versions_by_hits=[
									[reduced_kp_version_1,sem_ids_1],
									[reduced_kp_version_2,sem_ids_2],
									[reduced_kp_version_3,sem_ids_3],
									[reduced_kp_version_4,sem_ids_4],
							]

			sort_split_versions_by_hits.sort(key=lambda x: len(x[1]),reverse=True)

			sort_split_sem_ids=sort_split_versions_by_hits[0][1]

			if len(sort_split_sem_ids)>len(original_sem_ids):
				this_kp=sort_split_versions_by_hits[0][0]
				this_sem_ids=sort_split_versions_by_hits[0][1]

	else:
		this_kp=original_kp

	if this_kp==None and len(original_sem_ids)>=4:
		this_kp=original_kp

	if this_kp!=None:

		most_freq_kp_version=get_most_frequent_version_in_the_literature(this_kp,this_sem_ids)
		most_frequent_kp_version_in_the_literature_dict[this_kp]=most_freq_kp_version

most_frequent_kp_version_in_the_literature_dict['excitatory-inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['excitatory/inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['excitatory - inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['excitatory / inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['Excitatory-inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['Excitatory/inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['Excitatory - inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['Excitatory / inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['Excitatory-Inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['Excitatory/Inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['Excitatory - Inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['Excitatory / Inhibitory balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['e/i balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['e-i balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['e/i balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['e&i balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['e - i balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['e / i balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['e & i balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['ei balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['e i balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['E-I balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['E/I balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['E&I balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['E - I balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['E / I balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['E & I balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['EI balance']='E/I balance'
most_frequent_kp_version_in_the_literature_dict['E I balance']='E/I balance'

with open(most_frequent_kp_version_in_the_literature_fname,'wb') as f:
	pickle.dump(most_frequent_kp_version_in_the_literature_dict,f)

t22=time.time()

print('I just curated all available keyphrases. It took:', t22-t11, 'sec')

for k,v in processed_keyphrases_dict.items():

	unique_id=k
	keyphrases=v

	keyphrases=[keyphrase_alias_dict[x] for x in keyphrases if x in keyphrase_alias_dict]
	keyphrases=[most_frequent_kp_version_in_the_literature_dict[x] for x in keyphrases if x in most_frequent_kp_version_in_the_literature_dict]
	keyphrases=list(set(keyphrases))

	if len(keyphrases)>0:
		write_keyphrases_to_file(keyphrases,unique_id)
