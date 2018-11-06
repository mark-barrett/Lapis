# Developed by Mark Barrett
# http://markbarrettdesign.com
# https://github.com/mark-barrett

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import ModelForm
from django import forms

from core.models import *


class ProjectForm(ModelForm):
    name = forms.CharField(max_length=64)
    description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Project
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Create Project', css_class='btn btn-success btn-block'))


    def clean(self):
        # Get the entered project name
        project_name = self.cleaned_data.get('name', None)

        print(project_name)

        print(self.request.user)

        # Check the database for this already existing for this user
        try:
            project = Project.objects.get(user=self.request.user, name=project_name)

            self._errors['name'] = self.error_class([
                'A project with this name already exists.'])
        except:
            pass

        return self.cleaned_data
