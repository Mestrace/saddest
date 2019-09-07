from django import forms
from django.core.exceptions import ValidationError


class UserUploadedImage(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': "Image Name",
            'required': 'required'
        }),
    )
    file = forms.FileField(
        widget=forms.FileInput(attrs={}),
    )


from django.forms import formset_factory
from django.forms import BaseFormSet
from tempfile import NamedTemporaryFile
from PIL import Image


class BaseImageUploadFormset(BaseFormSet):

    def clean(self):
        if any(self.errors):
            return

        names = {}

        for form in self.forms:
            if form.cleaned_data:
                name = form.cleaned_data['name']
                file = form.cleaned_data['file']

                if name and file:
                    if name in names:
                        raise ValidationError("Each image must have unique "
                                              "name.", code='duplicate name')

                    with NamedTemporaryFile() as tmp:
                        for chunk in file.chunks():
                            tmp.write(chunk)
                        try:
                            img = Image.open(tmp)
                            img.verify()
                        except Exception as e:
                            print(e)
                            raise ValidationError("Not a valid image file",
                                                  code="invalid image")

                elif name:
                    raise ValidationError("Each image must have a unique "
                                          "name.", code="empty name")
                elif file:
                    raise ValidationError("No image file submitted.",
                                          code="empty image")
                else:
                    raise ValidationError("Null entry submitted.",
                                          code="Null entry.")


UserUploadedImageFormSet = formset_factory(UserUploadedImage,
                                           formset=BaseImageUploadFormset)
