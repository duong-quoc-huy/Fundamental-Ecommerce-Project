from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from cart.cart import Cart, CartItem
from .models import ShippingAddress, Order, OrderItem, Coupon, CouponUsage
from store.models import Product, Address  
from django.views.decorators.http import require_POST
from .utils import VNPay, PayPalClient
from decimal import Decimal
import requests
import json
from django.http import JsonResponse

# Create your views here.
@login_required
def payment_success(request):
	return render(request, "payment/payment_success.html", {})


def get_usd_to_vnd():
	try:
		response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
		data = response.json()
		return Decimal(str(data['rates']['VND']))
	except Exception as e:
		print(f"Error fetching exchange rate: {e}")
		return Decimal("25000")


@login_required
def checkout_shipping(request):
	cart = Cart(request)
	if cart.__len__() == 0:
		return redirect('cart:cart_summary')

	# Calculate totals
	subtotal = cart.get_total()
	discount = Decimal('0.00')
	applied_coupon = None
	
	# Check for applied coupon in session
	coupon_data = request.session.get('applied_coupon')
	if coupon_data:
		try:
			applied_coupon = Coupon.objects.get(code=coupon_data['code'])
			discount = Decimal(coupon_data['discount'])
		except Coupon.DoesNotExist:
			# Coupon no longer exists, remove from session
			del request.session['applied_coupon']
			discount = Decimal('0.00')
			applied_coupon = None
	
	# Calculate final amounts
	discounted_subtotal = subtotal - discount
	tax = discounted_subtotal * Decimal('0.1')
	total = discounted_subtotal + tax

	# Get user's saved addresses
	saved_addresses = Address.objects.filter(user=request.user)

	if request.method == 'POST':
		# Get selected payment method
		payment_method = request.POST.get('payment_method', 'vnpay')
		
		# Save shipping address
		shipping = ShippingAddress.objects.create(
			user=request.user,
			shipping_full_name=request.POST['full_name'],
			shipping_email=request.POST['email'],
			shipping_phone=request.POST.get('phone', ''),
			shipping_address1=request.POST['address1'],
			shipping_address2=request.POST.get('address2', ''),
			shipping_city=request.POST['city'],
			shipping_state_province=request.POST.get('state', ''),
			shipping_zipcode=request.POST['zipcode'],
			shipping_country=request.POST['country'],
		)

		# Create order with coupon
		order = Order.objects.create(
			user=request.user,
			shipping_address=shipping,
			subtotal=subtotal,
			discount_amount=discount,
			coupon=applied_coupon,
			tax=tax,
			total=total,
			status='pending',
			payment_method=payment_method
		)

		for item in cart.get_prods():
			quantity = getattr(item, 'cart_quantity', 1)
			OrderItem.objects.create(
				order=order,
				product=item,
				quantity=quantity,
				price=item.sale_price if item.is_sale else item.price
			)

		# If coupon was used, increment usage count
		if applied_coupon:
			applied_coupon.current_uses += 1
			applied_coupon.save()
			
			# Create usage record
			CouponUsage.objects.create(
				coupon=applied_coupon,
				user=request.user,
				order=order,
				discount_amount=discount
			)

		# Save to session
		request.session['current_order_id'] = str(order.order_number)
		
		# Clear coupon from session
		if 'applied_coupon' in request.session:
			del request.session['applied_coupon']

		# Route to appropriate payment gateway
		if payment_method == 'paypal':
			return redirect('payment:paypal_create')
		else:  # vnpay
			vnp = VNPay()
			total_usd = total
			EXCHANGE_RATE = get_usd_to_vnd()
			total_vnd = (total_usd * EXCHANGE_RATE).quantize(Decimal("1"))
			amount_vnd = int(total_vnd)

			payment_url = vnp.build_payment_url(
				order_id=str(order.order_number),
				amount=amount_vnd,
				order_info=f"Thanh toan don hang {order.order_number}",
				ip_addr=request.META.get('REMOTE_ADDR')
			)

			return redirect(payment_url)

	# GET request → Show form
	return render(request, 'payment/checkout_shipping.html', {
		"subtotal": subtotal,
		"discount": discount,
		"discounted_subtotal": discounted_subtotal,
		"tax": tax,
		"total": total,
		"saved_addresses": saved_addresses,
		"applied_coupon": applied_coupon
	})


