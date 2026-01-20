import hmac
import hashlib
import time
import requests
from urllib.parse import quote_plus
from django.conf import settings

class VNPay:
	def __init__(self):
		self.vnp_TmnCode = settings.VNPAY_TMN_CODE
		self.vnp_HashSecret = settings.VNPAY_HASH_SECRET
		self.vnp_PayUrl = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
		self.vnp_ReturnUrl = settings.VNPAY_RETURN_URL

	# -------------------------
	# BUILD PAYMENT URL
	# -------------------------
	def build_payment_url(self, order_id, amount, order_info, ip_addr):

		params = {
			"vnp_Version": "2.1.0",
			"vnp_Command": "pay",
			"vnp_TmnCode": self.vnp_TmnCode,
			"vnp_Amount": int(amount * 100),
			"vnp_CurrCode": "VND",
			"vnp_TxnRef": order_id,
			"vnp_OrderInfo": order_info,
			"vnp_OrderType": "billpayment",
			"vnp_Locale": "vn",
			"vnp_ReturnUrl": self.vnp_ReturnUrl,
			"vnp_IpAddr": ip_addr,
			"vnp_CreateDate": time.strftime("%Y%m%d%H%M%S"),
		}

		# 1) Sort all params alphabetically
		sorted_params = sorted(params.items())

		# 2) Build hash data string EXACTLY as VNPay requires
		hash_data = "&".join(f"{k}={quote_plus(str(v))}" for k, v in sorted_params)

		# 3) Compute HMAC SHA512
		secure_hash = hmac.new(
			self.vnp_HashSecret.encode("utf-8"),
			hash_data.encode("utf-8"),
			hashlib.sha512
		).hexdigest()

		# 4) Build final query string
		query = "&".join(f"{k}={quote_plus(str(v))}" for k, v in sorted_params)
		query += f"&vnp_SecureHash={secure_hash}"

		return f"{self.vnp_PayUrl}?{query}"

	def validate_return(self, data):
		vnp_securehash = data.get("vnp_SecureHash")

		data = {k: v for k, v in data.items() if k not in ("vnp_SecureHash", "vnp_SecureHashType")}
		sorted_data = sorted(data.items())
		hash_data = "&".join(f"{k}={quote_plus(str(v))}" for k, v in sorted_data)

		signed = hmac.new(
			self.vnp_HashSecret.encode("utf-8"),
			hash_data.encode("utf-8"),
			hashlib.sha512
		).hexdigest()

		return signed == vnp_securehash

class PayPalClient:
	"""
	PayPal REST API helper for creating and capturing orders
	"""
	def __init__(self):
		self.client_id = settings.PAYPAL_CLIENT_ID
		self.client_secret = settings.PAYPAL_CLIENT_SECRET
		# Use sandbox for testing, live for production
		self.base_url = settings.PAYPAL_MODE == 'live' and \
			"https://api-m.paypal.com" or "https://api-m.sandbox.paypal.com"
		self.access_token = None

	def get_access_token(self):
		"""Get OAuth 2.0 access token from PayPal"""
		url = f"{self.base_url}/v1/oauth2/token"
		headers = {
			"Accept": "application/json",
			"Accept-Language": "en_US",
		}
		data = {"grant_type": "client_credentials"}
		
		response = requests.post(
			url,
			headers=headers,
			data=data,
			auth=(self.client_id, self.client_secret)
		)
		
		if response.status_code == 200:
			self.access_token = response.json()['access_token']
			return self.access_token
		else:
			raise Exception(f"Failed to get access token: {response.text}")

	def create_order(self, amount, currency='USD', order_number='', return_url='', cancel_url=''):
		"""
		Create a PayPal order
		
		Args:
			amount: Decimal amount to charge
			currency: Currency code (USD, EUR, etc.)
			order_number: Your internal order reference
			return_url: URL to redirect after successful payment
			cancel_url: URL to redirect if payment is cancelled
		"""
		if not self.access_token:
			self.get_access_token()

		url = f"{self.base_url}/v2/checkout/orders"
		headers = {
			"Content-Type": "application/json",
			"Authorization": f"Bearer {self.access_token}"
		}
		
		# Convert Decimal to string with 2 decimal places
		amount_str = f"{amount:.2f}"
		
		payload = {
			"intent": "CAPTURE",
			"purchase_units": [{
				"reference_id": order_number,
				"amount": {
					"currency_code": currency,
					"value": amount_str
				},
				"description": f"Order {order_number}"
			}],
			"application_context": {
				"return_url": return_url,
				"cancel_url": cancel_url,
				"brand_name": settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else "Your Store",
				"landing_page": "BILLING",
				"user_action": "PAY_NOW"
			}
		}

		response = requests.post(url, json=payload, headers=headers)
		
		if response.status_code == 201:
			return response.json()
		else:
			raise Exception(f"Failed to create order: {response.text}")

	def capture_order(self, order_id):
		"""
		Capture payment for an approved order
		
		Args:
			order_id: PayPal order ID to capture
		"""
		if not self.access_token:
			self.get_access_token()

		url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"
		headers = {
			"Content-Type": "application/json",
			"Authorization": f"Bearer {self.access_token}"
		}

		response = requests.post(url, headers=headers)
		
		if response.status_code == 201:
			return response.json()
		else:
			raise Exception(f"Failed to capture order: {response.text}")

	def get_order_details(self, order_id):
		"""Get details of a PayPal order"""
		if not self.access_token:
			self.get_access_token()

		url = f"{self.base_url}/v2/checkout/orders/{order_id}"
		headers = {
			"Authorization": f"Bearer {self.access_token}"
		}

		response = requests.get(url, headers=headers)
		
		if response.status_code == 200:
			return response.json()
		else:
			raise Exception(f"Failed to get order details: {response.text}")