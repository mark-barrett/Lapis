from django.shortcuts import render
from django.views import View

from core.models import Project


class GetDocumentation(View):

    def get(self, request, project_id):

        context = {
            'project': Project.objects.get(id=project_id)
        }

        return render(request, 'docs/home.html', context)
