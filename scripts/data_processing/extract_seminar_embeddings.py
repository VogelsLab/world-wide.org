import sys,os,re,pickle,time,json,itertools
import numpy as np

from pprint import pprint
from collections import Counter

def write_embedding_to_file(embedding,unique_id):

	with open(embeddings_dir+unique_id+'.pkl','wb') as f:
		pickle.dump([unique_id,embedding],f)

def write_keyphrases_to_file(raw_keyphrases,unique_id):

	with open(keyphrases_dir+unique_id+'.pkl','wb') as f:
		pickle.dump([unique_id,raw_keyphrases],f)

from pathlib import Path
home = str(Path.home())

keyphrases_dir=home+'/Dropbox/websites/world-wide.org/keyphrases/seminars/raw/'
embeddings_dir=home+'/Dropbox/websites/world-wide.org/embeddings/seminars/'

with open(home+'/Dropbox/websites/world-wide.org/seminar_data.json','r') as f:
	seminar_data=json.load(f)

processed_seminar_ids=[x[:-4] for x in os.listdir(embeddings_dir) if x.endswith('.pkl')]
#processed_seminar_ids=[]

seminars_to_process=[]

for k,v in seminar_data.items():

	this_seminar_data=seminar_data[k]
	this_seminar_unique_id=this_seminar_data['calendar_event_hash']

	if this_seminar_unique_id in processed_seminar_ids:
		continue
	
	if this_seminar_data['hosted_by']=='WWNDev':
		continue

	if len(this_seminar_data['seminar_title'])>10 and len(this_seminar_data['seminar_abstract'])>200:
		
		raw_text=this_seminar_data['seminar_title'] + '. '
		raw_text+=this_seminar_data['seminar_abstract'] + ' '
		raw_text+=', '.join(this_seminar_data['topic_tags'])
		raw_text=raw_text.strip()
		raw_text=re.sub(r'\s\s+',' ',raw_text.lower())
		
		seminars_to_process.append([this_seminar_unique_id,raw_text])

# sys.exit()

# seminars_to_process=[['cd490d9d511f60418463a9f4f8101e40d1338606593ce0fbddee79f1d047eb6c',"Metabolic spikes: from rogue electrons to Parkinson's. Conventionally, neurons are thought to be cellular units that process synaptic inputs into synaptic spikes. However, it is well known that neurons can also spike spontaneously and display a rich repertoire of firing properties with no apparent functional relevance e.g. in in vitro cortical slice preparations. In this talk, I will propose a hypothesis according to which intrinsic excitability in neurons may be a survival mechanism to minimize toxic byproducts of the cell’s energy metabolism. In neurons, this toxicity can arise when mitochondrial ATP production stalls due to limited ADP. Under these conditions, electrons deviate from the electron transport chain to produce reactive oxygen species, disrupting many cellular processes and challenging cell survival. To mitigate this, neurons may engage in ADP-producing metabolic spikes. I will explore the validity of this hypothesis using computational models that illustrate the implications of synaptic and metabolic spiking, especially in the context of substantia nigra pars compacta dopaminergic neurons and their degeneration in Parkinson's disease."]]

if len(seminars_to_process)>0:

	seminar_unique_ids=[x[0] for x in seminars_to_process]
	print('I will get recommendations for these entries:', seminar_unique_ids)

	os.system('/bin/cp /home/pbozelos/Dropbox/keyphrase_extraction_algorithms/embed_rank/config.ini.copy /home/pbozelos/Dropbox/keyphrase_extraction_algorithms/embed_rank/config.ini')

	module_dir=home+'/Dropbox/keyphrase_extraction_algorithms/embed_rank/'
	os.chdir(module_dir)
	sys.path.insert(1, module_dir)  # the type of path is string

	import get_embeddings,launch
	from swisscom_ai.research_keyphrase.model.input_representation import InputTextObj

	embedding_distributor = get_embeddings.load_local_embedding_distributor()
	pos_tagger = get_embeddings.load_local_corenlp_pos_tagger()

	working_dir=home+'/Dropbox/websites/world-wide.org/python_scripts/'

	os.chdir(working_dir)

	for x in seminars_to_process:

		unique_id=x[0]
		raw_text=x[1]

		tagged = pos_tagger.pos_tag_raw_text(raw_text)
		text_obj = InputTextObj(tagged, 'en').filtered_pos_tagged

		tokenized_doc_text = ' '.join(token[0].lower() for sent in text_obj for token in sent)
		embedding = embedding_distributor.get_tokenized_sents_embeddings([tokenized_doc_text])
		write_embedding_to_file(embedding,unique_id)
		raw_keyphrases = launch.extract_keyphrases(embedding_distributor, pos_tagger, raw_text, 50, 'en')

		write_keyphrases_to_file(raw_keyphrases,unique_id)
