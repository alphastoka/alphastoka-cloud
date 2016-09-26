from django.shortcuts import render
from docker import Client
from django.http import HttpResponseRedirect
from django.contrib import messages
from pymongo import MongoClient
import re

cli = Client(base_url='unix:///var/run/docker.sock')
mongo_client = MongoClient("mongodb://54.169.89.105:27017")

# Create your views here.
def index(request):
	cli = Client(base_url='unix:///var/run/docker.sock')
	containers = cli.containers()
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

def results(request):
	db = request.GET.get("family")
	if not db:
		return render(request, "results.html", {
			"dbs": mongo_client.database_names()
		})
	mongo_db = mongo_client[db]

	count = mongo_db.human.count({})
	humans = mongo_db.human.find({}).sort([("followed_by", -1)]).skip(0).limit(200)
	
	# self.mongo_db = self.mongo_client['stoka_' + ]
	return render(request, "results.html", {
		"family": db,
		"count": count,
		"humans": humans
	})
def processors(request):
	return render(request, "processors.html")

def mgmt_murder(request, container_id):
	# cli = Client(base_url='unix:///var/run/docker.sock')
	cli.kill(container=container_id)
	messages.add_message(request, 50, message='The selected Stoka has been taken care of.', extra_tags="success")
	return HttpResponseRedirect("/") 

def mgmt_create(request):
	if request.method == "POST":
		# cli = Client(base_url='unix:///var/run/docker.sock')
		dna = request.POST.get("dna")
		group_name = request.POST.get("group_name")
		seeder_username = request.POST.get("seeder_username")
		envs = {
			"RABBIT_HOST": "rabbitmqhost",
			"RABBIT_USR": "rabbitmq",
			"RABBIT_PWD": "Nc77WrHuAR58yUPl",
			"RABBIT_PORT": "5672",
			"SEED_ID": "@" + seeder_username,
			"GROUP_NAME" : group_name
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