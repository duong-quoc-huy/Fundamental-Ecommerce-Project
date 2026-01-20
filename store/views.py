from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, ProductVariant, ProductImage, Favorite, Category, Reply, Comment
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UpdateAddressForm, CommentForm, ForgotPasswordForm, ResetPasswordForm, NewsletterSubscriptionForm
from django import forms
from .forms import OTPForm
from .utils import send_otp_via_email
from .models import EmailOTP, CustomUser, PhoneOTP, Address, Comment, NewsletterSubscriber
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from cart.cart import Cart
from .forms import PhoneCaptchaForm
import phonenumbers
import traceback
import logging
from firebase_admin import auth as firebase_auth
import json
from .mailchimp_service import MailchimpService
from .email_utils import send_welcome_email
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.views import View
from django.urls import is_valid_path
from django.utils.http import url_has_allowed_host_and_scheme
from .mailchimp_service import MailchimpService
from django.db.models import Q
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
# Create your views here.

class GoogleVerificationView(View):
	def get(self, request):
		return HttpResponse("google-site-verification: google9162f3f05492581f.html")



class RobotsView(TemplateView):
	template_name = 'robots.txt'
	content_type = 'text/plain'

def home(request):
	products = Product.objects.all()
	
	# Get user's favorites to show on home page
	favorites = []
	if request.user.is_authenticated:
		favorites = Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
	
	return render(request, 'home.html', {
		'products': products,
		'favorites': list(favorites)
	})


def about_us(request):
	return render (request, 'about_us.html', {})


def contact(request):
	return render(request, 'contact.html', {})


def cookies(request):
	return render(request, 'cookies.html', {})


def faq(request):
	return render(request, 'FAQ.html', {})


def privacy_policy(request):
	return render(request, 'privacy.html', {})


def terms(request):
	return render(request, 'terms.html', {})


def login_user(request):
	if request.user.is_authenticated:
		return redirect('home')
	
	if request.method == "POST":
		email = request.POST.get('email')
		password = request.POST.get('password')
		
		user = authenticate(request, email=email, password=password)
		
		if user is not None:
			if not user.is_active:
				messages.warning(request, "Your email has not been verified. Please enter the OTP sent to your email.")
				send_otp_via_email(user)
				request.session['pending_user_email'] = email
				return redirect('verify_otp')
			else:
				login(request, user)
				cart = Cart(request)
				cart.merge_to_database(user)
				messages.success(request, "You have logged in successfully!")
				next_url = request.GET.get('next') or request.POST.get('next')
				if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
					return redirect(next_url)
				else:
					return redirect('home')
		else:
			messages.error(request, "Invalid credentials. Please try again.")
			return redirect('login')
	
	return render(request, 'login.html', {})

@login_required
def logout_user(request):
	logout(request)
	messages.success(request, ("You have been logged out."))
	return redirect('home')



def register_user(request):
	if request.method == "POST":
		form = SignUpForm(request.POST)
		if form.is_valid():
			if 'term_of_service_and_privacy' in request.POST:
				user = form.save(commit=False)
				user.is_active = False
				user.newsletter_subscribed = form.cleaned_data.get('subscribe_news', False)
				user.save()
				
				# Subscribe to Mailchimp if user opted in
				if user.newsletter_subscribed:
					mailchimp = MailchimpService()
					success, response = mailchimp.subscribe_user(
						email=user.email,
						first_name=getattr(user, 'first_name', ''),
						last_name=getattr(user, 'last_name', '')
					)
					if not success:
						# Log the error but don't stop registration
						print(f"Mailchimp subscription failed: {response}")
				
				# Send OTP
				send_otp_via_email(user)
				messages.info(request, "We've sent a verification code to your email.")
				request.session['pending_user_id'] = user.id
				return redirect('verify_otp')
			else:
				form.add_error(None, 'You must agree to the terms of service and privacy policy.')
		else:
			messages.error(request, "Please correct the errors below.")
	else:
		form = SignUpForm()
	return render(request, 'register.html', {'form': form})



def send_otp_view(request):
	user = request.user
	send_otp_via_email(user)
	messages.success(request, "OTP has been sent to your email.")
	return redirect('verify_otp')

