from django.apps import AppConfig

class NotesConfig(AppConfig):  # Replace 'Notes' with your app name
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'knotebook'  # Replace 'notes' with your app name

    def ready(self):
        import knotebook.signals  # Replace 'notes' with your app name
