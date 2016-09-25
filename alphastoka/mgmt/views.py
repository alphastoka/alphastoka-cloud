from django.shortcuts import render
from docker import Client
from django.http import HttpResponseRedirect
from django.contrib import messages

# Create your views here.
def index(request):
	cli = Client(base_url='unix:///var/run/docker.sock')
	containers = cli.containers()
	return render(request, "index.html", {
		"containers": containers
	})

def mgmt_create(request):
	if request.method == "POST":
		cli = Client(base_url='unix:///var/run/docker.sock')
		dna = request.POST.get("dna")
		group_name = request.POST.get("group_name")
		seeder_username = request.POST.get("seeder_username")
		envs = {
			"RABBIT_HOST": "rabbitmqhost",
			"RABBIT_PORT": "5672",
			"SEED_ID": "@" + seeder_username,
			"GROUP_NAME" : group_name
		}

		lbl = {"astoka.seeder": seeder_username, "astoka.family": group_name }

		if dna is None:
			messages.error(request, 'You did not specify a DNA for the Stoka instance.')
			return HttpResponseRedirect("/") 

		linkconf = cli.create_host_config(
			links=[('rabbitmq','rabbitmqhost')]
		)

		con = cli.create_container(image=dna, labels=lbl, environment=envs, host_config=linkconf)
		response = cli.start(container=con.get("Id"))
		print(response)
		
	return HttpResponseRedirect("/") 