def verify_otp_view(request):
	user_id = request.session.get('pending_user_id')
	user_email = request.session.get('pending_user_email')
	
	if not user_id and not user_email:
		messages.error(request, "Session expired. Please try again.")
		return redirect('register')
	
	try:
		if user_id:
			user = CustomUser.objects.get(id=user_id)
		else:
			user = CustomUser.objects.get(email=user_email)
	except CustomUser.DoesNotExist:
		messages.error(request, "User not found. Please register again.")
		# Clean up invalid session
		request.session.pop('pending_user_id', None)
		request.session.pop('pending_user_email', None)
		return redirect('register')
	
	if request.method == "POST":
		form = OTPForm(request.POST)
		if form.is_valid():
			entered_otp = form.cleaned_data['otp']
			
			try:
				otp_record = EmailOTP.objects.filter(
					code=entered_otp, 
					user=user,
					is_used=False
				).latest('created_at')
				
				if otp_record.is_valid():
					otp_record.is_used = True
					otp_record.save()
					
					user.is_active = True
					user.is_email_active = True
					user.save()

					send_welcome_email(
						user_email=user.email,
						user_name=user.first_name or 'there'
					)
					
					messages.success(request, "Your account has been verified! You can now log in.")
					
					# Clean up session
					request.session.pop('pending_user_id', None)
					request.session.pop('pending_user_email', None)
					
					return redirect('login')
				else:
					messages.error(request, "This OTP has expired. Please request a new one.")
			except EmailOTP.DoesNotExist:
				messages.error(request, "Invalid OTP. Please try again.")
	else:
		form = OTPForm()
	
	return render(request, 'verify_otp.html', {
		'form': form,
		'user_email': user.email  
	})


def resend_otp_view(request):
	user_id = request.session.get('pending_user_id')
	user_email = request.session.get('pending_user_email')
	
	if not user_id and not user_email:
		messages.error(request, "Session expired. Please try again.")
		return redirect('register')
	
	try:
		if user_id:
			user = CustomUser.objects.get(id=user_id)
		else:
			user = CustomUser.objects.get(email=user_email)
	except CustomUser.DoesNotExist:
		messages.error(request, "User not found. Please try again.")
		request.session.pop('pending_user_id', None)
		request.session.pop('pending_user_email', None)
		return redirect('register')
	
	# Prevent spam
	latest_otp = EmailOTP.objects.filter(user=user).order_by('-created_at').first()
	if latest_otp and (timezone.now() - latest_otp.created_at) < timedelta(minutes=1):
		messages.warning(request, "Please wait a minute before requesting a new OTP.")
		return redirect('verify_otp')
	
	send_otp_via_email(user)
	messages.success(request, "A new OTP has been sent to your email.")
	return redirect('verify_otp')


def product(request, slug):
	# Optimize with select_related and prefetch_related
	product = get_object_or_404(
		Product.objects
			.select_related('category')  # Get category in same query
			.prefetch_related(
				'variants__images',  # Preload all variant images
				Prefetch(
					'comments',
					queryset=Comment.objects.select_related('author')
										   .prefetch_related(
											   Prefetch(
												   'replies',
												   queryset=Reply.objects.select_related('author')
											   )
										   )
										   .order_by('-date_added')
				)
			),
		slug=slug
	)
	
	comment_form = CommentForm()
	
	# Get user's favorites
	favorites = []
	if request.user.is_authenticated:
		favorites = list(Favorite.objects.filter(user=request.user).values_list('product_id', flat=True))
	
	# Cache first variant and image for template
	first_variant = product.variants.first() if product.variants.exists() else None
	first_image = first_variant.images.first() if first_variant and first_variant.images.exists() else None
	
	return render(request, 'product.html', {
		'product': product,
		'first_variant': first_variant,
		'first_image': first_image,
		'favorites': favorites,
		'comment_form': comment_form
	})

	

def get_variant_images(request, variant_id):
	variant = get_object_or_404(ProductVariant, id=variant_id)
	images = variant.images.all()

	image_urls = [image.image.url for image in images]

	return JsonResponse({'images': image_urls})


