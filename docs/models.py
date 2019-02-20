from django.db import models

from core.models import Project


class DocumentationInstance(models.Model):

    project = models.ForeignKey(Project, unique=True)
    introduction_text = models.TextField(blank=True, null=True)
    support_email = models.CharField(max_length=256, blank=True, null=True)
    navbar_colour = models.CharField(max_length=6, blank=True, null=True, default='FFFFFF')
    logo = models.ImageField(upload_to='static/docs/images/docs-logos', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Documentation Instances'

    def __str__(self):
        return self.project.name


class ProgrammingLanguageChoice(models.Model):
    LANGUAGE_CHOICES = (
        ('curl', 'curl'),
        ('Python', 'Python')
    )

    name = models.CharField(max_length=32, choices=LANGUAGE_CHOICES)
    documentation_instance = models.ForeignKey(DocumentationInstance)

    class Meta:
        unique_together = ('name', 'documentation_instance')
        verbose_name_plural = 'Programming Language Choices'

    def __str__(self):
        return self.documentation_instance.project.name + ' ' + self.name

