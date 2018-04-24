from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import auth
from django.http import HttpResponseRedirect
from .forms import CustomUserCreationForm
from .forms import CustomUserEditForm
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, \
    PasswordResetCompleteView, PasswordResetConfirmView
import os
import math
from contour.settings import PATH_MEDIA, PATH_USER_GENERATED
from virocon.settings import USE_S3
from contour.models import MeasureFileModel, ProbabilisticModel, \
    EnvironmentalContour, PlottedFigure



def authentication(request):
    """
    Thr method to login users.
    Parameters
    ----------
    request : to authenticate the user.

    Returns
    -------
    HttpResponse
    """
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(None, request.POST or None)
        if form.is_valid():
            auth.login(request, form.get_user())
            return HttpResponseRedirect(reverse('contour:index'))
        else:
            return render(request, 'user/login.html', {'form': form})

    return render(request, 'user/login.html', {'form': form})


# Method is called after userdata is entered and checks database for verification
def authentic(request, username, password):
    user = auth.authenticate(username=username, password=password)
    auth.login(request, user)


def create(request):
    """
    The method creates a new user account .

    Parameters
    ----------
    request : to create a new user account.

    Returns
    -------
    HttpResponse
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            authentic(request, username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            return HttpResponseRedirect(reverse('contour:index'))
        else:
            return render(request, 'user/edit.html', {'form': form})
    else:
        return render(request, 'user/edit.html', {'form': CustomUserCreationForm()})


def logout(request):
    """
    The method logs out a user.

    Parameters
    ---------
    request : to log out.


    Return
    ------
    HttpResponseRedirect to home.
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect(reverse('contour:index'))
    else:
        auth.logout(request)
        return HttpResponseRedirect(reverse('contour:index'))


def profile(request):
    """
    The method views the user profile.

    Parameters
    ----------
    request : to view the user profile.

    Returns
    -------
    HttpResponse
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect(reverse('contour:index'))
    else:
        storage_space = user_storage_space(request.user)
        return render(request,
                      'user/profile.html',
                      {'storage_space': storage_space})


def edit(request):
    """
    The method allows users to edit their profiles.

    Parameters
    ---------
    request : request to edit a user profile.

    Returns
    -------
    HttpResponse
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect(reverse('contour:index'))
    else:
        if request.method == 'POST':
            form = CustomUserEditForm(request.POST, instance=request.user)

            if form.is_valid():
                form.save()
                return redirect(reverse('user:profile'))
            else:
                return render(request, 'user/edit.html', {'form': form})
        else:
            form = CustomUserEditForm(instance=request.user)
            return render(request, 'user/edit.html', {'form': form})


def change_password(request):
    """
    The method allows a user to change his password.

    Parameters
    ----------
    request : to change the user password

    Returns
    -------
    HttpResponse
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect(reverse('contour:index'))
    else:
        if request.method == 'POST':
            form = PasswordChangeForm(data=request.POST, user=request.user)

            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)
                return redirect(reverse('user:profile'))
            else:
                return render(request, 'user/edit.html', {'form': form})
        else:
            form = PasswordChangeForm(user=request.user)
            return render(request, 'user/edit.html', {'form': form})


class ResetView(PasswordResetView):
    template_name = 'user/password_reset/form.html'
    email_template_name = 'user/password_reset/email.html'
    subject_template_name = 'user/password_reset/subject.txt'
    success_url = 'done/'


class ResetDoneView(PasswordResetDoneView):
    template_name = 'user/password_reset/done.html'


class ResetConfirmView(PasswordResetConfirmView):
    template_name = 'user/password_reset/confirm.html'
    success_url = '/user/reset/done'


class ResetCompleteView(PasswordResetCompleteView):
    template_name = 'user/password_reset/complete.html'


# Thanks to: https://stackoverflow.com/questions/1392413/calculating-a-
# directorys-size-using-python
def user_storage_space(user):
    """
    Calculates the storage space that the user's file occupy in byte.

    Parameters
    ----------
    user : User
        The user whose storage space if of interest. Comes from request.user.

    Returns
    -------
    total_size : str
        The total size of the user's used storage space.
    """
    total_size = 0
    if USE_S3:
        measure_models = MeasureFileModel.objects.filter(
            primary_user=user)
        for measure_model in measure_models:
            total_size = total_size + \
                            measure_model.measure_file.file.size
        environmental_contours = EnvironmentalContour.objects.filter(
            primary_user=user)
        for environmental_contour in environmental_contours:
            total_size = total_size + \
                            environmental_contour.latex_report.file.size
    else:
        start_path = PATH_MEDIA + PATH_USER_GENERATED + str(user)
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
    total_size = convert_size(total_size)
    return total_size


# Thanks to: https://stackoverflow.com/questions/5194057/better-way-to-convert-
# file-sizes-in-python
def convert_size(size_bytes):
    """
    Converts the size in bytes into a nicely readable number with unit, for
    example into megabytes if it is more than 1000 KB and less than 1000 MB.

    Parameters
    ----------
    size_bytes : int
        The size of one or multiple files in bytes.

    Returns
    -------
    total_size : str
        The input size formated appropriately using "B", "KB", "MB" and so forth
        as unit.
    """
    if size_bytes == 0:
       return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    size_formated = "%s %s" % (s, size_name[i])
    return size_formated
