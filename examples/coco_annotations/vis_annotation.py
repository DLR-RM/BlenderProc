

# In[6]:


from PIL import Image, ImageFont, ImageDraw, ImageEnhance
import json
import argparse

# In[35]:

parser = argparse.ArgumentParser()
parser.add_argument('-c','--conf', dest='conf', default = 'coco_annotations.json', help='coco annotation json file')
parser.add_argument('-i','--image_index', dest='image_index', default = 0 ,help='image over which to annotate, uses the rgb rendering', type=int)
parser.add_argument('-b','--base_path',dest = 'base_path', default = 'output', help='base path for all the files', type = str )
args = parser.parse_args()

conf = args.conf
image_idx = args.image_index
base_path = args.base_path

with open(base_path+'/'+conf) as f:
    annotations = json.load(f)
    categories = annotations['categories'] 
    annotations = annotations['annotations']


# In[50]:


def get_category(_id):
    category = [category["name"] for category in categories if category["id"] == _id]
    return category[0]


# In[61]:

imname = base_path+'/'+"rgb_" +  "%04d"%image_idx + ".png"
im = Image.open(imname)
draw = ImageDraw.Draw(im)

for idx, annotation in enumerate(annotations):
    if annotation["image_id"] == image_idx:
        bb = annotation['bbox']
        draw.rectangle(((bb[0], bb[1]), (bb[0] + bb[2], bb[1] + bb[3])), fill=None, outline = "red")
        draw.text((bb[0]+2, bb[1]+2), get_category(annotation["category_id"]), font=ImageFont.truetype("arial"))
        poly = Image.new('RGBA', im.size)
        pdraw = ImageDraw.Draw(poly)
        pdraw.polygon(annotation["segmentation"][0],
              fill=(255,255,255,127),outline=(255,255,255,255))
        im.paste(poly,mask=poly)
        
im.save('annotated.png', "PNG")
an = Image.open('annotated.png')
an.show()

