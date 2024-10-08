import os
from datetime import datetime
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView

from rest_framework import routers

from .sitemaps import HomeSitemap, FaqSitemap, AboutSitemap, \
     ListSitemap, ProfilesSitemap
from . import views

router = routers.DefaultRouter()
router.register(r'api/countries', views.RepresentedCountriesViewSet)
router.register(r'api/positions', views.TopPositionsViewSet)


sitemaps = {
    'home': HomeSitemap,
    'list': ListSitemap,
    'faq': FaqSitemap,
    'about': AboutSitemap,
    'profiles': ProfilesSitemap,
}

app_name = 'profiles'
academic_advice_updated_at = datetime.fromtimestamp(
    os.path.getmtime('profiles/templates/profiles/academic_advice.html')
)
tips_updated_at = datetime.fromtimestamp(
    os.path.getmtime('profiles/templates/profiles/tips.html')
)
faq_updated_at = datetime.fromtimestamp(
    os.path.getmtime('profiles/templates/profiles/faq.html')
)
about_updated_at = datetime.fromtimestamp(
    os.path.getmtime('profiles/templates/profiles/about.html')
)

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('repo/', views.ListProfiles.as_view(), name='index'),
    path('repo/recommend/', views.CreateRecommendation.as_view(), name='recommend'),
    path('repo/<int:pk>/', views.ProfileDetail.as_view(), name='detail'),
    path('repo/<int:pk>/recommend/', views.CreateRecommendation.as_view(), name='recommend_profile'),
    path('repo/<int:pk>/claim/', views.ProfileClaim.as_view(), name='claim_profile'),
    path('repo/<str:user__username>/', views.ProfileDetail.as_view(), name='detail_username'),
    path('repo/<str:user__username>/recommend/', views.CreateRecommendation.as_view(), name='recommend_profile_username'),
    path('repo/<str:user__username>/claim/', views.ProfileClaim.as_view(), name='claim_profile_username'),

    path('publications/', views.PublicationsList.as_view(), name='publications'),
    path('faq/', TemplateView.as_view(
        template_name='profiles/faq.html',
        extra_context={'updated_at': faq_updated_at}
    ), name='faq'),
    path('tips/', TemplateView.as_view(
        template_name='profiles/tips.html',
        extra_context={'updated_at': tips_updated_at}
    ), name='tips'),
    path('about/', TemplateView.as_view(
        template_name='profiles/about.html',
        extra_context={'updated_at': about_updated_at}
    ), name='about'),
    path('academic_advice/', TemplateView.as_view(
        template_name='profiles/academic_advice.html',
        extra_context={'updated_at': about_updated_at}
    ), name='academic_advice'),

    path('profiles-autocomplete/', views.ProfilesAutocomplete.as_view(), name='profiles_autocomplete'),
    path('countries-autocomplete/', views.CountriesAutocomplete.as_view(), name='countries_autocomplete'),

    path('account/', views.UserView.as_view(), name='user'),
    path('account/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('account/change_password/', views.UserChangePasswordView.as_view(), name='user_change_password'),
    path('account/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/claim/', views.UserProfileClaimView.as_view(), name='user_profile_claim'),
    path('profile/edit/', views.UserProfileEditView.as_view(), name='user_profile_edit'),
    path('profile/delete/', views.UserProfileDeleteView.as_view(), name='user_profile_delete'),

    path('signup/', views.UserCreateView.as_view(), name='signup'),
    path('signup/confirm/', views.UserCreateConfirmView.as_view(), name='signup_confirm'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/forgot', views.UserPasswordResetView.as_view(), name='forgot'),
    path('login/forgot/confirm', views.UserPasswordResetConfirmView.as_view(), name='forgot_confirm'),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    path('', include(router.urls)),
#     path('api/', include('rest_framework.urls', namespace='rest_framework')),
]
