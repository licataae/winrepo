from datetime import datetime, timedelta
import random
import re
import time
from functools import reduce
from operator import and_, or_

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash, views as auth_views
from django.contrib.auth.forms import (PasswordResetForm, SetPasswordForm)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import  url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView, DetailView,  CreateView, FormView, ListView
from django.views.generic.edit import ModelFormMixin
from rest_framework import viewsets
from dal.autocomplete import Select2QuerySetView

from .emails import (
    profile_update_email,
    user_create_confirm_email,
    user_reset_password_email,
    user_update_email,
    user_update_email_email
)
from .forms import (ProfileClaimForm, RecommendModelForm, UserCreateForm,
                    UserDeleteForm, UserForm, UserProfileDeleteForm,
                    UserProfileForm, UserPasswordChangeForm, AuthenticationForm)
from .models import Country, Profile, Recommendation, User, Publication
from .serializers import CountrySerializer, PositionsCountSerializer
from .tokens import UserCreateToken, UserEmailChangeToken, UserPasswordResetToken


class Home(ListView):
    template_name = 'profiles/home.html'
    context_object_name = 'recommendations_sample'
    model = Recommendation

    def get_queryset(self):
        top_reco = Recommendation.objects.filter(profile__deleted_at__isnull=True).order_by('-id')[:100]
        nb_samples = 6

        if len(top_reco) == 0:
            sample = []
        else:
            sample = [
                top_reco[i]
                for i in random.sample(range(len(top_reco)), nb_samples)
            ]

        return sample


class ListProfiles(ListView):
    template_name = 'profiles/list.html'
    context_object_name = 'profiles'
    model = Profile
    paginate_by = 20

    def get_queryset(self):
        s = self.request.GET.get('s')
        is_underrepresented = self.request.GET.get('ur') == 'on'
        is_senior = self.request.GET.get('senior') == 'on'

        # create filter on search terms
        # q_st = ~Q(pk=None)  # always true
        q_st = Q(is_public=True, deleted_at__isnull=True)

        if s is not None:
            # split search terms and filter empty words (if successive spaces)
            search_terms = list(filter(None, s.split(' ')))

            for st in search_terms:
                st_regex = re.compile(f'.*{st}.*', re.IGNORECASE)

                # matching_positions = list(
                #   code
                #   for code, name in Profile.get_position_choices()
                #   if st_regex.match(name)
                # )
                matching_structures = list(
                    Q(brain_structure__contains=code)
                    for code, name in Profile.get_structure_choices()
                    if st_regex.match(name)
                )
                matching_modalities = list(
                    Q(modalities__contains=code)
                    for code, name in Profile.get_modalities_choices()
                    if st_regex.match(name)
                )
                matching_methods = list(
                    Q(methods__contains=code)
                    for code, name in Profile.get_methods_choices()
                    if st_regex.match(name)
                )
                matching_domains = list(
                    Q(domains__contains=code)
                    for code, name in Profile.get_domains_choices()
                    if st_regex.match(name)
                )

                st_conditions = [
                    Q(name__icontains=st),
                    Q(institution__icontains=st),
                    Q(position__icontains=st),
                    Q(brain_structure__icontains=st),
                    Q(country__name__icontains=st),
                    Q(keywords__icontains=st),
                 ] + matching_structures \
                   + matching_modalities \
                   + matching_methods \
                   + matching_domains

                q_st = and_(reduce(or_, st_conditions), q_st)

        #  create filter on under-represented countries
        if is_underrepresented:
            q_ur = Q(country__is_under_represented=True)
        else:
            q_ur = ~Q(pk=None)  # always true

        # create filter on senior profiles
        if is_senior:
            senior_profiles_keywords = ('Senior', 'Lecturer', 'Professor',
                                        'Director', 'Principal')
            # position must contain one of the words(case insensitive)
            q_senior = reduce(or_, (Q(position__icontains=x)
                                    for x
                                    in senior_profiles_keywords))
        else:
            q_senior = ~Q(pk=None)  # always true

        # apply filters
        profiles_list = Profile.objects \
            .filter(q_st, q_ur, q_senior) \
            .order_by('-published_at')

        return profiles_list


class ProfileDetail(DetailView):
    model = Profile
    queryset = Profile.objects.filter(is_public=True)
    slug_url_kwarg = 'user__username'
    slug_field = 'user__username'
    query_pk_and_slug = True


