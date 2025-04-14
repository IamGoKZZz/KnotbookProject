from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Subject, Module

@receiver(post_save, sender=Subject)
def create_default_modules(sender, instance, created, **kwargs):
    if created:  # Only add modules if a new subject is created
        default_module_names = [
            "Module 1",
            "Module 2",
            "Module 3",
            "Module 4",
            "Module 5",
        ]
        for name in default_module_names:
            Module.objects.create(subject=instance, name=name)
