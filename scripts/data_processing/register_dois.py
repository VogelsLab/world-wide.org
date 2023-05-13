import os,sys,re,json,time,datetime,xmltodict,requests,uuid,pickle
from datacite import DataCiteRESTClient, schema42
import glob, json, datetime, re, getpass
import requests

from pprint import pprint

# EXAMPLE POSTER BRIEF DATA
'''
"poster_id": "4be12230",
"poster_title": "One engram, two ways to recall it",
"poster_authors": "Mehrab Modi,Adithya Rajagopalan,Hervé Rouault,Yoshinori Aso,Glenn Turner",
"poster_abstract": "Animals learn when punishment or reward is predicted by neutral stimuli like tones or odors. Synaptic plasticity maps the predictor to the appropriate behavioral drive, forming a memory trace. But if the predictor is presented as one of two options, the optimal response is uncertain and depends on the alternative. Can a single memory trace evoke different behaviors, depending on stimulus context? We used optogenetics in Drosophila to form an odor-punishment association restricted to a single set of synapses, ie. a single memory trace. These flies showed flexible behavioral responses to a given odor stimulus. Depending on the choice, flies either generalized the association from the learned odor (A) to an unreinforced, similar odor (A’), or discriminated between them. We measured neuronal activity in the fly memory circuit, the mushroom body. The mushroom body output neuron (MBON) downstream of the memory trace had indistinguishable responses to single pulses of odors A and A’ - generalizing across them. But if odors were presented as transitions from A to A’, mimicking the fly crossing an odor boundary, MBON responses to A’ were dramatically altered, allowing discrimination. Receiving odors in a specific sequence caused the MB circuit to alter the output of the memory trace. We tested this behaviorally. When odors were presented singly, flies responded to the punished odor, A and A’ indistinguishably. Only when A transitioned into A’, fly behavior switched and they were attracted to A’. An association assigns valence or meaning to a stimulus. But valence is subjective and ever-changing, depending on ongoing events in the environment. Our study reveals a novel way for animals to modulate how a test stimulus evokes behavior, based on ongoing stimulus dynamics. This is an important step to move beyond a plasticity-centric view of memory recall.",
"timestamp": "1647360612040",
"requested_doi": true,
"brief": true,
"url_link": "https://www.world-wide.org/cosyne-22/engram-ways-recall-4be12230",
"first_name": "Mehrab",
"last_name": "Modi",
"email": "modim@janelia.hhmi.org",
"lab_website": "https://www.janelia.org/lab/turner-lab",
"twitter_profile": "",
"video_audio": "video"
'''

def register_doi():

	already_registered_dois=[x[0] for x in already_registered_dois_and_respective_timestamps]

	proposed_doi=None

	standard_suffix='ww-'

	while proposed_doi is None or proposed_doi in already_registered_dois:	

		short_uuid = str(uuid.uuid4())[:8]
		proposed_doi = standard_suffix + short_uuid[:4] + '-' + short_uuid[4:]

		print('Proposed DOI: ' + proposed_doi)

	print('The DOI is available, good: ' + proposed_doi)
	
	return proposed_doi

def delete_dois(dois_to_be_deleted):

	if isinstance(dois_to_be_deleted, str):
		dois_to_be_deleted = [dois_to_be_deleted]
	
	for doi in dois_to_be_deleted:
	
		try:
	
			try:
				with open('doi_dir/already_registered_dois_and_respective_timestamps.pkl', 'rb') as f:
					already_registered_dois_and_respective_timestamps = pickle.load(f)
			except:
				already_registered_dois_and_respective_timestamps = []
	
			already_registered_dois=[x[0] for x in already_registered_dois_and_respective_timestamps]

			if doi in already_registered_dois:

				print('Deleting DOI: ' + doi)
				dc_client.delete_doi(doi)

				already_registered_dois_and_respective_timestamps = [x for x in already_registered_dois_and_respective_timestamps if x[0] != doi]

				with open('doi_dir/already_registered_dois_and_respective_timestamps.pkl', 'wb') as f:
					pickle.dump(already_registered_dois_and_respective_timestamps, f)
			
			else:

				print('DOI not found in the local list of registered DOIs')
				print('Skipping deletion...')
				print()

		except Exception as e:
			print('-------------------------------------------------------')
			print('Error: ' + str(e))
			print()
			print('Exiting...')
			print('-------------------------------------------------------')
			sys.exit()

def get_registered_dois_sorted_by_timestamp():

	with open('doi_dir/already_registered_dois_and_respective_timestamps.pkl', 'rb') as f:
		already_registered_dois_and_respective_timestamps = pickle.load(f)

	already_registered_dois_and_respective_timestamps.sort(key=lambda x: x[1])

	for doi,timestamp in already_registered_dois_and_respective_timestamps:

		human_readable_timestamp = datetime.datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
		print('DOI: ' + doi + ' registered on ' + human_readable_timestamp)

	return already_registered_dois_and_respective_timestamps