@login_required
def toggle_favorite(request, product_id):
	product = get_object_or_404(Product, id=product_id)
	
	# Try to get or create favorite
	favorite, created = Favorite.objects.get_or_create(
		user=request.user, 
		product=product
	)
	
	if not created:
		# Favorite already existed, so remove it (unfavorite)
		favorite.delete()
		return JsonResponse({'status': 'removed'})
	else:
		# New favorite was created (favorite)
		return JsonResponse({'status': 'added'})


def category(request, foo):
	#replace hyphens with spaces
	foo = foo.replace('-', ' ')
	try:
		category = Category.objects.get(name=foo)
		products = Product.objects.filter(category=category)
		return render(request, 'category.html', {'products':products, 'category':category})
	except:
		messages.success(request, ("That Category didn't exist"))
		return redirect('home')

@login_required
def update_user(request):
	if request.user.is_authenticated:
		current_user = request.user

		if request.method == 'POST':
			print("=== UPDATE USER POST REQUEST ===")
			print("POST data:", request.POST)
			
			user_form = UpdateUserForm(
				request.POST,
				request.FILES,
				instance=current_user
			)

			if user_form.is_valid():
				print("=== FORM IS VALID ===")
				print("Before save - First name:", current_user.first_name)
				print("Form cleaned data:", user_form.cleaned_data)
				
				saved_user = user_form.save()
				
				print("After save - First name:", saved_user.first_name)
				print("Database value:", CustomUser.objects.get(pk=saved_user.pk).first_name)
				
				messages.success(request, "User has been updated!")
				return redirect('update_user')
			else:
				print("=== FORM ERRORS ===")
				print(user_form.errors)
				
				for field, errors in user_form.errors.items():
					for error in errors:
						messages.error(request, f"{field}: {error}")
		else:
			user_form = UpdateUserForm(instance=current_user)

		context = {
			'user_form': user_form,
			'user_phone': current_user.phone_number,
		}

		return render(request, 'update_user.html', context)
	else:
		messages.error(request, "You are not logged in")
		return redirect('login')

@login_required
def update_password(request):
	if request.user.is_authenticated:
		current_user = request.user
		if request.method == 'POST':
			form = ChangePasswordForm(current_user, request.POST)
			#is the form valid
			if form.is_valid():
				form.save()
				messages.success(request, "Password Updated.")
				return redirect('login')

			else:
				for error in list(form.errors.values()):
					messages.error(request, error)
					return redirect('update_password')

		else:
			form = ChangePasswordForm(current_user)
			return render(request, 'update_password.html', {'form':form})
	else:
		messages.success(request, "You are not logged in")
		return redirect('login')



@login_required
def update_address(request):
	addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
	return render(request, 'address_list.html', {'addresses': addresses})


@login_required
def add_address(request):
	if request.method == 'POST':
		form = UpdateAddressForm(request.POST)
		if form.is_valid():
			address = form.save(commit=False)
			address.user = request.user
			
			# If user checked "set as default" OR this is their first address
			if form.cleaned_data.get('is_default') or not Address.objects.filter(user=request.user).exists():
				# Remove default from all other addresses
				Address.objects.filter(user=request.user).update(is_default=False)
				address.is_default = True
			
			address.save()
			messages.success(request, "Address added successfully!")
			return redirect('update_address')
		else:
			for field, errors in form.errors.items():
				for error in errors:
					messages.error(request, f"{field}: {error}")
	else:
		form = UpdateAddressForm()
	
	return render(request, 'add_address.html', {'form': form})


@login_required
def edit_address(request, address_id):
	address = get_object_or_404(Address, id=address_id, user=request.user)
	
	if request.method == 'POST':
		form = UpdateAddressForm(request.POST, instance=address)
		if form.is_valid():
			updated_address = form.save(commit=False)
			
			# If user checked "set as default"
			if form.cleaned_data.get('is_default'):
				# Remove default from all other addresses
				Address.objects.filter(user=request.user).exclude(id=address_id).update(is_default=False)
				updated_address.is_default = True
			
			updated_address.save()
			messages.success(request, "Address updated successfully!")
			return redirect('update_address')
		else:
			for field, errors in form.errors.items():
				for error in errors:
					messages.error(request, f"{field}: {error}")
	else:
		form = UpdateAddressForm(instance=address)
	
	return render(request, 'edit_address.html', {'form': form, 'address': address})