class LoginView(auth_views.LoginView):
    form_class = AuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        next = request.GET.get('next')
        if next:
            url_is_safe = url_has_allowed_host_and_scheme(
                url=next,
                allowed_hosts=self.get_success_url_allowed_hosts(),
                require_https=self.request.is_secure(),
            )
            if url_is_safe:
                request.session['next'] = next
                request.session['next_expiration'] = datetime.timestamp(datetime.now() + timedelta(minutes=15))
        return super().dispatch(request, *args, **kwargs)

    def get_redirect_url(self):
        if self.request.session.get('next') and \
            self.request.session.get('next_expiration'):

            if datetime.timestamp(datetime.now()) < self.request.session['next_expiration']:
                return self.request.session.get('next')
        
        if self.request.session.get('first_login', False):
            return reverse('profiles:user_profile')

        return super().get_redirect_url()


class UserProfileView(TemplateView):
    template_name = "account/user_profile.html"


class UserProfileClaimView(LoginRequiredMixin, TemplateView):
    template_name = "account/user_profile_claim_form.html"
    def get(self, request, *args, **kwargs):
        try:
            self.request.user.profile
            return redirect('profiles:user_profile_edit')
        except Profile.DoesNotExist:
            pass
        return super().get(request, *args, **kwargs)

    def get_queryset(self, search=None):
        profiles = Profile.objects.all()
        qs = Q(user__isnull=True)
        if search:
            terms = filter(None, search.strip().split(' '))
            for term in terms:
                qs &= Q(name__icontains=term)
        profiles = profiles.filter(qs)
        return profiles[:5]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search = self.request.GET.get('s', self.request.user.name)
        context.update({
            "profiles": self.get_queryset(search),
            "search": search,
        })
        return context


