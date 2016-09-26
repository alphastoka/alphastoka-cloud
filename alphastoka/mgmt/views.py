from django.shortcuts import render
from docker import Client
from django.http import HttpResponseRedirect
from django.contrib import messages
from pymongo import MongoClient

cli = Client(base_url='unix:///var/run/docker.sock')
mongo_client = MongoClient("mongodb://54.169.89.105:27017")

# Create your views here.
def index(request):
	cli = Client(base_url='unix:///var/run/docker.sock')
	containers = cli.containers()
	return render(request, "index.html", {
		"containers": containers
	})

def results(request):
	db = request.GET.get("family")
	if not db:
		return render(request, "results.html", {
			"dbs": mongo_client.database_names()
		})
	mongo_db = mongo_client[db]
	humans = mongo_db.human.find({}).sort([("followed_by", -1)]).skip(0).limit(200)
	
	# self.mongo_db = self.mongo_client['stoka_' + ]
	return render(request, "results.html", {
		"family": db,
		"humans": humans
	})

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
			"RABBIT_USER": "rabbitmq",
			"RABBIT_PASSWORD": "Nc77WrHuAR58yUPl",
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