@login_required
def delete_address(request, address_id):
	address = get_object_or_404(Address, id=address_id, user=request.user)
	
	
	if Address.objects.filter(user=request.user).count() == 1:
		messages.warning(request, "You must have at least one address.")
		return redirect('update_address')
	
	
	if address.is_default:
		address.delete()
		# Set the most recent address as default
		next_address = Address.objects.filter(user=request.user).first()
		if next_address:
			next_address.is_default = True
			next_address.save()
	else:
		address.delete()
	
	messages.success(request, "Address deleted successfully!")
	return redirect('update_address')


@login_required
def set_default_address(request, address_id):
	address = get_object_or_404(Address, id=address_id, user=request.user)
	
	# Remove default from all other addresses
	Address.objects.filter(user=request.user).update(is_default=False)
	
	# Set this one as default
	address.is_default = True
	address.save()
	
	messages.success(request, "Default address updated!")
	return redirect('update_address')



@login_required
def add_phone_number(request):
	"""Validate phone number and prepare for Firebase verification"""
	print("\n" + "="*60)
	print("ADD_PHONE_NUMBER VIEW - Firebase Version (No Django CAPTCHA)")
	print("="*60)
	print(f"Method: {request.method}")
	print(f"User: {request.user.email} (ID: {request.user.id})")
	
	if request.method != "POST":
		print("✗ Invalid method")
		return JsonResponse({
			'success': False,
			'error': 'Invalid request method'
		}, status=405)

	# REMOVED: Django CAPTCHA check
	# Firebase reCAPTCHA will handle bot protection

	# Get phone number
	phone_number = request.POST.get('phone_input')
	print(f"\n--- Phone Number ---")
	print(f"Received: {phone_number}")
	
	if not phone_number:
		print("✗ No phone number provided")
		return JsonResponse({
			'success': False,
			'error': 'Phone number required'
		}, status=400)

	# Validate E.164
	if not phone_number.startswith('+'):
		print("✗ Phone doesn't start with +")
		return JsonResponse({
			'success': False,
			'error': 'Invalid phone format'
		}, status=400)

	# Validate with phonenumbers
	print("\n--- Validating phone number ---")
	try:
		parsed = phonenumbers.parse(phone_number, None)
		print(f"Parsed: {parsed}")
		print(f"Country code: +{parsed.country_code}")
		print(f"National number: {parsed.national_number}")
		
		if not phonenumbers.is_valid_number(parsed):
			print("✗ Invalid phone number")
			return JsonResponse({
				'success': False,
				'error': 'Phone number is not valid'
			}, status=400)
		
		print("✓ Phone number is valid")
		
	except Exception as e:
		print(f"✗ Parsing error: {e}")
		return JsonResponse({
			'success': False,
			'error': 'Invalid phone number'
		}, status=400)

	# Normalize to E.164
	phone_number = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
	print(f"✓ Normalized to: {phone_number}")

	# Unique check
	print("\n--- Checking uniqueness ---")
	User = get_user_model()
	existing = User.objects.filter(phone_number=phone_number).exclude(pk=request.user.pk).exists()
	
	if existing:
		print(f"✗ Phone {phone_number} already registered to another user")
		return JsonResponse({
			'success': False,
			'error': 'This phone number is already registered'
		}, status=400)
	
	print("✓ Phone number is unique")

	# Save to session
	print("\n--- Saving to session ---")
	request.session['pending_phone'] = phone_number
	print(f"✓ Saved pending_phone to session: {phone_number}")


	print("\n--- SUCCESS ---")
	print(f"Phone validated. Ready for Firebase OTP.")
	print("="*60 + "\n")
	
	# Return phone number so frontend can use it with Firebase
	return JsonResponse({
		'success': True,
		'phone_number': phone_number,
		'message': 'Phone number validated. Proceed with verification.'
	})



