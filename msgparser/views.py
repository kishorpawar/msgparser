from rest_framework.views import APIView
from rest_framework.response import Response

from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from parsers.parsers import MailParser

class FileUploadView(APIView):
	parser_classes = (MailParser,)

	def put(self, request, format=None):
		# file_ob = request.FILES['file']

		# print type(file_ob)
		# print file_ob
		print request.data.dump
		print dir(request.data)
		return Response(status=204)

	@method_decorator(csrf_exempt)
	def dispatch(self, request, *args, **kwargs):
		return super(FileUploadView, self).dispatch(request, *args, **kwargs)

class Home(TemplateView):
	"""Home page"""
	template_name = 'home.html'