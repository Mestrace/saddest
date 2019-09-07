from django.db import models
import os
from django.dispatch import receiver

from django.conf import settings

class DisplayImage(models.Model):
    name = models.CharField(max_length=256, null=False)
    file = models.ImageField(upload_to=os.path.join(settings.MEDIA_ROOT,
                                                    "images"))
    groupid = models.CharField(max_length=256, null=False)

@receiver(models.signals.post_delete, sender=DisplayImage)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(models.signals.pre_save, sender=DisplayImage)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).file
    except sender.DoesNotExist:
        return False

    new_file = instance.file
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


