from django.shortcuts import render
from django.views import View

from core.models import Project, Resource
from docs.models import *


class GetDocumentation(View):

    def get(self, request, project_id):

        project = Project.objects.get(id=project_id)

        documentation_instance = DocumentationInstance.objects.get(project=project)

        context = {
            'project': project,
            'document': documentation_instance,
            'resources': Resource.objects.all().filter(project=project),
            'languages': ProgrammingLanguageChoice.objects.all().filter(documentation_instance=documentation_instance)
        }

        return render(request, 'docs/home.html', context)
