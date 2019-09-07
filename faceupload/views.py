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


import numpy as np
from PIL import Image
# Models from
# https://towardsdatascience.com/face-detection-recognition-and-emotion-detection-in-8-lines-of-code-b2ce32d4d5de
from keras.models import load_model

model = load_model(
    os.path.join(settings.BASE_DIR, "models", 'model_v6_23.hdf5'))
model.predict(np.random.random([1, 48, 48, 1]))


def rank_sadness(name_face):
    # shuffle(name_face)
    # return name_face
    sadness_level = []
    for _, face_arr in name_face:
        face_arr = Image.fromarray(face_arr) \
            .resize((48, 48), Image.ANTIALIAS) \
            .convert('L')
        face_arr = np.array(face_arr)
        face_arr = face_arr.reshape([1, *face_arr.shape, 1])
        print(face_arr.shape)
        result = model.predict(face_arr)
        print(result)

        # Classes:
        # {0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Neutral', 5: 'Sad', 6: 'Surprise'}
        sadness_level.append(result[0][5])  # 5 is sad

    return [nf for _, nf in
            sorted(
                zip(sadness_level, name_face),
                key=lambda pair: pair[0],
                reverse=True
            )
            ]