@login_required
def verify_firebase_phone(request):
	"""Verify phone number using Firebase ID token"""
	print("\n" + "="*60)
	print("VERIFY_FIREBASE_PHONE VIEW")
	print("="*60)
	
	if request.method != "POST":
		return JsonResponse({
			'success': False,
			'error': 'Invalid request method'
		}, status=405)
	
	try:
		# Get the Firebase ID token from request
		data = json.loads(request.body)
		id_token = data.get('idToken')
		
		if not id_token:
			print("✗ No ID token provided")
			return JsonResponse({
				'success': False,
				'error': 'No verification token provided'
			}, status=400)
		
		print(f"✓ Received ID token")
		
		# Get pending phone from session
		pending_phone = request.session.get('pending_phone')
		print(f"Session pending_phone: {pending_phone}")
		
		if not pending_phone:
			print("✗ No pending phone in session")
			return JsonResponse({
				'success': False,
				'error': 'Session expired. Please start over.'
			}, status=400)
		
		# Verify the Firebase token
		print("\n--- Verifying Firebase token ---")
		decoded_token = firebase_auth.verify_id_token(id_token)
		print(f"✓ Token verified")
		
		# Get phone number from Firebase token
		verified_phone = decoded_token.get('phone_number')
		print(f"Verified phone from Firebase: {verified_phone}")
		print(f"Expected phone from session: {pending_phone}")
		
		# Make sure phones match
		if verified_phone != pending_phone:
			print("✗ Phone number mismatch!")
			return JsonResponse({
				'success': False,
				'error': 'Phone number verification failed'
			}, status=400)
		
		print("✓ Phone numbers match!")
		
		# Save phone number to user
		print("\n--- Saving phone number ---")
		request.user.phone_number = pending_phone
		request.user.save()
		print(f"✓ Phone saved to user: {request.user.phone_number}")
		
		# Optional: Create PhoneOTP record for logging
		PhoneOTP.objects.create(
			user=request.user,
			code=000000,  # Placeholder - Firebase handled the actual OTP
			verified=True
		)
		print("✓ Created PhoneOTP record for logging")
		
		# Clean up old unverified OTPs
		PhoneOTP.objects.filter(user=request.user, verified=False).delete()
		
		# Clear session
		del request.session['pending_phone']
		print("✓ Cleared pending_phone from session")
		
		print("\n--- SUCCESS ---")
		print(f"Phone {pending_phone} verified and saved!")
		print("="*60 + "\n")
		
		return JsonResponse({
			'success': True,
			'message': 'Phone number verified successfully!',
			'phone_number': pending_phone
		})
		
	except firebase_auth.InvalidIdTokenError:
		print("✗ Invalid Firebase token")
		return JsonResponse({
			'success': False,
			'error': 'Invalid verification token'
		}, status=400)
		
	except firebase_auth.ExpiredIdTokenError:
		print("✗ Expired Firebase token")
		return JsonResponse({
			'success': False,
			'error': 'Verification token expired'
		}, status=400)
		
	except Exception as e:
		print(f"\n✗ ERROR: {type(e).__name__}")
		print(f"Message: {str(e)}")
		import traceback
		print(traceback.format_exc())
		
		return JsonResponse({
			'success': False,
			'error': f'Verification failed: {str(e)}'
		}, status=500)

@login_required
def add_comment(request, product_id):
	product = get_object_or_404(Product, id=product_id)
	
	if request.method == 'POST':
		form = CommentForm(request.POST)
		if form.is_valid():
			comment = form.save(commit=False)
			comment.author = request.user
			comment.product = product
			comment.save()
			
			return JsonResponse({
				'success': True,
				'author_name': request.user.get_display_name(),
				'body': comment.body,
				'date_added': comment.date_added.strftime('%b %d, %Y')
			})
		else:
			return JsonResponse({'success': False, 'message': 'Invalid comment data'})
	
	return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def delete_comment(request, comment_id):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'message': 'Invalid request'}, status=405)
	
	comment = get_object_or_404(Comment, id=comment_id)
	
	
	if comment.author != request.user:
		return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
	
	comment.delete()
	return JsonResponse({'success': True})

@login_required
def add_reply(request, comment_id):
	comment = get_object_or_404(Comment, id=comment_id)
	
	if request.method == 'POST':
		body = request.POST.get('body')
		if body:
			reply = Reply.objects.create(
				author=request.user,
				parent_comment=comment,
				body=body
			)
			
			return JsonResponse({
				'success': True,
				'reply_id': reply.id,
				'author_name': request.user.get_display_name(),
				'body': reply.body,
				'date_added': reply.date_added.strftime('%b %d, %Y')
			})
		else:
			return JsonResponse({'success': False, 'message': 'Reply cannot be empty'})
	
	return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def delete_reply(request, reply_id):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'message': 'Invalid request'}, status=405)
	
	reply = get_object_or_404(Reply, id=reply_id)
	
	if reply.author != request.user:
		return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
	
	reply.delete()
	return JsonResponse({'success': True})


