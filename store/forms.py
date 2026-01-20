from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django import forms
from .models import CustomUser, Address, Comment, NewsletterSubscriber
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
import phonenumbers

class UpdateAddressForm(forms.ModelForm):  
	class Meta:
		model = Address
		fields = [
			'address_line1',
			'address_line2', 
			'city',
			'state_province',
			'zip_code',
			'country',
			'is_default',
			'nickname'
		]
	
	def __init__(self, *args, **kwargs):  # Fixed: *args not **args
		super(UpdateAddressForm, self).__init__(*args, **kwargs)
		
		# Address Line 1
		self.fields['address_line1'].widget.attrs.update({
			'class': 'form-control neu-input-field',
			'placeholder': 'Enter street address'
		})
		self.fields['address_line1'].label = 'Street Address'
		
		# Address Line 2
		self.fields['address_line2'].widget.attrs.update({
			'class': 'form-control neu-input-field',  
			'placeholder': 'Apt, Suite, Unit, Floor (optional)'
		})
		self.fields['address_line2'].label = 'Apt/Suite/Unit'
		self.fields['address_line2'].required = False 
		
		# City
		self.fields['city'].widget.attrs.update({
			'class': 'form-control neu-input-field',  
			'placeholder': 'Enter city'
		})
		self.fields['city'].label = 'City'
		
		# State/Province
		self.fields['state_province'].widget.attrs.update({  
			'class': 'form-control neu-input-field',  
			'placeholder': 'Enter state or province'
		})
		self.fields['state_province'].label = 'State/Province'
		
		# Zip Code
		self.fields['zip_code'].widget.attrs.update({  
			'class': 'form-control neu-input-field',  
			'placeholder': 'Enter zip/postal code'
		})
		self.fields['zip_code'].label = 'Zip/Postal Code'
		
		# Country
		self.fields['country'].widget.attrs.update({
			'class': 'form-control neu-input-field', 
			'placeholder': 'Enter country'
		})
		self.fields['country'].label = 'Country'
		
		# Is Default checkbox
		self.fields['is_default'].widget.attrs.update({
			'class': 'form-check-input'
		})
		self.fields['is_default'].label = 'Set as default address'

		# Nickname
		self.fields['nickname'].widget.attrs.update({
			'class': 'form-control neu-input-field',  
			'placeholder': 'Enter nickname. Such as: Home, Workplace, etc'
		})
		self.fields['nickname'].label = 'Nickname'



class ChangePasswordForm(PasswordChangeForm):
	def __init__(self, *args, **kwargs):
		super(ChangePasswordForm, self).__init__(*args, **kwargs)
		
		# Style old password field
		self.fields['old_password'].widget.attrs.update({
			'class': 'form-control neu-input-field',
			'placeholder': 'Current Password'
		})
		self.fields['old_password'].label = 'Current Password'
		
		# Style new password field
		self.fields['new_password1'].widget.attrs.update({
			'class': 'form-control neu-input-field',
			'placeholder': 'New Password'
		})
		self.fields['new_password1'].label = 'New Password'
		
		# Style confirm password field
		self.fields['new_password2'].widget.attrs.update({
			'class': 'form-control neu-input-field',
			'placeholder': 'Confirm New Password'
		})
		self.fields['new_password2'].label = 'Confirm Password'


class UpdateUserForm(UserChangeForm):
	password = None
	email = forms.EmailField(
		label="", 
		widget=forms.TextInput(attrs={
			'class':'form-control neu-input-field', 
			'placeholder':'Email Address'
		})
	)
	first_name = forms.CharField(
		label="", 
		max_length=100, 
		widget=forms.TextInput(attrs={
			'class':'form-control neu-input-field', 
			'placeholder':'First Name'
		})
	)
	last_name = forms.CharField(
		label="", 
		max_length=100, 
		widget=forms.TextInput(attrs={
			'class':'form-control neu-input-field', 
			'placeholder':'Last Name'
		})
	)

	GENDER_CHOICES = [
		('Male', 'Male'),
		('Female', 'Female'),
		('Other', 'Other'),
	]
	gender = forms.ChoiceField(
		label="Gender", 
		required=False, 
		widget=forms.RadioSelect(attrs={'class': 'form-check-input'}), 
		choices=GENDER_CHOICES
	)

	profile_image = forms.ImageField(
		label="Profile Picture",
		required=False,
		widget=forms.FileInput(attrs={
			'class': 'form-control neu-input-field',
			'accept': "image/png, image/jpeg, image/jpg"
		})
	)

	
	class Meta:
		model = get_user_model() 
		fields = ('email', 'first_name', 'last_name','gender', 'birthday', 'profile_image')

	def __init__(self, *args, **kwargs):
		super(UpdateUserForm, self).__init__(*args, **kwargs)
		
		# Email field styling
		self.fields['email'].widget.attrs.update({
			'class': 'form-control neu-input-field',
			'placeholder': 'Email Address'
		})

		# Birthday field styling
		self.fields['birthday'].widget = forms.DateInput(attrs={
			'type': 'date',
			'class': 'form-control neu-input-field'
		})


	def clean_profile_image(self):
		image = self.cleaned_data.get("profile_image")

		if image:
			if image.size > 5 * 1024 * 1024:
				raise forms.ValidationError("Image must be smaller than 5MB.")

			valid_ext = ['jpg', 'jpeg', 'png']
			ext = image.name.split('.')[-1].lower()

			if ext not in valid_ext:
				raise forms.ValidationError("Only JPG and PNG files are allowed.")

		return image