def write_metadata_to_file(metadata, doi):
	xml = schema42.tostring(metadata)

	outname = f.split(".xml")[0] + "_datacite.xml"
	outfile = open(outname, "w", encoding="utf8")
	outfile.write(xml)

def get_metadata(brief_data,url_link_to_brief):

	metadata = {}

	# Add the authors
	# split the poster_authors string into a list of authors -- delimited by commas
	poster_authors = brief_data["poster_authors"].split(",")
	poster_authors = [x.strip() for x in poster_authors]

	authors_creators = []
	for poster_author in poster_authors:
		author_item = {}
		author_item["name"] = poster_author
		authors_creators.append(author_item)
	
	metadata["creators"] = authors_creators
	
	metadata["titles"] = [
			{ 
				'title':brief_data["poster_title"]
			}
		]
	
	metadata["publisher"] = "Science Communications World Wide"
	
	metadata["publicationYear"] = '2022'

	metadata["types"] = {
		"resourceType": "Conference Brief",
		"resourceTypeGeneral": "Audiovisual"
	}

	metadata["descriptions"] = [
			{
				"descriptionType": "Abstract",
				"description": brief_data["poster_abstract"]
			}
		]

	metadata["language"] = "English"

	proposed_doi=register_doi()

	# set the DOI identifier now
	metadata["identifiers"] = [
			{
				"identifier": proposed_doi,
				"identifierType": "DOI"
			}
		]

	# Subjects
	'''subject_set = set()
	if "keywords" in eprint:
		subjects = eprint["keywords"].split(";")
		if len(subjects) == 1:
			subjects = eprint["keywords"].split(",")
		for s in subjects:
			subject_set.add(s.strip())'''

	#metadata["Subject"] = [ "Computational Neuroscience" ]

	#metadata["Rights"] = "Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)"
	
	'''# Dates
	dates = []
	dates.append({"date": ## fill-in, "dateType": "Available"})
	metadata["dates"] = dates'''

	# Identifiers
	'''identifiers = []
	if "doi" in eprint:
		identifiers.append({"identifier": eprint["doi"], "identifierType": "DOI"})

	metadata["identifiers"] = identifiers'''

	metadata["schemaVersion"] = "http://datacite.org/schema/kernel-4"
	# metadata["additionalProperties"]=True

	return metadata,proposed_doi

from pathlib import Path

home=str(Path.home())
credentials_dir=home+'/Dropbox/credentials/'
world_wide_dir=home+'/Dropbox/websites/world-wide.org/'
cosyne_dir=world_wide_dir+'cosyne-22/'

# load poster submissions file
with open(cosyne_dir+'all_submissions.json') as f:
	poster_brief_submissions = json.load(f)

'''for poster_brief in poster_brief_submissions:
	poster_title = poster_brief["poster_title"]
	pprint(poster_brief)
'''

try:
	with open('doi_dir/already_registered_dois_and_respective_timestamps.pkl', 'rb') as f:
		already_registered_dois_and_respective_timestamps = pickle.load(f)
except:
	already_registered_dois_and_respective_timestamps = []

# load credentials
with open(credentials_dir+'datacite_credentials.json') as json_file:
	credentials = json.load(json_file)

datacite_SCIWW_repo=credentials["datacite_SCIWW_repo"]
datacite_SCIWW_repo_password=credentials["datacite_SCIWW_repo_password"]
datacite_SCIWW_repo_prefix=credentials["datacite_SCIWW_repo_prefix"]

print()
print('Datacite SCIWW repo: '+datacite_SCIWW_repo)
print('Datacite SCIWW repo prefix: '+datacite_SCIWW_repo_prefix)
print()

mint=True # Mint DOIs
test_mode=True # Only register test DOI

if test_mode == True:
	# Existing test record
	dc_client = DataCiteRESTClient(
		username=datacite_SCIWW_repo,
		password=datacite_SCIWW_repo_password,
		prefix=datacite_SCIWW_repo_prefix
		#test_mode=True,
	)
else:
	dc_client = DataCiteRESTClient(
		username=datacite_SCIWW_repo,
		password=datacite_SCIWW_repo_password,
		prefix=datacite_SCIWW_repo_prefix,
	)

# doi_to_delete=['10.57736/ww-f72c-f1f5','10.57736/ww-8a57-ab5a','10.57736/ww-b166-dd1b','10.57736/ww-0605-4a8d','10.57736/ww-0605-4a8d','10.57736/ww-5882-3b75','10.57736/ww-5882-3b75']
# delete_dois(doi_to_delete)

'''with open('doi_dir/already_registered_dois_and_respective_timestamps.pkl', 'rb') as f:
	already_registered_dois_and_respective_timestamps = pickle.load(f)

dois_to_delete = [x[0] for x in already_registered_dois_and_respective_timestamps]

delete_dois(dois_to_delete)
'''

try:
	with open('doi_dir/poster_ids_to_dois_and_urls.pkl', 'rb') as f:
		poster_ids_to_dois_and_urls = pickle.load(f)
