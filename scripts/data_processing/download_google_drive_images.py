import os,sys,re,pickle,json,time,uuid,io
from pprint import pprint
from pathlib import Path

from apiclient.discovery import build
from google.oauth2.service_account import Credentials
from apiclient.http import MediaIoBaseDownload

from urllib.parse import urlparse

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

def download_file_from_gdrive(file_id):

	try:
		file_details = drive_service.files().get(fileId=file_id).execute()
	except Exception as e:
		print('='*80)
		print(e)
		print('Error getting file details from Google Drive')
		print(file_id)
		print('Perhaps, it\'s restricted, the owner must share it with anybody who gets the link -- you need to let them know and ask them to change that sharing setting and subsequently update the GDrive link in the GSheet')
		print('='*80)
		return None

	file_extension=file_details['name'].split('.')[-1]

	ww_img_name=str(uuid.uuid4())+'.'+file_extension
	while os.path.isfile(images_dir+ww_img_name):
		ww_img_name=str(uuid.uuid4())+'.'+file_extensions

	request = drive_service.files().get_media(fileId=file_id)
	fh = io.BytesIO()
	downloader = MediaIoBaseDownload(fh, request)
	done = False
	while done is False:
		status, done = downloader.next_chunk()
	with open(images_dir + ww_img_name, 'wb') as f:
		fh.seek(0)
		f.write(fh.read())
	fh.close()

	return ww_img_name

def get_file_id_from_gdrive_url(gdrive_url):
	try:
		# https://drive.google.com/file/d/1DtxNJaJFglKGRn1MJnIgn0fKzuZZFyka/view
		file_id=re.search('(?<=file/d/).*(?=/view)',gdrive_url).group(0)
	except:
		return None

	return file_id

def download_image_from_twitter(media_url):

	print(media_url)

	#https://pbs.twimg.com/media/FD7jt3JXIAoTKQu

	url_obj = urlparse(media_url)
	
	print(url_obj)

	file_name = url_obj.path.replace("/media/", "")
	'''path = str(Path(photo_location, file_name))
	if not Path(path).is_file():
		with open(path, "wb") as file:
			file.write(requests.get(photo_url).content)'''

	sys.exit()

	ww_img_name=str(uuid.uuid4())+'.'+file_extension
	while os.path.isfile(images_dir+ww_img_name):
		ww_img_name=str(uuid.uuid4())+'.'+file_extensions

	request = drive_service.files().get_media(fileId=file_id)
	fh = io.BytesIO()
	downloader = MediaIoBaseDownload(fh, request)
	done = False
	while done is False:
		status, done = downloader.next_chunk()
	with open(images_dir + ww_img_name, 'wb') as f:
		fh.seek(0)
		f.write(fh.read())
	fh.close()

	return ww_img_name

CLIENT_SECRET_FILE = str(Path.home())+'/Dropbox/credentials/sincere-amulet-333317-c4d8e3b733f0.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

service_account_info = json.load(open(CLIENT_SECRET_FILE))
creds=Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=creds)

#{'kind': 'drive#file', 'id': '1DtxNJaJFglKGRn1MJnIgn0fKzuZZFyka', 'name': 'NMC_Logo.PNG', 'mimeType': 'image/png'}
#file_id = '1DtxNJaJFglKGRn1MJnIgn0fKzuZZFyka'

working_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/'
images_dir=working_dir + 'images/'
scripts_dir=working_dir+'python_scripts/'

with open(working_dir+'seminar_data.json','r') as json_file:
	seminar_data = json.load(json_file)

# Load gdrive_img_url_to_local_path dict
try:
	with open(scripts_dir+'gdrive_img_urls_to_world_wide_path.pkl', 'rb') as f:
		gdrive_img_urls_to_world_wide_path = pickle.load(f)
except:
	gdrive_img_urls_to_world_wide_path = dict()

# Iterate over seminar data and get the "Banner Ad" image urls hosted on Google Drive

banner_ads=[v['Banner Ad'] for v in seminar_data.values() if 'Banner Ad' in v]
banner_ads=[v for v in banner_ads if len(v)>=5]

'''twitter_banner_ads=[v for v in banner_ads if img_is_hosted_on_twitter(v)]
twitter_banner_ads=list(set(twitter_banner_ads))

for twitter_banner_ad in twitter_banner_ads:
	print(twitter_banner_ad)
	download_image_from_twitter(twitter_banner_ad)
	sys.exit()'''

gdrive_banner_ads=[v for v in banner_ads if img_is_hosted_on_gdrive(v)]
gdrive_banner_ads=list(set(gdrive_banner_ads))

img_file_ids=[get_file_id_from_gdrive_url(img_url) for img_url in gdrive_banner_ads]
img_file_ids=[file_id for file_id in img_file_ids if file_id is not None]
img_file_ids=[file_id for file_id in img_file_ids if file_id not in gdrive_img_urls_to_world_wide_path]
download_these_gdrive_images=list(set(img_file_ids))

if len(download_these_gdrive_images)==0:
	sys.exit()

for file_id in img_file_ids:

	ww_img_name=download_file_from_gdrive(file_id)
	if ww_img_name is None:
		continue
	ww_img_url='https://www.world-wide.org/images/'+ww_img_name
	gdrive_img_urls_to_world_wide_path[file_id]=ww_img_url

with open(scripts_dir+'gdrive_img_urls_to_world_wide_path.pkl', 'wb') as f:
	pickle.dump(gdrive_img_urls_to_world_wide_path, f)

upload_images_script_path=scripts_dir+'upload_new_images_and_get_links.py'
python3_path=sys.executable

cmd=python3_path+' '+upload_images_script_path

os.system(cmd)