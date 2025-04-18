from django.db import models
from django.utils.text import slugify

class Mood(models.Model):
    """Model representing a mood for music categorization."""
    MOOD_CATEGORIES = [
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('energetic', 'Energetic'),
        ('relaxed', 'Relaxed'),
        ('romantic', 'Romantic'),
        ('angry', 'Angry'),
        ('nostalgic', 'Nostalgic'),
        ('lonely', 'Lonely'),
        ('hopeful', 'Hopeful'),
        ('peaceful', 'Peaceful'),
        ('melancholic', 'Melancholic'),
        ('confident', 'Confident'),
        ('party', 'Party'),
        ('devotional', 'Devotional'),  # For Indian devotional music
        ('patriotic', 'Patriotic'),    # For patriotic songs
        ('festive', 'Festive'),        # For festival songs
    ]
    
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=MOOD_CATEGORIES, default='happy')
    color = models.CharField(max_length=20, default='blue')
    icon = models.ImageField(upload_to='mood_icons/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Language targeting
    language_specific = models.BooleanField(default=False)
    language = models.CharField(max_length=20, blank=True, null=True, 
                                 choices=[
                                     ('hindi', 'Hindi'),
                                     ('tamil', 'Tamil'),
                                     ('telugu', 'Telugu'),
                                     ('kannada', 'Kannada'),
                                     ('malayalam', 'Malayalam'),
                                     ('punjabi', 'Punjabi'),
                                     ('marathi', 'Marathi'),
                                     ('bengali', 'Bengali'),
                                     ('gujarati', 'Gujarati'),
                                     ('english', 'English'),
                                 ])
    
    def __str__(self):
        if self.language_specific and self.language:
            return f"{self.name} ({self.language})"
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            if self.language_specific and self.language:
                base_slug = f"{base_slug}-{self.language}"
            self.slug = base_slug
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']