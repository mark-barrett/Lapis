# Developed by Mark Barrett
# http://markbarrettdesign.com
# https://github.com/mark-barrett

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import ModelForm
from django import forms

from core.models import *


class ProjectForm(ModelForm):
    TYPE_CHOICES = (
        ('private', 'Private'),
        ('public', 'Public')
    )

    name = forms.CharField(max_length=64)
    description = forms.CharField(required=False)

    class Meta:
        model = Project
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.edit = kwargs.pop('edit', None)
        # Get the project_id to check if the project we are editing is the same
        self.project_id = kwargs.pop('project_id', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        if self.edit:
            self.helper.add_input(Submit('submit', 'Edit Project', css_class='btn btn-success btn-block'))
        else:
            self.helper.add_input(Submit('submit', 'Create Project', css_class='btn btn-success btn-block'))


    def clean(self):
        # Get the entered project name
        project_name = self.cleaned_data.get('name', None)

        # Check the database for this already existing for this user
        try:
            project = Project.objects.get(user=self.request.user, name=project_name)

            # Check if the project id of what we are editing and the one that the form is associated with
            # are the same. If they are the same then the name can be the same as the already set name of this
            # project.
            if str(project.id) != self.project_id:
                self._errors['name'] = self.error_class([
                    'A project with this name already exists.'])
        except:
            pass

        return self.cleaned_data


class DatabaseBuilderForm(forms.Form):

    server_address = forms.CharField(max_length=32)
    database_user = forms.CharField(max_length=32)
    database_password = forms.CharField(max_length=256)
    database_name = forms.CharField(max_length=64)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
class ResourceForm(forms.Form):
    REQUEST_CHOICES = (
        ('GET', 'GET'),
        ('POST', 'POST')
    )

    RESPONSE_CHOICES = (
        ('JSON', 'JSON'),
        ('XML', 'XML')
    )

    name = forms.CharField(max_length=64)
    description = forms.CharField(max_length=64)
    request_type = forms.ChoiceField(choices=REQUEST_CHOICES)

    response_type = forms.ChoiceField(choices=RESPONSE_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        # Get the project_id to check if the project we are editing is the same
        self.project_id = kwargs.pop('project_id', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Create Resource', css_class='btn btn-success btn-block'))

        self.fields['request_type'].label = 'Request Type'

        self.fields['response_type'].widget.attrs['class'] = 'selectpicker'
