import os,re
from openpyxl import Workbook
from pymongo import MongoClient

mongo_client = MongoClient("mongodb://54.169.89.105:27017")

FAMILY = os.getenv('FAMILY')
COLLECTION = os.getenv('COLLECTION', "instagram")
FILENAME = os.getenv('FILENAME', "file")

db = FAMILY
collection = COLLECTION
mongo_db = mongo_client[db]
humans = mongo_db[collection].find({})

wb = Workbook(write_only=True)
ws = wb.create_sheet()

i = 0
j = mongo_db[collection].count({})
print("Starting loop")
for x in humans:
	fields = ['username', 'biography', '_dna', 'followed_by', 'category', 'language', 'predicted_age', '_seed_username', 'is_verified', 'caption', 'profile_pic_url', 'id']

	if collection == 'youtube':
		x['subscriber_count'] = x['stats']['subscriber_count']
		x['view_count'] = x['stats']['view_count']
		x['description'] = x['description'].strip()
		fields = [ 'phone', 'country', 'subscriber_count', 'video_descriptions', 'view_count', 'category', 'predicted_age', 'language', 'url', '_dna', '_seed_username', 'language', 'description', 'title', 'id', 'logo_url', 'email', 'medium']
	else:
		caption = ""
		for m in x['media']['nodes']:
			if "caption" in m:
				caption = str(caption) + " " +  str(m["caption"])

		x['caption'] = caption

	if i == 0:
		ws.append(fields)

	r = []
	for col in fields:
		if col == "followed_by":
			r.append(str(x[col]["count"]))
		else:
			cleaned = re.sub(r'[^ก-๙a-zA-Z0-9-._~ ]+', '', str(x[col]).replace("\n", ""))
			r.append(cleaned)

	ws.append(r)
	i = i + 1
	print("%", i/j)

wb.save("/tmp/"+ FILENAME +".xlsx")