@login_required
def paypal_create_order(request):
	"""Create PayPal order and redirect to PayPal"""
	order_number = request.session.get('current_order_id')
	
	if not order_number:
		messages.error(request, "No order found. Please try again.")
		return redirect('cart_summary')
	
	try:
		order = Order.objects.get(order_number=order_number)
	except Order.DoesNotExist:
		messages.error(request, "Order not found.")
		return redirect('cart_summary')
	
	# Create PayPal order
	try:
		paypal = PayPalClient()
		
		# Build return URLs
		return_url = request.build_absolute_uri(reverse('payment:paypal_return'))
		cancel_url = request.build_absolute_uri(reverse('payment:paypal_cancel'))
		
		paypal_order = paypal.create_order(
			amount=order.total,
			currency='USD',
			order_number=str(order.order_number),
			return_url=return_url,
			cancel_url=cancel_url
		)
		
		# Save PayPal order ID for later reference
		order.payment_transaction_id = paypal_order['id']
		order.save()
		
		# Get approval URL and redirect user to PayPal
		for link in paypal_order['links']:
			if link['rel'] == 'approve':
				return redirect(link['href'])
		
		messages.error(request, "Failed to get PayPal approval URL.")
		return redirect('cart_summary')
		
	except Exception as e:
		print(f"PayPal Error: {e}")
		messages.error(request, f"PayPal error: {str(e)}")
		return redirect('cart_summary')


@login_required
def paypal_return(request):
	"""Handle PayPal return after user approves payment"""
	paypal_order_id = request.GET.get('token')
	
	if not paypal_order_id:
		messages.error(request, "Invalid PayPal response.")
		return redirect('cart_summary')
	
	try:
		# Find our order
		order = Order.objects.get(payment_transaction_id=paypal_order_id)
		
		# Prevent double processing
		if order.status == "paid":
			return render(request, "payment/paypal_return.html", {
				"order": order,
				"message": "Payment already processed!",
				"success": True
			})
		
		# Capture the payment
		paypal = PayPalClient()
		capture_result = paypal.capture_order(paypal_order_id)
		
		# Check capture status
		if capture_result['status'] == 'COMPLETED':
			# Mark order as paid
			order.status = "paid"
			order.paid_at = timezone.now()
			
			# Get capture ID for reference
			if 'purchase_units' in capture_result:
				capture_id = capture_result['purchase_units'][0]['payments']['captures'][0]['id']
				order.payment_transaction_id = capture_id
			
			order.save()
			
			# Deduct stock
			for order_item in order.items.all():
				product = order_item.product
				requested_qty = order_item.quantity
				
				if product.stock >= requested_qty:
					product.stock -= requested_qty
					product.save(update_fields=['stock'])
				else:
					print(f"WARNING: Not enough stock for {product.name}. Requested: {requested_qty}, Available: {product.stock}")
			
			# Clear cart
			cart = Cart(request)
			if request.user.is_authenticated:
				CartItem.objects.filter(user=request.user).delete()
			else:
				if "cart" in request.session:
					del request.session["cart"]
				if "session_key" in request.session:
					request.session["session_key"] = {}
			
			request.session.modified = True
			
			if "current_order_id" in request.session:
				del request.session["current_order_id"]
			
			return render(request, "payment/paypal_return.html", {
				"order": order,
				"message": "Payment successful! Thank you for your purchase.",
				"success": True
			})
		else:
			order.status = "canceled"
			order.save()
			return render(request, "payment/paypal_return.html", {
				"order": order,
				"message": f"Payment failed. Status: {capture_result['status']}",
				"success": False
			})
			
	except Order.DoesNotExist:
		messages.error(request, "Order not found.")
		return redirect('cart_summary')
	except Exception as e:
		print(f"PayPal Capture Error: {e}")
		messages.error(request, f"Payment processing error: {str(e)}")
		return redirect('cart_summary')


@login_required
def paypal_cancel(request):
	"""Handle PayPal cancellation"""
	order_number = request.session.get('current_order_id')
	
	if order_number:
		try:
			order = Order.objects.get(order_number=order_number)
			order.status = "canceled"
			order.save()
		except Order.DoesNotExist:
			pass
	
	messages.warning(request, "Payment was cancelled.")
	return redirect('cart_summary')


