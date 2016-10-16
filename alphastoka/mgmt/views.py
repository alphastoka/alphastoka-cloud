from django.shortcuts import render
from docker import Client
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from pymongo import MongoClient
import re, math, json, csv
from openpyxl import Workbook
# import xlsxwriter

cli = Client(base_url='unix:///var/run/docker.sock')
mongo_client = MongoClient("mongodb://cloud.alphastoka.com:27017")

def abbreviated_pages(n, page):

	# Build set of pages to display
	if n <= 10:
		pages = set(range(1, n + 1))
	else:
		pages = (set(range(1, 6))
		         | set(range(max(1, page - 2), min(page + 3, n + 1)))
                 | set(range(n - 2, n + 1)))
	
	def display():
		last_page = 0
		for p in sorted(pages):
			if p != last_page + 1: yield '...'
			yield ('{0}' if p == page else '{0}').format(p)
			last_page = p

	return ' '.join(display()).split(' ')


# Create your views here.
def index(request):
	cli = Client(base_url='unix:///var/run/docker.sock')
	containers = cli.containers(filters={"status": "running"}) + cli.containers(filters={"status": "paused"})
	images = []
	for im in cli.images():
		if 'stoka-' in ','.join(im.get('RepoTags')):
			im["Alias"] = im.get('RepoTags')[0].replace("stoka-", "").replace("ssabpisa/", "").replace("yt", "Youtube").replace("ig", "Instagram")
			images.append(im)

	for container in containers:
		container["Discovered"] = 0 
		container["Error"] = 0
		sstr = cli.logs(container=container.get("Id"), tail=300)
		m = re.findall(r"@astoka.progress\s+([0-9]+)", sstr.decode("utf-8"))
		if(len(m) > 0):
			container["Discovered"] = int(m[-1])
		sstr = cli.logs(container=container.get("Id"), tail=300)
		m = re.findall(r"@astoka.error\s+([0-9]+)", sstr.decode("utf-8"))
		if(len(m) > 0):
			container["Error"] = int(m[-1])

	return render(request, "index.html", {
		"containers": containers,
		"images": images
	})


def results_export(request):
	"""
	Export to excel
	"""

	db = request.GET.get("family")
	collection = request.GET.get("collection", "instagram")
	mongo_db = mongo_client[db]
	humans = mongo_db[collection].find({})
	
	wb = Workbook(write_only=True)
	ws = wb.create_sheet()

	i = 0
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
			try:
				if col == "followed_by":
					r.append(str(x[col]["count"]))
				else:
					cleaned = re.sub(r'[^ก-๙a-zA-Z0-9-._~:/ ]+', '', str(x[col]).replace("\n", ""))
					r.append(cleaned)
			except KeyError:
				r.append("n/a")

		ws.append(r)
		i = i + 1

	response = HttpResponse(content_type='application/octet-stream')

	response['Content-Disposition'] = 'attachment; filename="export_%s_%s.xlsx"' % (db,collection)
	wb.save(response)
	return response

def results(request):
	db = request.GET.get("family")
	search = request.GET.get("search")
	#db.instagram.find({ 'media.nodes.caption': { '$regex': '#rasta r' } }).count()
	collections = ["instagram", "youtube", "facebook"]
	collection = request.GET.get("collection", "instagram")
	current_page = request.GET.get("page", "1")
	
	if not db:
		return render(request, "results.html", {
			"dbs": mongo_client.database_names(),
			"collections": collections
		})
	mongo_db = mongo_client[db]

	filter = {}
	if search is not None:
		filter = { '$or' : [
			{ 'media.nodes.caption': { '$regex': str(search) } },
			{ 'biography': { '$regex': str(search) } },
			{ 'video_descriptions.description': {'$regex'  : str(search)} },
			{ 'video_descriptions.title': {'$regex'  : str(search)} },
			{ 'description': {'$regex'  : str(search)} }
		] }
	else:
		search = ""

	count = mongo_db[collection].count(filter)
	humans = mongo_db[collection].find(filter).sort([("stats.subscriber_count", -1), ("followed_by.count", -1)]).skip(50*(int(current_page)-1)).limit(50)

	pages = abbreviated_pages(math.ceil(count/50), int(current_page))
	
	return render(request, "results.html", {
		"family": db,
		"count": count,
		"search": search,
		"humans": humans,
		"collections": collections,
		"current_collection": collection,
		"pages": pages,
		"current_page" : current_page
	})
	
def processors(request):
	return render(request, "processors.html")

def mgmt_jail(request, container_id):
	# cli = Client(base_url='unix:///var/run/docker.sock')
	cli.pause(container=container_id)
	messages.add_message(request, 50, message='The selected Stoka has been convicted and jailed.', extra_tags="success")
	return HttpResponseRedirect("/") 

def mgmt_release(request, container_id):
	# cli = Client(base_url='unix:///var/run/docker.sock')
	cli.unpause(container=container_id)
	messages.add_message(request, 50, message='The selected Stoka has been released and is back running.', extra_tags="success")
	return HttpResponseRedirect("/") 

def mgmt_murder(request, container_id):
	# cli = Client(base_url='unix:///var/run/docker.sock')
	cli.kill(container=container_id)
	messages.add_message(request, 50, message='The selected Stoka has been taken care of.', extra_tags="success")
	return HttpResponseRedirect("/") 

def categorization(request):
	
	mongo_system = mongo_client['stoka_system']
		
	return render(request, "categorization.html",{
		"category_key": mongo_system.categorizer.find({}).skip(0).limit(1)[0]
	})

def mgmt_create(request):
	if request.method == "POST":
		# cli = Client(base_url='unix:///var/run/docker.sock')
		dna = request.POST.get("dna").replace(" ", "")
		group_name = request.POST.get("group_name").replace(" ", "")
		depth = request.POST.get("depth", "12")
		seeder_username = request.POST.get("seeder_username").replace(" ", "")
		cookie = request.POST.get("cookie", "")

		envs = {
			"RABBIT_HOST": "rabbitmqhost",
			"RABBIT_USR": "rabbitmq",
			"RABBIT_PWD": "Nc77WrHuAR58yUPl",
			"RABBIT_PORT": "5672",
			"SEED_ID": seeder_username,
			"GROUP_NAME" : group_name,
			"DEPTH": int(depth),
			"COOKIE": cookie
		}

		lbl = {"astoka.seeder": seeder_username, "astoka.family": group_name }

		if dna is None:
			messages.error(request, 'You did not specify a DNA for the Stoka instance.')
			return HttpResponseRedirect("/") 
		
		if len(seeder_username) <= 2:
			messages.add_message(request, 50, message='A seeder is required to spawn a Stoka Instance.', extra_tags="danger")
			return HttpResponseRedirect("/") 

		linkconf = cli.create_host_config(
			links=[('rabbitmq','rabbitmqhost')]
		)

		con = cli.create_container(image=dna, labels=lbl, environment=envs, host_config=linkconf)
		response = cli.start(container=con.get("Id"))
		messages.add_message(request, 50, message='Stoka instance spawn successfully.', extra_tags="success")
		
	return HttpResponseRedirect("/") 