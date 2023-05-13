# pip install pillow
import sys,os,hashlib,pickle
#from PIL import Image, ImageDraw
 
'''img = Image.new('RGB', (100, 30), color = (73, 109, 137))
 
d = ImageDraw.Draw(img)
d.text((10,10), "Hello World", fill=(255,255,0))
 
img.save('pil_text.png')

from PIL import Image, ImageDraw, ImageFont
 
img = Image.new('RGB', (100, 30), color = (73, 109, 137))
 
fnt = ImageFont.truetype('/Library/Fonts/Arial.ttf', 15)
d = ImageDraw.Draw(img)
d.text((10,10), "Hello world", font=fnt, fill=(255, 255, 0))
 
img.save('pil_text_font.png')'''

### <----> https://haptik.ai/tech/putting-text-on-image-using-python/
 
from PIL import Image, ImageDraw, ImageFont
from pprint import pprint
from pathlib import Path
# create Image object with the input image

this_domain='Neuro/'
domain_dir=str(Path.home()) + '/Dropbox/websites/world-wide.org/' + this_domain

if not os.path.exists(domain_dir+'/meta_cards'):
	os.makedirs(domain_dir+'/meta_cards')

try:
	with open(domain_dir+'/card_images/processed_cards.pkl','rb') as f:
		processed_cards=pickle.load(f)
except:
	processed_cards=[]

def is_actual_image_file(x):
	bad_fnames=['processed_cards','cropped','DS_Store']
	for i in bad_fnames:
		if i in x:
			return False
	return True

files=[x for x in os.listdir(domain_dir+'card_images/') if is_actual_image_file(x) and x not in processed_cards]

i=0
for x in files:

	fname=domain_dir+'card_images/'+x

	basename,file_extension=os.path.splitext(fname)

	im = Image.open(fname)
	width, height = im.size   # Get dimensions

	ratio=1.001

	new_width=width
	new_height=height

	while new_width<=1200:
		new_width=ratio*new_width
		new_height=ratio*new_height

	while new_width>1205:
		new_width=1/ratio*new_width
		new_height=1/ratio*new_height
	
	im = im.resize((int(new_width), int(new_height)), Image.ANTIALIAS)

	left = (new_width - 1200)/2
	top = (new_height - 628)/2
	right = (new_width + 1200)/2
	bottom = (new_height + 628)/2

	# Crop the center of the image
	cropped_im = im.crop((left, top, right, bottom))

	string_to_digest=x
	bytes_to_digest=bytes(string_to_digest.encode())
	unique_hash_fname=hashlib.sha256(bytes_to_digest).hexdigest()

	save_fname=domain_dir+'/meta_cards/'+unique_hash_fname+file_extension
	cropped_im.save(save_fname)

	processed_cards.append(x)
	with open(domain_dir+'/card_images/processed_cards.pkl','wb') as f:
		pickle.dump(processed_cards,f)

	os.system('/usr/local/bin/aws s3 cp ' + save_fname + ' s3://www.world-wide.org/' + this_domain + 'meta_cards/'+unique_hash_fname+file_extension)
	
	i+=1



sys.exit()
 
image = Image.open('background.jpg')
 
# initialise the drawing context with
# the image object as background
 
draw = ImageDraw.Draw(image)

# create font object with the font file and specify
# desired size
 
font = ImageFont.truetype('fonts/Roboto-Bold.ttf', size=45)
 
# starting position of the message
 
(x, y) = (50, 50)
message = "Happy Birthday!"
color = 'rgb(0, 0, 0)' # black color
 
# draw the message on the background
 
draw.text((x, y), message, fill=color, font=font)
(x, y) = (150, 150)
name = 'Vinay'
color = 'rgb(255, 255, 255)' # white color
draw.text((x, y), name, fill=color, font=font)
 
# save the edited image
 
image.save('greeting_card.png')

image.save('optimized.png', optimize=True, quality=20)