def vnpay_return(request):
	vnp = VNPay()
	params = request.GET.dict()

	# 1. Validate signature
	if not vnp.validate_return(params):
		return render(request, "payment/vnpay_return.html", {
			"success": False,
			"message": "Chữ ký không hợp lệ (Invalid Signature)"
		})

	# 2. Read basic fields
	order_number = params.get("vnp_TxnRef")
	response_code = params.get("vnp_ResponseCode")

	try:
		order = Order.objects.get(order_number=order_number)
	except Order.DoesNotExist:
		return render(request, "payment/vnpay_return.html", {
			"success": False,
			"message": "Đơn hàng không tồn tại!"
		})

	# 3. Handle payment result
	if response_code == "00":
		# --- ONLY PROCESS ONCE: Prevent double deduction ---
		if order.status == "paid":
			# Already processed → just show success (idempotent)
			return render(request, "payment/vnpay_return.html", {
				"order": order,
				"message": "Thanh toán đã được xử lý trước đó!",
				"success": True
			})

		# Mark order as paid
		order.status = "paid"
		order.paid_at = timezone.now()
		order.payment_transaction_id = params.get("vnp_TransactionNo")
		order.save()

		# --- 1. DEDUCT STOCK SAFELY ---
		for order_item in order.items.all():
			product = order_item.product
			requested_qty = order_item.quantity

			if product.stock >= requested_qty:
				product.stock -= requested_qty
				product.save(update_fields=['stock'])
			else:
				print(f"WARNING: Not enough stock for {product.name}. Requested: {requested_qty}, Available: {product.stock}")

		# --- 2. CLEAR USER'S CART COMPLETELY ---
		cart = Cart(request)

		if request.user.is_authenticated:
			CartItem.objects.filter(user=request.user).delete()
		else:
			# Delete from session
			if "cart" in request.session:
				del request.session["cart"]
			# Also clear the custom session_key if exists
			if "session_key" in request.session:
				request.session["session_key"] = {}
		
		request.session.modified = True

		if "current_order_id" in request.session:
			del request.session["current_order_id"]

		message = "Thanh toán thành công! Cảm ơn bạn đã mua hàng."
		success = True

	else:
		order.status = "canceled"
		order.save()
		message = f"Thanh toán thất bại (Mã lỗi: {response_code})"
		success = False

	return render(request, "payment/vnpay_return.html", {
		"order": order,
		"message": message,
		"success": success
	})


@login_required
def payment_history(request):
	# Get all orders for the current user, ordered by most recent first
	orders = Order.objects.filter(user=request.user).order_by('-created_at')
	
	return render(request, 'payment/payment_history.html', {'orders': orders})

@login_required
@require_POST
def apply_coupon(request):
	"""AJAX endpoint to validate and apply coupon"""
	try:
		data = json.loads(request.body)
		coupon_code = data.get('coupon_code', '').strip().upper()
		subtotal = Decimal(str(data.get('subtotal', 0)))
		
		if not coupon_code:
			return JsonResponse({
				'success': False,
				'message': 'Please enter a coupon code.'
			})
		
		# Find coupon
		try:
			coupon = Coupon.objects.get(code__iexact=coupon_code)
		except Coupon.DoesNotExist:
			return JsonResponse({
				'success': False,
				'message': 'Invalid coupon code.'
			})
		
		# Check if coupon is valid
		is_valid, message = coupon.is_valid()
		if not is_valid:
			return JsonResponse({
				'success': False,
				'message': message
			})
		
		# Check if user can use this coupon
		can_use, message = coupon.can_be_used_by_user(request.user)
		if not can_use:
			return JsonResponse({
				'success': False,
				'message': message
			})
		
		# Check minimum order value
		if subtotal < coupon.min_order_value:
			return JsonResponse({
				'success': False,
				'message': f'Minimum order value of ${coupon.min_order_value} required.'
			})
		
		# Calculate discount
		discount = coupon.calculate_discount(subtotal)
		new_subtotal = subtotal - discount
		tax = new_subtotal * Decimal('0.1')
		new_total = new_subtotal + tax
		
		# Store coupon in session
		request.session['applied_coupon'] = {
			'code': coupon.code,
			'discount': str(discount),
			'discount_type': coupon.discount_type,
			'discount_value': str(coupon.discount_value)
		}
		
		return JsonResponse({
			'success': True,
			'message': f'Coupon "{coupon.code}" applied successfully!',
			'discount': float(discount),
			'new_subtotal': float(new_subtotal),
			'new_tax': float(tax),
			'new_total': float(new_total),
			'coupon_description': coupon.description
		})
		
	except Exception as e:
		return JsonResponse({
			'success': False,
			'message': f'Error applying coupon: {str(e)}'
		})


@login_required
@require_POST
def remove_coupon(request):
	"""AJAX endpoint to remove applied coupon"""
	try:
		# Get original subtotal from cart
		cart = Cart(request)
		subtotal = cart.get_total()
		tax = subtotal * Decimal('0.1')
		total = subtotal + tax
		
		# Remove coupon from session
		if 'applied_coupon' in request.session:
			del request.session['applied_coupon']
		
		return JsonResponse({
			'success': True,
			'message': 'Coupon removed.',
			'subtotal': float(subtotal),
			'tax': float(tax),
			'total': float(total)
		})
		
	except Exception as e:
		return JsonResponse({
			'success': False,
			'message': f'Error removing coupon: {str(e)}'
		})