import os
import uuid

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from .forms import UserUploadedImageFormSet
from .models import DisplayImage


# Create your views here.

def upload_image(request):
    if request.method == 'GET':
        formset = UserUploadedImageFormSet()
    elif request.method == 'POST':
        formset = UserUploadedImageFormSet(request.POST, request.FILES)
        if formset.is_valid():
            faces = []
            for imageForm in formset:
                faces.extend(crop_faces(imageForm.cleaned_data['name'],
                                        imageForm.cleaned_data['file']))

            ranked_faces = rank_sadness(faces)
            gid = uuid.uuid4()
            for name, img_arr in ranked_faces:
                tf = tempfile.NamedTemporaryFile(delete=False,
                                                 dir=os.path.join(
                                                     settings.MEDIA_ROOT,
                                                     "images",
                                                 ), suffix=".jpg")
                tf.close()
                io.imsave(tf.name, img_arr)
                dimg = DisplayImage(name=name, file=tf.name,
                                    groupid=gid)
                dimg.save()
            return render(request, 'sadness.html',
                          {"imgs": DisplayImage.objects.filter(groupid=gid)})
    else:
        return HttpResponse(status=405)
    return render(request, 'upload.html', {"formset": formset})


import tempfile
import dlib
from skimage import io


def crop_faces(image_name, file):
    with tempfile.NamedTemporaryFile() as destination:
        for chunk in file.chunks():
            destination.write(chunk)
        face_detector = dlib.get_frontal_face_detector()

        name_face_tuples = []
        img = io.imread(destination)

        for i, fx in enumerate(face_detector(img, 1)):
            name_face_tuples.append((image_name + "_" + str(i),
                                     img[fx.top(): fx.bottom(),
                                     fx.left(): fx.right()]))
        return name_face_tuples


from random import shuffle


def rank_sadness(name_face):
    shuffle(name_face)
    return name_face
