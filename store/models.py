from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import datetime 
from django.conf import settings
from ckeditor.fields import RichTextField
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from pathlib import Path
import uuid
# Create your models here.

class Category(models.Model):
	name = models.CharField(max_length=50)

	def __str__(self):
		return self.name

	class Meta:
		verbose_name_plural = 'categories'

class CustomUserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError("Email is required")
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		extra_fields.setdefault('is_active', True)

		return self.create_user(email, password, **extra_fields)


def user_profile_path(instance, filename):
	ext = Path(filename).suffix
	# Use user ID if exists, otherwise generate a temporary UUID
	user_id = instance.pk if instance.pk else uuid.uuid4()
	return f"uploads/user_image/{user_id}/{filename}"

class CustomUser(AbstractBaseUser, PermissionsMixin):
	email = models.EmailField(unique=True)
	username = models.CharField(max_length=150, blank=True)
	phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True, validators=[RegexValidator(regex=r'^\d{10}$', message='Enter a valid 10-digit phone number')])
	first_name = models.CharField(max_length=30, blank=True)
	last_name = models.CharField(max_length=30, blank=True)
	gender = models.CharField(max_length=6, blank=True)
	birthday = models.DateField(null=True, blank=True)
	is_staff = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	is_phone_active = models.BooleanField(default=False)
	is_email_active = models.BooleanField(default=False)
	date_joined = models.DateTimeField(default=timezone.now)
	profile_image = models.ImageField(upload_to=user_profile_path, null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])
	newsletter_subscribed = models.BooleanField(default=False)

	
	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []  # No username required

	objects = CustomUserManager()

	def get_display_name(self):
		if self.username:
			return self.username
		elif self.first_name:
			return self.first_name
		elif self.first_name and self.last_name:
			return f"{self.first_name} {self.last_name}"
		else:
			# Fallback to email username part
			return self.email.split('@')[0]
	
	def __str__(self):
		return self.get_display_name()


class Product(models.Model):
	name = models.CharField(max_length=100)
	slug = models.SlugField(unique=True, blank=True, null=True)
	price = models.DecimalField(default=0, decimal_places=2, max_digits=8)
	category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
	description = RichTextField(blank=True, null=True)
	is_sale = models.BooleanField(default=False)
	sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=8)
	stock = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	#SEO columns
	meta_title = models.CharField(max_length=150, blank=True, null=True)
	meta_description = models.CharField(max_length=300, blank=True, null=True)
	seo_updated_at = models.DateTimeField(auto_now=True)

	def get_meta_title(self):
		"""Returns meta title or generates one"""
		if self.meta_title:
			return self.meta_title
		return f"{self.name} - Firefly E-Commerce"
	
	def get_meta_description(self):
		"""Returns meta description or generates one"""
		if self.meta_description:
			return self.meta_description
		# Generate from description (strip HTML and truncate)
		from django.utils.html import strip_tags
		desc = strip_tags(self.description) if self.description else ''
		return desc[:155] + '...' if len(desc) > 155 else desc or f"Buy {self.name} at Firefly E-Commerce. High quality products with fast shipping."
	
	def get_canonical_url(self):
		"""Returns the canonical URL for this product"""
		from django.urls import reverse
		return reverse('product_detail', kwargs={'slug': self.slug})
	
	def save(self, *args, **kwargs):
		# Auto-generate slug if not exists
		if not self.slug:
			from django.utils.text import slugify
			self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class ProductVariant(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
	color_name = models.CharField(max_length=50)
	color_code = models.CharField(max_length=7, blank=True, null=True, help_text="Optional HEX code like #000000")
	extra_price = models.DecimalField(default=0, decimal_places=2, max_digits=8, help_text="Price difference if any")

	def __str__(self):
		return f"{self.product.name} - {self.color_name}"


class ProductImage(models.Model):
	variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="images")
	image = models.ImageField(upload_to="uploads/product/")

	def __str__(self):
		return f"Image for {self.variant.product.name} ({self.variant.color_name})"




User = get_user_model()

class EmailOTP(models.Model):

	PURPOSE_CHOICES = [
		('verification', 'Email Verification'),
		('password_reset', 'Password Reset'),
	]

	user = models.ForeignKey(User, on_delete=models.CASCADE)
	code = models.CharField(max_length=6)
	purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='verification')
	created_at = models.DateTimeField(auto_now_add=True)
	is_used = models.BooleanField(default=False)

	def is_valid(self):
		# OTP valid for 5 minutes
		return (timezone.now() - self.created_at).seconds < 300 and not self.is_used

	def __str__(self):
		return f"OTP for {self.user.email}: {self.code}"

class PhoneOTP(models.Model):
	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	code = models.IntegerField()
	created_at = models.DateTimeField(auto_now_add=True)
	attempts = models.IntegerField(default=0)
	verified = models.BooleanField(default=False)
	
	def is_expired(self):
		from datetime import timedelta
		from django.utils import timezone
		return timezone.now() > self.created_at + timedelta(minutes=5)

class Favorite(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
	created_at = models.DateTimeField(auto_now_add=True)

	
class CartItem(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)
	added_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.product.name} x {self.quantity}"



class Address(models.Model):
	ADDRESS_TYPES = (
		('shipping', 'Shipping'),
		('billing', 'Billing'),
	)
	
	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
	address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='shipping')
	
	# Address fields
	address_line1 = models.CharField(max_length=255)
	address_line2 = models.CharField(max_length=255, blank=True)
	city = models.CharField(max_length=100)
	state_province = models.CharField(max_length=100)
	zip_code = models.CharField(max_length=10, validators=[RegexValidator(r'^[0-9A-Za-z\- ]+$', 'Enter a valid postal code')])
	country = models.CharField(max_length=100)
	nickname = models.CharField(max_length=100, blank=True)
	
	
	# Convenience fields
	is_default = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		verbose_name_plural = 'Addresses'
		ordering = ['-is_default', '-created_at']
	
	def __str__(self):
		return f"{self.user.email} - {self.address_type} - {self.city}"


class Comment(models.Model):
	author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comments')
	product = models.ForeignKey(Product, related_name="comments", on_delete=models.CASCADE)
	#name = models.CharField(max_length=255)
	body = models.TextField()
	date_added = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-date_added']

	def __str__(self):
		author_name = self.author.get_display_name() if self.author else "Anonymous"
		return f'{self.product.name} - {author_name}'


class Reply(models.Model):
	author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="replies")
	parent_comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="replies")
	body = models.TextField()
	date_added = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-date_added']

	def __str__(self):
		author_name = self.author.get_display_name() if self.author else "Anonymous"
		return f'{self.parent_comment.product.name} - {author_name}'

class NewsletterSubscriber(models.Model):
	email = models.EmailField(unique=True)
	is_active = models.BooleanField(default=True)
	subscribed_at = models.DateTimeField(auto_now_add=True)
	unsubscribe_token = models.CharField(max_length=100, unique=True, blank=True)
	
	# Optional: link to CustomUser if they're registered
	user = models.OneToOneField(
		CustomUser, 
		on_delete=models.SET_NULL, 
		null=True, 
		blank=True,
		related_name='newsletter'
	)
	
	def __str__(self):
		return self.email
	
	def save(self, *args, **kwargs):
		# Generate unsubscribe token if not exists
		if not self.unsubscribe_token:
			import secrets
			self.unsubscribe_token = secrets.token_urlsafe(32)
		super().save(*args, **kwargs)
	
	class Meta:
		verbose_name = 'Newsletter Subscriber'
		verbose_name_plural = 'Newsletter Subscribers'
		ordering = ['-subscribed_at']