class UserProfileEditView(LoginRequiredMixin, SuccessMessageMixin, ModelFormMixin, FormView):
    template_name = "account/user_profile_form.html"
    form_class = UserProfileForm
    success_message = 'Your profile has been saved successfully!'

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.request.user.profile
        except Profile.DoesNotExist:
            self.object = Profile()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.request.user.profile
        except Profile.DoesNotExist:
            self.object = Profile()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        if self.object._state.adding is False and \
            any(f in form.changed_data for f in form.base_fields):
            profile_update_email(self.request, self.request.user, self.object).send()
        form.save(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profiles:user_profile')


class UserProfileDeleteView(LoginRequiredMixin, FormView):

    form_class = UserProfileDeleteForm
    template_name = 'account/user_profile_delete.html'
    success_message = 'Your profile has been deleted successfully!'

    def form_valid(self, form):
        user = self.request.user
        try:
            profile = user.profile
            profile.user = None
            profile.delete()

            user.profile = None
            user.save()
        except Profile.DoesNotExist:
            pass

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profiles:user')

class UserView(LoginRequiredMixin, TemplateView):
    template_name = "account/user.html"


class UserEditView(LoginRequiredMixin, SuccessMessageMixin, ModelFormMixin, FormView):
    template_name = "account/user_form.html"
    form_class = UserForm
    success_message = 'Your account has been updated successfully!'
    email_success_message = 'Your account has been updated successfully! Please check your email for the verification link.'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.request.user
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # if any info was updated, send email
        if any(f in form.changed_data for f in form.base_fields):

            # if email was changed, logout and goes through the
            # email verification process
            if 'email' in form.changed_data:
                # get the original user, so we have the original email
                original_user = User.objects.get(pk=self.object.pk)
                token = UserEmailChangeToken.generate(
                    user=original_user,
                    # send the new email via token, so we update
                    # the email upon verification
                    email=form.cleaned_data['email']
                )

                # send confirmation email to the new address
                user_update_email_email(self.request, form.instance, token).send()

                # logout the user
                logout(self.request)

                self.request.session['user_confirmation_token'] = token

                # deactivate account until email is verified
                self.object = original_user
                form.instance.is_active = False
                form.instance.email = original_user.email

                self.success_message = self.email_success_message
                form.changed_data.remove('email')  # do not save email change

            # send email to old address
            user_update_email(self.request, self.object).send()
        
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profiles:user')


class UserChangePasswordView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    form_class = UserPasswordChangeForm
    template_name = "account/user_change_password.html"
    success_message = 'Your password has been updated successfully!'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profiles:user')


class UserDeleteView(LoginRequiredMixin, FormView):
    form_class = UserDeleteForm
    template_name = 'account/user_delete.html'
    success_message = 'Your account has been deleted successfully!'

    def form_valid(self, form):
        user = self.request.user

        # Logout the current user, so to delete it
        logout(self.request)

        try:
            # User profile will be changed and saved (soft-delete)
            profile = user.profile
            profile.user = None
            profile.delete()
        except Profile.DoesNotExist:
            pass

        try:
            # Soft-deleted profiles need to be manually updated (sqlite)
            Profile.all_objects.filter(user=user).update(claimed_by=None)
        except Profile.DoesNotExist:
            pass

        user.delete()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profiles:login')


class UserCreateView(CreateView):
    form_class = UserCreateForm
    template_name = 'registration/signup.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('profiles:user')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        valid = super().form_valid(form)
        token = UserCreateToken.generate(self.object)
        self.request.session['user_confirmation_token'] = token
        user_create_confirm_email(self.request, self.object, token).send()
        return valid

    def get_success_url(self):
        return reverse('profiles:signup_confirm')


class UserCreateConfirmView(TemplateView):
    template_name = 'registration/signup_confirm.html'
    success_message = 'Your e-mail is confirmed! Please, sign-in!'
    same_session_success_message = 'Your e-mail is confirmed!'
    same_session_success_profile_message = 'Your e-mail is confirmed! Please, if you identify yourself as a woman, set-up your public profile!'
    error_message = 'There was an error with your activation. Please, try again.'

    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        if token:  # if there's a token

            payload = UserCreateToken.check(token)
            if payload:  # if the token is valid

                user = User.objects.get(pk=payload['sub'])
                user.is_active = True  # activate user
                if 'email' in payload:  # e-mail update flow
                    user.email = payload['email']
                user.save()

                if Profile.objects.filter(contact_email=user.email, user__isnull=True).exists():
                    profile = Profile.objects.get(contact_email=user.email, user__isnull=True)
                    profile.user = user  # assign user to profile if email matches
                    profile.save()

                same_session_confirmation = False
                if 'user_confirmation_token' in request.session:
                    same_session_confirmation = request.session['user_confirmation_token'] == token
                    del request.session['user_confirmation_token']
                
                if same_session_confirmation:
                    # Same session confirmations are cool to direct login
                    login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
                    if Profile.objects.filter(user=user).exists():
                        messages.success(self.request, self.same_session_success_profile_message)
                    else:
                        messages.success(self.request, self.same_session_success_message)
                    return redirect(self.get_redirect_url())
                else:
                    # Not same session, so request for login
                    messages.success(self.request, self.success_message)
                    return redirect('profiles:login')

            messages.error(self.request, self.error_message)
            return redirect('profiles:login')

        return super().get(request, *args, **kwargs)

    def get_redirect_url(self):
        if self.request.session.get('next') and \
            self.request.session.get('next_expiration'):

            if datetime.timestamp(datetime.now()) < self.request.session['next_expiration']:
                return self.request.session.get('next')
        
        if self.request.session.get('first_login', False):
            return reverse('profiles:user_profile')

        return reverse('profiles:user')


class UserPasswordResetView(FormView):
    form_class = PasswordResetForm
    template_name = 'registration/reset_password.html'
    success_message = 'If your e-mail address is in our registry, you will receive an e-mail soon on how to reset your password.'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('profiles:user')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            token = UserPasswordResetToken.generate(user)
            user_reset_password_email(self.request, user, token).send()
        except User.DoesNotExist:
            time.sleep(4)

        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profiles:forgot')


class UserPasswordResetConfirmView(FormView):
    form_class = SetPasswordForm
    template_name = 'registration/reset_password_confirm.html'
    success_message = 'Your password has been resetted! Please, sign-in!'
    error_message = 'There was an error with your password reset. Please, try again.'

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        self.user = None
        token = request.GET.get('token')
        if token:  # if there's a token
            payload = UserPasswordResetToken.check(token)
            if payload:  # if the token is valid
                self.user = User.objects.get(pk=payload['sub'])

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.user:
            return super().get(request, *args, **kwargs)

        messages.error(self.request, self.error_message)
        return redirect('profiles:forgot')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        form.user.is_active = True
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, self.success_message)
        return reverse('profiles:login')


