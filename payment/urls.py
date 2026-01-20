from django.urls import path
from . import views
app_name = "payment"
urlpatterns = [
	path('payment_success', views.payment_success, name='payment_success'),
	path('checkout/', views.checkout_shipping, name='checkout_shipping'),
	path('vnpay-return/', views.vnpay_return, name='vnpay_return'),
	path('paypal-create/', views.paypal_create_order, name='paypal_create'),
	path('paypal-return/', views.paypal_return, name='paypal_return'),
	path('paypal-cancel/', views.paypal_cancel, name='paypal_cancel'),
	path('history/', views.payment_history, name='payment_history'),
	path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
	path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
]