import sys,os,re,pickle,time,json,itertools
from pprint import pprint
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def myround(x,base):
	return base*round(x/base)

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

def get_matching_seeker_info(uuid):

	seeker_dict=dict()
	
	with open(home+'/Dropbox/websites/world-wide.org/jobs/s/'+uuid+'/listing_data.json','r') as f:
		listing_data=json.load(f)

	seeker_name=listing_data['Full Name']
	looking_for=listing_data['Looking for']
	#keywords=listing_data['Keywords']

	seeker_dict['seeker_name']=seeker_name
	seeker_dict['looking_for']=looking_for
	#seeker_dict['keywords']=keywords
	seeker_dict['url']='https://www.world-wide.org/jobs/s/'+uuid

	return seeker_dict

def get_matching_employer_info(uuid):

	employer_dict=dict()
	
	with open(home+'/Dropbox/websites/world-wide.org/jobs/e/'+uuid+'/listing_data.json','r') as f:
		listing_data=json.load(f)

	job_type=listing_data['Job Type']
	employer_name=listing_data['Full Name']
	affiliation=listing_data['Affiliation']
	#keywords=listing_data['Keywords']

	employer_dict['job_type']=job_type
	employer_dict['employer_name']=employer_name
	employer_dict['affiliation']=affiliation
	#employer_dict['keywords']=keywords
	employer_dict['url']='https://www.world-wide.org/jobs/e/'+uuid

	return employer_dict

def get_matching_seminar_info(uuid):

	seminar_dict=dict()

	for k,v in seminar_data.items():
		if v['calendar_event_hash']==uuid:
			this_seminar_data=v
			break

	seminar_title=this_seminar_data['seminar_title']
	seminar_speaker=this_seminar_data['seminar_speaker']
	speaker_title=this_seminar_data['speaker_title']
	speaker_affil=this_seminar_data['speaker_affil']
	#keywords=this_seminar_data['topic_tags']
	seminar_id=this_seminar_data['seminar_id']

	seminar_dict['seminar_title']=seminar_title
	seminar_dict['seminar_speaker']=seminar_speaker
	seminar_dict['speaker_title']=speaker_title
	seminar_dict['speaker_affil']=speaker_affil
	#seminar_dict['keywords']=keywords
	seminar_dict['url']='https://www.world-wide.org/seminar/'+str(seminar_id)

	return seminar_dict

from pathlib import Path
home = str(Path.home())

ww_dir=home+'/Dropbox/websites/world-wide.org/'
pairwise_similarity_dir=home+'/Dropbox/websites/world-wide.org/python_scripts/'
jobs_dir=home+'/Dropbox/websites/world-wide.org/jobs/'
job_embeddings_dir=home+'/Dropbox/websites/world-wide.org/embeddings/jobs/'
seminar_embeddings_dir=home+'/Dropbox/websites/world-wide.org/embeddings/seminars/'

job_embeddings=[[job_embeddings_dir+x,x[:-4]] for x in os.listdir(job_embeddings_dir) if x.endswith('.pkl')]
seminar_embeddings=[[seminar_embeddings_dir+x,x[:-4]] for x in os.listdir(seminar_embeddings_dir) if x.endswith('.pkl')]

element_ids_and_embeddings=[]

for x in job_embeddings + seminar_embeddings:

	fname=x[0]
	uid=x[1]

	with open(fname,'rb') as f:
		data=pickle.load(f)
	
	element_ids_and_embeddings.append(data)


el_embeddings=[x[1][0] for x in element_ids_and_embeddings]
pairwise_similarities=cosine_similarity(el_embeddings)

sim_score_threshold=0.6  # 0.825

pairwise_dict=dict()
for x in range(len(pairwise_similarities)):

	pairwise_list=[]
	for y in range(len(pairwise_similarities)):

		if x==y:
			continue
		uid=element_ids_and_embeddings[y][0]
		sim_score=pairwise_similarities[x][y]
		if sim_score>=sim_score_threshold:
			pairwise_list.append([uid,sim_score])
	
	pairwise_list.sort(key=lambda x: x[1], reverse=True)

	if len(pairwise_list)>0:
	
		pairwise_dict[element_ids_and_embeddings[x][0]]=pairwise_list

with open(jobs_dir+'active_seeker_listings.json','r') as f:
	active_seekers=json.load(f)

with open(jobs_dir+'active_curious_listings.json','r') as f:
	active_curious=json.load(f)

with open(jobs_dir+'active_employer_listings.json','r') as f:
	active_employers=json.load(f)

with open(home+'/Dropbox/websites/world-wide.org/seminar_data.json','r') as f:
	seminar_data=json.load(f)

