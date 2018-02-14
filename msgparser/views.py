from rest_framework.views import APIView
from rest_framework.response import Response

from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from parsers.parsers import MailParser, Message

class FileUploadView(APIView):
	# parser_classes = (MailParser,)

	def post(self, request, format=None):
		file_ob = request.FILES['file'].read()

		m = Message(file_ob)
		# print dir(m)
		resp = {
			'subject' : m.subject,
			'header' : m.header,
			'date' : m.date,
			'to' : m.to,
			'sender' : m.sender, 
			'cc' : m.cc, 
			'body' : m.body,
			# 'attachements' : m.attachments
		}
		print resp
		return Response(resp)

class Home(TemplateView):
	"""Home page"""
	template_name = 'home.html'
