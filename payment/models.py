from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


# Create your models here.
class ShippingAddress(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		null=True,
		blank=True
	)

	shipping_full_name = models.CharField(max_length=255)

	shipping_email = models.EmailField(max_length=255)

	shipping_phone = models.CharField(
		max_length=20,
		null=True,
		blank=True,
		validators=[
			RegexValidator(
				r'^\+?[0-9]{8,15}$',
				'Enter a valid phone number (8–15 digits, optional +).'
			)
		]
	)

	shipping_address1 = models.CharField(max_length=255)
	shipping_address2 = models.CharField(max_length=255, null=True, blank=True)

	shipping_city = models.CharField(max_length=255)

	shipping_state_province = models.CharField(max_length=255, null=True, blank=True)

	shipping_zipcode = models.CharField(
		max_length=12,
		validators=[
			RegexValidator(
				r'^[0-9A-Za-z\- ]+$',
				'Enter a valid postal code.'
			)
		]
	)

	shipping_country = models.CharField(max_length=255)

	class Meta:
		verbose_name_plural = "Shipping Address"

	def __str__(self):
		return f"{self.shipping_full_name} - {self.shipping_city}, {self.shipping_country}"


class Order(models.Model):
	ORDER_STATUS = (
		('pending', 'Pending'),
		('paid', 'Paid'),
		('processing', 'Processing'),
		('shipped', 'Shipped'),
		('completed', 'Completed'),
		('canceled', 'Canceled'),
	)

	coupon = models.ForeignKey(
		'Coupon', 
		on_delete=models.SET_NULL, 
		null=True, 
		blank=True,
		related_name='orders'
	)
	discount_amount = models.DecimalField(
		max_digits=10, 
		decimal_places=2, 
		default=0.00
	)

	order_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True)
	
	subtotal = models.DecimalField(max_digits=12, decimal_places=2)
	tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
	total = models.DecimalField(max_digits=12, decimal_places=2)
	
	status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
	created_at = models.DateTimeField(auto_now_add=True)
	paid_at = models.DateTimeField(null=True, blank=True)
	payment_method = models.CharField(max_length=20, choices=[
		('vnpay', 'VNPay'),
		('paypal', 'PayPal'),
	], null=True, blank=True)
	
	# Keep this generic for all providers
	payment_transaction_id = models.CharField(max_length=100, blank=True, null=True)

	def __str__(self):
		return f"Order {self.order_number}"

class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey('store.Product', on_delete=models.SET_NULL, null=True)
	quantity = models.PositiveIntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of purchase

	def __str__(self):
		return f"{self.quantity} × {self.product.name if self.product else 'Deleted Product'}"




class Coupon(models.Model):
	DISCOUNT_TYPE = (
		('percentage', 'Percentage'),
		('fixed', 'Fixed Amount'),
	)
	
	code = models.CharField(max_length=50, unique=True, db_index=True)
	description = models.TextField(blank=True)
	
	discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE, default='percentage')
	discount_value = models.DecimalField(
		max_digits=10, 
		decimal_places=2,
		validators=[MinValueValidator(0)]
	)
	
	# Optional: Maximum discount amount (useful for percentage coupons)
	max_discount = models.DecimalField(
		max_digits=10, 
		decimal_places=2, 
		null=True, 
		blank=True,
		validators=[MinValueValidator(0)]
	)
	
	# Minimum order value required
	min_order_value = models.DecimalField(
		max_digits=10, 
		decimal_places=2, 
		default=0,
		validators=[MinValueValidator(0)]
	)
	
	# Usage limits
	max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="Total number of times this coupon can be used")
	max_uses_per_user = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum uses per user")
	current_uses = models.PositiveIntegerField(default=0)
	
	# Date restrictions
	valid_from = models.DateTimeField()
	valid_until = models.DateTimeField()
	
	# Status
	is_active = models.BooleanField(default=True)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['-created_at']
	
	def __str__(self):
		return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else ' USD'}"
	#Check if coupon is currently valid
	def is_valid(self):
		
		now = timezone.now()
		if not self.is_active:
			return False, "This coupon is not active."
		if now < self.valid_from:
			return False, "This coupon is not yet valid."
		if now > self.valid_until:
			return False, "This coupon has expired."
		if self.max_uses and self.current_uses >= self.max_uses:
			return False, "This coupon has reached its usage limit."
		return True, "Coupon is valid"
	
	#Calculate discount amount based on subtotal
	def calculate_discount(self, subtotal):
		if self.discount_type == 'percentage':
			discount = subtotal * (self.discount_value / 100)
			if self.max_discount:
				discount = min(discount, self.max_discount)
		else:  # fixed
			discount = min(self.discount_value, subtotal)
		return discount
	

	#Check if user can still use this coupon
	def can_be_used_by_user(self, user):
		if not self.max_uses_per_user:
			return True, "Can use"
		
		usage_count = CouponUsage.objects.filter(
			coupon=self,
			user=user
		).count()
		
		if usage_count >= self.max_uses_per_user:
			return False, "You have already used this coupon the maximum number of times."
		return True, "Can use"

#Track coupon usage
class CouponUsage(models.Model):
	coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	order = models.ForeignKey('Order', on_delete=models.CASCADE)
	discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
	used_at = models.DateTimeField(auto_now_add=True)
	
	class Meta:
		ordering = ['-used_at']
	
	def __str__(self):
		return f"{self.user.username} used {self.coupon.code} on {self.order.order_number}"