# mailchimp_service.py
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
from django.conf import settings
import hashlib

class MailchimpService:
	def __init__(self):
		self.client = MailchimpMarketing.Client()
		self.client.set_config({
			"api_key": settings.MAILCHIMP_API_KEY,
			"server": settings.MAILCHIMP_SERVER_PREFIX
		})
		self.audience_id = settings.MAILCHIMP_AUDIENCE_ID
	
	def subscribe_user(self, email, first_name='', last_name=''):
		"""Add or update a subscriber"""
		try:
			member_info = {
				"email_address": email,
				"status": "subscribed",
				"merge_fields": {
					"FNAME": first_name,
					"LNAME": last_name
				}
			}
			
			response = self.client.lists.add_list_member(
				self.audience_id,
				member_info
			)
			return True, response
		except ApiClientError as error:
			return False, error.text
	
	def unsubscribe_user(self, email):
		"""Unsubscribe a user"""
		try:
			subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
			response = self.client.lists.update_list_member(
				self.audience_id,
				subscriber_hash,
				{"status": "unsubscribed"}
			)
			return True, response
		except ApiClientError as error:
			return False, error.text