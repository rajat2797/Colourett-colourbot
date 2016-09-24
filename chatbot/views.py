from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import re
import random
import pprint
import requests

# Create your views here.

VERIFY_TOKEN = '24thseptember2016'
PAGE_ACCESS_TOKEN = 'EAAO89xUqo7gBABxZBZC4G6PRp3pOVckcvxbMmR89ZBJmMjj2kAuvtPL0x2FhjEyBh4BIi7X6pGUVmtWdxpSWeb6MCFILrm643RuAS1XqIhOgJ3Ud3Q5EZARJM3lplvwNUvIXeRvepmMD0VYfsrAFNgfrZCN3EfGnTPgPKc14vcgZDZD'

def index(request):
	# colour=request.GET['text']
	return HttpResponse(search_colour('red'))

def scrape_spreadsheet():
	url = 'https://spreadsheets.google.com/feeds/list/1FChO1iS-SnEw9a3JUnUT1ZInLfCaETpvYb7Y_2egOq0/od6/public/values?alt=json'
	resp=requests.get(url=url).text
	data=json.loads(resp)
	arr=[]
	for entry in data['feed']['entry']:	
		# print entry['gsx$name']['$t']
		d=dict(colour_name=entry['gsx$name']['$t'],colour_hex=entry['gsx$colour1']['$t'])
		arr.append(d)
	# although it would be better to create a json object and then return it as it will be fast
	return arr

def search_colour(text):
	colour_arr=scrape_spreadsheet()
	for colour in colour_arr:
		if text.lower() in colour['colour_name'].lower():
			return colour
	num=random.randint(0,len(colour_arr)-1)
	print "***************%d****************"%(num)
	return colour_arr[num]

def post_facebook_message(fbid,message_text):
	post_message_url = 'https://graph.facebook.com/v2.6/me/messages?access_token=%s'%PAGE_ACCESS_TOKEN
	matching_colour = search_colour(message_text)
	image_url = 'https://dummyimage.com/100x100/%s/%s.png'%(matching_colour['colour_hex'][1:],matching_colour['colour_hex'][1:])
	# print image_url
	output_text = '%s : %s'%(matching_colour['colour_name'],matching_colour['colour_hex'])
	response_msg_generic = {
				  "recipient":{
				    "id":fbid
				  },
				  "message":{
				    "attachment":{
				      "type":"template",
				      "payload":{
				        "template_type":"generic",
				        "elements":[
				          {
				            "title":matching_colour['colour_name'],
				            "item_url":'https://api.chucknorris.io',
				            "image_url":image_url,
				            "subtitle":'HE HE',
				            "buttons":[
				              {
				                "type":"element_share",
				              }
				             ]
				          }              
				         ]
				       }
				  }
				}
			}
	# response_msg_image = {
	# 			"recipient":{
	# 			    "id":fbid
	# 			  },
	# 			  "message":{
	# 			    "attachment":{
	# 			      "type":"image",
	# 			      "payload":{
	# 			        "url":image_url
	# 			      }
	# 			    }
	# 			  }

	# }

	response_msg = json.dumps({"recipient":{"id":fbid}, "message":{"text":output_text}})
	# response_msg_image = json.dumps(response_msg_image)
	response_msg_generic = json.dumps(response_msg_generic)
	requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg)
	# requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg_image)
	requests.post(post_message_url, headers={"Content-Type": "application/json"},data=response_msg_generic)

def logg(message,symbol='-'):
	print '%s\n %s\n %s\n'%(symbol*10,message,symbol*10)

class MyChatBotView(generic.View):
	def get (self, request, *args, **kwargs):
		if self.request.GET['hub.verify_token'] == VERIFY_TOKEN:
			return HttpResponse(self.request.GET['hub.challenge'])
		else:
			return HttpResponse('Oops invalid token')

	@method_decorator(csrf_exempt)
	def dispatch(self, request, *args, **kwargs):
		return generic.View.dispatch(self, request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		incoming_message= json.loads(self.request.body.decode('utf-8'))
		logg(incoming_message)

		for entry in incoming_message['entry']:
			for message in entry['messaging']:
				print message
				try:
					if 'postback' in message:
						handle_postback(message['sender']['id'],message['postback']['payload'])
						return HttpResponse()
					else:
						pass
				except Exception, e:
					logg(e,symbol='-140-')

				try:
					if 'quick_reply' in message['message']:
						# logg(message['message']['quick_reply']['payload'],symbol='--------------avnaua------------')
						handle_quickreply(message['sender']['id'],message['message']['quick_reply']['payload'])
						# to end it with one question
						return HttpResponse()
					else:
						pass
				except Exception, e:
					logg(e,symbol='-140-')


				try:
					sender_id = message['sender']['id']
					message_text = message['message']['text']
					post_facebook_message(sender_id,message_text) 
					# jokes(sender_id)
				except Exception as e:
					print e
					pass

		return HttpResponse()  