except:
	poster_ids_to_dois_and_urls = {}

draft_status=False
public_status=True

for brief_data in poster_brief_submissions:

	#pprint(brief_data)

	if 'requested_doi' not in brief_data:
		continue
	
	if brief_data["requested_doi"] == False:
		continue

	print()
	print()
	print('============================================================')
	print()
	print()

	poster_id=brief_data["poster_id"]

	print('poster_id: '+poster_id)

	#if poster_id in poster_ids_to_dois_and_urls:
	#	print('Already registered: '+poster_id)
	#	continue

	url_link_to_brief = brief_data["url_link"]
	# pprint(brief_data)

	metadata,proposed_doi=get_metadata(brief_data,url_link_to_brief)

	update_status=False
	if poster_id=="2cf75432":
		proposed_doi="ww-e49b-6195"
		update_status=True
	
	if poster_id=="f1606980":
		proposed_doi="ww-ceef-5f77"
		update_status=True
	
	if poster_id=="a640cfd5":
		proposed_doi="ww-63de-19e0"
		update_status=True

	if poster_id=="c06fa72a":
		proposed_doi="ww-ceef-5f77"
		update_status=True
	
	if poster_id=="9d9a6f56":
		proposed_doi="ww-67fc-50c8"
		update_status=True

	if poster_id in poster_ids_to_dois_and_urls:
		proposed_doi=poster_ids_to_dois_and_urls[poster_id]["doi"]

	print('Poster ID: '+poster_id,' -- proposed DOI: '+proposed_doi)

	valid = schema42.validate(metadata)

	if valid == False:
		v = schema42.validator.validate(metadata)
		errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
		for error in errors:
			print(error.message)
		
		if len(errors) > 0:
			print()
			print('Exiting ...')
			print()
			sys.exit()

	poster_ids_to_dois_and_urls[poster_id]={
		"doi": proposed_doi,
		"url": url_link_to_brief,
		"draft_status": draft_status,
		"public_status": public_status
	}

	with open('doi_dir/poster_ids_to_dois_and_urls.pkl', 'wb') as f:
		pickle.dump(poster_ids_to_dois_and_urls, f)
	
	print("URL associated with the proposed DOI saved to local registry")

	if update_status == True:

		registered_doi = dc_client.update_doi(proposed_doi, metadata=metadata, url=url_link_to_brief)
		this_registered_doi = registered_doi["doi"]
		print('Metadata and URL successfully updated for DOI: ', this_registered_doi)
		print('Visit this DOI at: https://doi.org/', this_registered_doi)
	
	else:
	
		if draft_status==False and public_status==True:
	
			registered_doi = dc_client.public_doi(metadata=metadata,doi=proposed_doi,url=url_link_to_brief)
			this_registered_doi = registered_doi
			print('DOI registered in the public domain: ', this_registered_doi)
			print('Visit this DOI at: https://doi.org/', this_registered_doi)
	
		else:
	
			this_registered_doi = dc_client.draft_doi(metadata=None,doi=proposed_doi,url=url_link_to_brief)
			print('DOI registered as draft: ' + this_registered_doi)

	# get unix timestamp in milliseconds
	unix_timestamp = int(time.time() * 1000)

	already_registered_dois_and_respective_timestamps.append([this_registered_doi,unix_timestamp])

	with open('doi_dir/already_registered_dois_and_respective_timestamps.pkl', 'wb') as f:
		pickle.dump(already_registered_dois_and_respective_timestamps, f)
	
	print('DOI registration saved to the local registry')

	

	


'''# Debugging if verification fails
if valid == False:
v = schema43.validator.validate(metadata)
errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
for error in errors:
print(error.message)
sys.exit()


# What record in eprints are we dealing with?
record_number = eprint["eprintid"]

# Get our DataCite password
infile = open("pw", "r")
password = infile.readline().strip()



metadata["identifier"] = {
	"identifier": doi, ## fill-in,
	"identifierType": "DOI"
}

# IF DOI ALREADY EXISTS, UPDATE
d.update_doi(doi, metadata)
print("This DOI will be updated: " + doi+"\n")
print("Metadata: " + str(metadata) + "\n")

# IF DOI DOES NOT EXIST, CREATE
# if test_mode is true

if mint == True:	
	d.create_doi(metadata)
	print("This DOI will be created: " + doi+"\n")
	print("Metadata: " + str(metadata) + "\n")
else:
	pass

brief_url = bu ## fill-in

# Create a public DOI
datacite_request_response = d.public_doi(metadata=metadata)
# Create a draft DOI
datacite_request_response = d.draft_doi(metadata=metadata)
# Create a private DOI
datacite_request_response = d.private_doi(metadata=metadata)

# Update the metadata or url for a given DOI
datacite_request_response = update_doi(doi, metadata=metadata)
# Update the url of a given DOI
datacite_request_response = update_url(doi, url)'''