class CreateRecommendation(SuccessMessageMixin, FormView):
    template_name = 'profiles/recommendation_form.html'
    form_class = RecommendModelForm
    success_message = 'Your recommendation has been submitted successfully!'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                profile_id = self.kwargs.get('pk')
                if profile.id == profile_id:
                    return redirect('profiles:detail', pk=profile_id)
            except Profile.DoesNotExist:
                pass
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        recommendation = form.save()
        self.profile_id = recommendation.profile.id
        if self.request.user.is_authenticated:
            recommendation.reviewer = self.request.user
            recommendation.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profiles:detail', kwargs={'pk': self.profile_id})

    def get_initial(self):
        initial = super().get_initial()
        profile_id = self.kwargs.get('pk')
        if profile_id is not None:
            profile = get_object_or_404(Profile, pk=profile_id)
            initial.update({'profile': profile})
        if self.request.user.is_authenticated:
            initial.update({'reviewer_name': self.request.user.name})
        return initial


class ProfileClaim(SuccessMessageMixin, FormView, LoginRequiredMixin):
    template_name = 'profiles/claim_form.html'
    form_class = ProfileClaimForm
    success_message = 'Your claim has been submitted successfully!'

    profile = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        profile_id = self.kwargs.get('pk')
        if profile_id is None:
            raise Http404('No Profile matches the given query.')

        user = self.request.user
        try:
            user.profile
            return redirect('profiles:user_profile')
        except Profile.DoesNotExist:
            pass

        if user.any_claimed_profile:
            return redirect('profiles:detail', pk=profile_id)

        self.profile = get_object_or_404(Profile, pk=profile_id)

        if self.profile.user:
            return redirect('profiles:detail', pk=profile_id)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.request.user
        self.profile.user = user
        self.profile.claimed_at = timezone.now()
        self.profile.claimed_by = user
        self.profile.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profiles:user_profile')

    def get_context_data(self, **kwargs):
        context = {"profile": self.profile}
        context.update(kwargs)
        return super().get_context_data(**context)


class PublicationsList(ListView):
    template_name = 'publications/list.html'
    context_object_name = 'publications'
    model = Publication
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        s = self.request.GET.get('s', '')
        t = self.request.GET.get('t', '')
        context.update({
            "s": s,
            "t": t,
            "types": Publication.Type.choices,
        })
        return context

    def get_queryset(self):
        q_st = ~Q(pk=None)  # always true

        t = self.request.GET.get('t')
        if t:
            q_st = q_st & Q(type=t)

        s = self.request.GET.get('s')
        if s:
            # split search terms and filter empty words (if successive spaces)
            search_terms = list(filter(None, s.split(' ')))

            for st in search_terms:
                st_regex = re.compile(f'.*{st}.*', re.IGNORECASE)

                st_conditions = [
                    Q(title__icontains=st),
                    Q(authors__icontains=st),
                    Q(description__icontains=st),
                 ]

                q_st = q_st & reduce(or_, st_conditions)

        return Publication.objects \
            .filter(q_st) \
            .order_by('-published_at')


class ProfilesAutocomplete(Select2QuerySetView):

    def get_queryset(self):
        profiles = Profile.objects.all()
        if self.q:
            qs = ~Q(pk=None)
            search_terms = filter(None, self.q.strip().split(' '))
            for st in search_terms:
                qs &= (
                    Q(name__icontains=st) | Q(institution__icontains=st)
                )
            profiles = profiles.filter(qs)
        return profiles


class CountriesAutocomplete(Select2QuerySetView):

    def get_queryset(self):
        countries = Country.objects.all()
        if self.q:
            qs = ~Q(pk=None)
            search_terms = filter(None, self.q.split(' '))
            for st in search_terms:
                qs &= Q(name__icontains=st)
            countries = countries.filter(qs)
        return countries


class RepresentedCountriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.annotate(profiles_count=Count('profiles')) \
                              .filter(profiles_count__gt=0)
    serializer_class = CountrySerializer
    authentication_classes = []


class TopPositionsViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []

    queryset = Profile.objects.all() \
        .values('position') \
        .annotate(profiles_count=Count('id')) \
        .order_by('-profiles_count')
    serializer_class = PositionsCountSerializer