def search(request):
	query = request.GET.get('q', '')
	category_filter = request.GET.get('category', '')
	sort_by = request.GET.get('sort', '')
	
	products = Product.objects.all()
	categories = Category.objects.all()
	
	# Apply search query
	if query:
		products = products.filter(
			Q(name__icontains=query) | 
			Q(description__icontains=query) |
			Q(category__name__icontains=query)
		)
	
	# Apply category filter
	if category_filter:
		products = products.filter(category__id=category_filter)
	
	# Apply sorting
	if sort_by == 'price_low':
		products = products.order_by('price')
	elif sort_by == 'price_high':
		products = products.order_by('-price')
	elif sort_by == 'name':
		products = products.order_by('name')
	elif sort_by == 'newest':
		products = products.order_by('-created_at')
	else:
		products = products.order_by('-created_at')  # default
	
	context = {
		'products': products,
		'categories': categories,
		'query': query,
		'selected_category': category_filter,
		'selected_sort': sort_by,
		'total_results': products.count()
	}
	
	return render(request, 'search.html', context)

# @login_required Note: this one is for showing social app linked
# def account_settings(request):
# 	return render(request, 'account_settings.html', {'user': request.user})

# views.py - Add these views

def forgot_password(request):
	if request.method == 'POST':
		form = ForgotPasswordForm(request.POST)
		if form.is_valid():
			email = form.cleaned_data['email']
			
			try:
				user = CustomUser.objects.get(email=email)
				
				# Check rate limiting
				latest_otp = EmailOTP.objects.filter(
					user=user, 
					purpose='password_reset'
				).order_by('-created_at').first()
				
				if latest_otp and (timezone.now() - latest_otp.created_at) < timedelta(minutes=1):
					messages.warning(request, "Please wait a minute before requesting a new OTP.")
					return redirect('forgot_password')
				
				# Send OTP
				send_otp_via_email(user, purpose='password_reset')
				
				# Store email in session
				request.session['reset_password_email'] = email
				
				messages.success(request, "Password reset code sent to your email.")
				return redirect('reset_password')
				
			except CustomUser.DoesNotExist:
				# Don't reveal if email exists or not (security best practice)
				messages.success(request, "If that email exists, a reset code has been sent.")
				return redirect('forgot_password')
	else:
		form = ForgotPasswordForm()
	
	return render(request, 'forgot_password.html', {'form': form})


def reset_password(request):
	email = request.session.get('reset_password_email')
	
	if not email:
		messages.error(request, "Session expired. Please request a new reset code.")
		return redirect('forgot_password')
	
	try:
		user = CustomUser.objects.get(email=email)
	except CustomUser.DoesNotExist:
		messages.error(request, "Invalid session. Please try again.")
		request.session.pop('reset_password_email', None)
		return redirect('forgot_password')
	
	if request.method == 'POST':
		form = ResetPasswordForm(request.POST)
		if form.is_valid():
			otp_code = form.cleaned_data['otp']
			new_password = form.cleaned_data['new_password']
			
			try:
				otp_record = EmailOTP.objects.filter(
					user=user,
					code=otp_code,
					purpose='password_reset',
					is_used=False
				).latest('created_at')
				
				if otp_record.is_valid():
					# Mark OTP as used
					otp_record.is_used = True
					otp_record.save()
					
					# Reset password
					user.set_password(new_password)
					user.save()
					
					# Clear session
					request.session.pop('reset_password_email', None)
					
					messages.success(request, "Password reset successfully! You can now login.")
					return redirect('login')
				else:
					messages.error(request, "OTP has expired. Please request a new one.")
			except EmailOTP.DoesNotExist:
				messages.error(request, "Invalid OTP. Please try again.")
	else:
		form = ResetPasswordForm()
	
	return render(request, 'reset_password.html', {
		'form': form,
		'email': email
	})


