from django.shortcuts import render

from .forms import CreationForm


def SignUp(request):
    template = 'users/signup.html'
    form = CreationForm()
    context = {
        'form': form,
    }
    return render(request, template, context)