class SignUpForm(UserCreationForm):
	email = forms.EmailField(
		label="", 
		widget=forms.TextInput(attrs={
			'class':'form-control neu-input-field', 
			'placeholder':'Email Address'
		})
	)
	first_name = forms.CharField(
		label="", 
		max_length=100, 
		widget=forms.TextInput(attrs={
			'class':'form-control neu-input-field', 
			'placeholder':'First Name'
		})
	)
	last_name = forms.CharField(
		label="", 
		max_length=100, 
		widget=forms.TextInput(attrs={
			'class':'form-control neu-input-field', 
			'placeholder':'Last Name'
		})
	)

	GENDER_CHOICES = [
		('Male', 'Male'),
		('Female', 'Female'),
		('Other', 'Other'),
	]
	gender = forms.ChoiceField(
		label="Gender", 
		required=True, 
		widget=forms.RadioSelect(attrs={'class': 'form-check-input'}), 
		choices=GENDER_CHOICES
	)

	term_of_service_and_privacy = forms.BooleanField(
		required=True,
		label="I have read Terms and Privacy",
		error_messages={'required': 'You must agree to the terms of service and privacy policy.'}
	)

	subscribe_news = forms.BooleanField(
		required=False,
		label="Click here to receive our latest news",
		widget=forms.CheckboxInput()
	)
	
	
	class Meta:
		model = get_user_model() 
		fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'gender', 'birthday', 'term_of_service_and_privacy', 'subscribe_news')

	def __init__(self, *args, **kwargs):
		super(SignUpForm, self).__init__(*args, **kwargs)
		
		# Email field styling
		self.fields['email'].widget.attrs.update({
			'class': 'form-control neu-input-field',
			'placeholder': 'Email Address'
		})
		self.fields['email'].label = ''
		self.fields['email'].help_text = '<span class="form-text text-muted"><small>Required. Enter a valid email address.</small></span>'

		# Password fields styling
		self.fields['password1'].widget.attrs.update({
			'class': 'form-control neu-input-field',
			'placeholder': 'Password'
		})
		self.fields['password1'].label = ''
		
		self.fields['password2'].widget.attrs.update({
			'class': 'form-control neu-input-field',
			'placeholder': 'Confirm Password'
		})
		self.fields['password2'].label = ''

		# Birthday field styling
		self.fields['birthday'].widget = forms.DateInput(attrs={
			'type': 'date',
			'class': 'form-control neu-input-field'
		})

class OTPForm(forms.Form):
	otp = forms.CharField(
		label="Enter OTP",
		max_length=6,
		widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '6-digit code'})
	)


class PhoneCaptchaForm(forms.Form):
	captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

class CommentForm(forms.ModelForm):
	class Meta:
		model = Comment
		fields = ['body']
		widgets = {
		'body': forms.Textarea(attrs={
			'class': 'comment-textarea',
			'placeholder': 'Share your thoughts on this product ...',
			'rows': 5
			})
		}
		labels = {
		'body':'Your Comment'
		}


class ForgotPasswordForm(forms.Form):
	email = forms.EmailField(
		widget=forms.EmailInput(attrs={
			'placeholder': 'Enter your email',
			'class': 'form-control'
		})
	)

class ResetPasswordForm(forms.Form):
	otp = forms.CharField(
		max_length=6,
		widget=forms.TextInput(attrs={
			'placeholder': 'Enter 6-digit OTP',
			'class': 'form-control'
		})
	)
	new_password = forms.CharField(
		widget=forms.PasswordInput(attrs={
			'placeholder': 'New password',
			'class': 'form-control'
		})
	)
	confirm_password = forms.CharField(
		widget=forms.PasswordInput(attrs={
			'placeholder': 'Confirm new password',
			'class': 'form-control'
		})
	)
	
	def clean(self):
		cleaned_data = super().clean()
		password = cleaned_data.get('new_password')
		confirm = cleaned_data.get('confirm_password')
		
		if password and confirm and password != confirm:
			raise forms.ValidationError("Passwords don't match")
		
		return cleaned_data


class NewsletterSubscriptionForm(forms.ModelForm):
	class Meta:
		model = NewsletterSubscriber
		fields = ['email']
		widgets = {
			'email': forms.EmailInput(attrs={
				'class': 'form-control bg-transparent border-light text-white',
				'placeholder': 'Your email',
				'required': True
			})
		}