def resend_reset_otp(request):
	email = request.session.get('reset_password_email')
	
	if not email:
		messages.error(request, "Session expired. Please start over.")
		return redirect('forgot_password')
	
	try:
		user = CustomUser.objects.get(email=email)
		
		# Rate limiting
		latest_otp = EmailOTP.objects.filter(
			user=user,
			purpose='password_reset'
		).order_by('-created_at').first()
		
		if latest_otp and (timezone.now() - latest_otp.created_at) < timedelta(minutes=1):
			messages.warning(request, "Please wait a minute before requesting a new OTP.")
			return redirect('reset_password')
		
		send_otp_via_email(user, purpose='password_reset')
		messages.success(request, "A new reset code has been sent to your email.")
		
	except CustomUser.DoesNotExist:
		messages.error(request, "User not found.")
		request.session.pop('reset_password_email', None)
		return redirect('forgot_password')
	
	return redirect('reset_password')


@require_http_methods(["POST"])
def newsletter_subscribe(request):
	email = request.POST.get('email', '').strip()
	
	if not email:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({'success': False, 'message': 'Email is required'}, status=400)
		messages.error(request, 'Please enter a valid email address.')
		return redirect(request.META.get('HTTP_REFERER', '/'))
	
	# Check if already subscribed
	existing = NewsletterSubscriber.objects.filter(email=email).first()
	
	if existing:
		if existing.is_active:
			message = 'You are already subscribed to our newsletter!'
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				return JsonResponse({'success': False, 'message': message})
			messages.info(request, message)
			return redirect(request.META.get('HTTP_REFERER', '/'))
		else:
			# Reactivate subscription
			existing.is_active = True
			existing.save()
			subscriber = existing
			message = 'Welcome back! Your subscription has been reactivated.'
	else:
		# Create new subscription
		try:
			subscriber = NewsletterSubscriber.objects.create(email=email)
			
			# Link to user account if logged in
			if request.user.is_authenticated:
				subscriber.user = request.user
				subscriber.save()
				
				# Update user's newsletter_subscribed field
				request.user.newsletter_subscribed = True
				request.user.save()
			
			message = 'Successfully subscribed! Check your email for confirmation.'
		except Exception as e:
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)
			messages.error(request, 'An error occurred. Please try again.')
			return redirect(request.META.get('HTTP_REFERER', '/'))
	
	# Send welcome email
	try:
		send_newsletter_welcome_email(request, subscriber)
	except Exception as e:
		print(f"Error sending email: {e}")
	
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		return JsonResponse({'success': True, 'message': message})
	
	messages.success(request, message)
	return redirect(request.META.get('HTTP_REFERER', '/'))


def send_newsletter_welcome_email(request, subscriber):
	context = {
		'email': subscriber.email,
		'shop_url': request.build_absolute_uri('/'),
		'unsubscribe_url': request.build_absolute_uri(
			f'/newsletter/unsubscribe/{subscriber.unsubscribe_token}/'
		),
		'privacy_url': request.build_absolute_uri('/privacy-policy/'),
	}
	
	# Render HTML email
	html_message = render_to_string('emails/newsletter_welcome.html', context)
	plain_message = strip_tags(html_message)
	
	# Send email
	send_mail(
		subject='Welcome to Firefly E-Commerce Newsletter! 🔥',
		message=plain_message,
		from_email=settings.DEFAULT_FROM_EMAIL,
		recipient_list=[subscriber.email],
		html_message=html_message,
		fail_silently=False,
	)


def newsletter_unsubscribe(request, token):
	try:
		subscriber = NewsletterSubscriber.objects.get(unsubscribe_token=token)
		
		if request.method == 'POST':
			subscriber.is_active = False
			subscriber.save()
			
			# Update user's newsletter_subscribed field if linked
			if subscriber.user:
				subscriber.user.newsletter_subscribed = False
				subscriber.user.save()
			
			messages.success(request, 'You have been successfully unsubscribed from our newsletter.')
			return redirect('home')
		
		return render(request, 'newsletter/unsubscribe_confirm.html', {
			'subscriber': subscriber
		})
		
	except NewsletterSubscriber.DoesNotExist:
		messages.error(request, 'Invalid unsubscribe link.')
		return redirect('home')