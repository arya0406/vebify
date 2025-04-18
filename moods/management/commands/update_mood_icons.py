from django.core.management.base import BaseCommand
from moods.models import Mood

class Command(BaseCommand):
    help = 'Updates mood icons'

    def handle(self, *args, **options):
        mood_icons = {
            'Happy': '😊',
            'Sad': '😔',
            'Dance': '💃',
            'Joy': '🎉',
            'Nostalgia': '📷',
            'Frustration': '😤',
            'Confidence': '💪',
            'Sad/Lonely': '💔',
            'Love': '❤️',
            'Excitement': '🌟',
            'Anger': '😠',
            'Lowkey': '🎧',
            'Sunday Mood': '☀️'
        }

        for mood_name, icon in mood_icons.items():
            try:
                mood = Mood.objects.get(name=mood_name)
                mood.icon = icon
                mood.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully updated icon for {mood_name}'))
            except Mood.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Mood {mood_name} not found')) 