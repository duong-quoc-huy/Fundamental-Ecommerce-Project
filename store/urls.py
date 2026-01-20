from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.home,  name='home'),
    path('about_us/', views.about_us, name='about_us'),
    path('contact_us/', views.contact, name='contact_us'),
    path('cookies', views.cookies, name='cookies'),
    path('faq/', views.faq, name='faq'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms, name="term_of_service"),
    path('login/', views.login_user, name="login"),
    path('logout/', views.logout_user, name="logout"),
    path('register/', views.register_user, name="register"),
    path('send-otp/', views.send_otp_view, name='send_otp'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('product/<slug:slug>/', views.product, name='product'),
    path('get-images/<int:variant_id>/', views.get_variant_images, name='get_variant_images'),
    path('toggle-favorite/<int:product_id>/', views.toggle_favorite, name="toggle_favorite"),
    path('category/<str:foo>', views.category,  name='category'),
    path('account/update_user/', views.update_user, name='update_user'),
    path('account/update_password/', views.update_password, name='update_password'),
    path('account/addresses/', views.update_address, name='update_address'),  # List
    path('account/addresses/add/', views.add_address, name='add_address'),
    path('account/addresses/<int:address_id>/edit/', views.edit_address, name='edit_address'),
    path('account/addresses/<int:address_id>/delete/', views.delete_address, name='delete_address'),
    path('account/addresses/<int:address_id>/set-default/', views.set_default_address, name='set_default_address'),
    path('add-phone-number/', views.add_phone_number, name='add_phone_number'),
    path('verify-firebase-phone/', views.verify_firebase_phone, name='verify_firebase_phone'),
    path('add-comment/<int:product_id>/', views.add_comment, name='add_comment'),
    path('data-deletion/', TemplateView.as_view(template_name='data_deletion.html'), name='data_deletion'),
    path('delete-comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('add-reply/<int:comment_id>/', views.add_reply, name='add_reply'),
    path('delete-reply/<int:reply_id>/', views.delete_reply, name='delete_reply'),
    path('search/', views.search, name='search'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('resend-reset-otp/', views.resend_reset_otp, name='resend_reset_otp'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/unsubscribe/<str:token>/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
    #path('settings/', views.account_settings, name='account_settings') this one is for show linked accounts to social media

]