seminar_listings=[v for k,v in seminar_data.items() if 'video_on_demand' in v and v['hosted_by'] not in ['Ad hoc','SMARTSTART Midsummer Brains','WWNDev','Learning Salon','ISAM-NIG Webinars']]
seminar_listings=[v['calendar_event_hash'] for v in seminar_listings if len(v['video_on_demand'])>5]

seekers_matching_data=dict()

for x in active_seekers:

	seeker_is_looking_for=get_matching_seeker_info(x)['looking_for']

	matching_employers=[]
	matching_seminars=[]

	if x in pairwise_dict:

		seekers_matching_data[x]=dict()

		pairwise_data=pairwise_dict[x]

		for uuid,sim_score in pairwise_data:

			if uuid in active_employers:
				employer_info=get_matching_employer_info(uuid)
				if len(set.intersection(set(seeker_is_looking_for),set(employer_info['job_type'])))>0:
					matching_employers.append(employer_info)

			if uuid in seminar_listings:
				seminar_info=get_matching_seminar_info(uuid)
				matching_seminars.append(seminar_info)

	if len(matching_employers)>0:
		seekers_matching_data[x]['matching_employers']=matching_employers[:3]
	if len(matching_seminars)>0:
		seekers_matching_data[x]['matching_seminars']=matching_seminars[:3]

if if_json_file_is_not_the_same_or_doesnt_exist(jobs_dir+'seekers_matching_data.json',seekers_matching_data):

	with open(jobs_dir+'seekers_matching_data.json', 'w') as f:
		json.dump(seekers_matching_data,f)

	os.system('/usr/local/bin/aws s3 cp ' + jobs_dir + 'seekers_matching_data.json s3://www.world-wide.org/jobs/')


employers_matching_data=dict()

for x in active_employers:

	employer_is_looking_for=get_matching_employer_info(x)['job_type']

	matching_seekers=[]
	matching_seminars=[]

	if x in pairwise_dict:

		employers_matching_data[x]=dict()

		pairwise_data=pairwise_dict[x]

		for uuid,sim_score in pairwise_data:

			if uuid in active_seekers:
				seeker_info=get_matching_seeker_info(uuid)
				if len(set.intersection(set(employer_is_looking_for),set(seeker_info['looking_for'])))>0:
					matching_seekers.append(seeker_info)

			if uuid in seminar_listings:
				seminar_info=get_matching_seminar_info(uuid)
				#seminar_info['matching_score']=sim_score
				matching_seminars.append(seminar_info)

	if len(matching_seekers)>0:
		employers_matching_data[x]['matching_seekers']=matching_seekers[:3]
	if len(matching_seminars)>0:
		employers_matching_data[x]['matching_seminars']=matching_seminars[:3]

if if_json_file_is_not_the_same_or_doesnt_exist(jobs_dir+'employers_matching_data.json',employers_matching_data):

	with open(jobs_dir+'employers_matching_data.json', 'w') as f:
		json.dump(employers_matching_data,f)

	os.system('/usr/local/bin/aws s3 cp ' + jobs_dir + 'employers_matching_data.json s3://www.world-wide.org/jobs/')

seminars_matching_data=dict()

for x in seminar_listings:

	matching_seekers=[]
	matching_employers=[]
	matching_seminars=[]

	if x in pairwise_dict:

		seminars_matching_data[x]=dict()

		pairwise_data=pairwise_dict[x]

		for uuid,sim_score in pairwise_data:

			if uuid in active_seekers:
				seeker_info=get_matching_seeker_info(uuid)
				matching_seekers.append(seeker_info)

			if uuid in active_employers:
				employer_info=get_matching_employer_info(uuid)
				employer_info['matching_score']=myround(sim_score,0.0005)
				matching_employers.append(employer_info)

			if uuid in seminar_listings:
				seminar_info=get_matching_seminar_info(uuid)
				seminar_info['matching_score']=myround(sim_score,0.0005)
				matching_seminars.append(seminar_info)

	#if len(matching_seekers)>0:
	#	seminars_matching_data[x]['matching_seekers']=matching_seekers
	if len(matching_employers)>0:
		seminars_matching_data[x]['matching_employers']=matching_employers[:2]
	if len(matching_seminars)>0:
		seminars_matching_data[x]['matching_seminars']=matching_seminars[:3]

if if_json_file_is_not_the_same_or_doesnt_exist(ww_dir+'seminars_matching_data.json',seminars_matching_data):

	with open(ww_dir+'seminars_matching_data.json', 'w') as f:
		json.dump(seminars_matching_data,f)

	os.system('/usr/local/bin/aws s3 cp ' + ww_dir + 'seminars_matching_data.json s3://www.world-wide.org/')

#pprint(seminars_matching_data)

sys.exit()

with open(pairwise_similarity_dir+'pairwise_sim_dict.pkl','wb') as f:
	pickle.dump(pairwise_dict,f)