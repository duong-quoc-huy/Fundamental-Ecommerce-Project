from django.shortcuts import render, get_object_or_404, redirect
from .cart import Cart
from store.models import Product, ProductVariant, ProductImage, CartItem
from django.http import JsonResponse
from decimal import Decimal

# Create your views here.
def cart_summary(request):
	cart = Cart(request)
	cart_products = cart.get_prods()
	quantities = cart.get_quantities()
	subtotal = cart.get_total()
	tax = subtotal * Decimal('0.1')
	total = subtotal + tax
	
	return render(request, "cart_summary.html", {
		'cart_products': cart_products,
		'quantities': quantities,
		'subtotal': subtotal,
		'tax': tax,
		'total': total
	})

	

def cart_add(request):
	cart = Cart(request)
	if request.POST.get('action') == 'post':
		product_id = int(request.POST.get('product_id'))
		quantity = int(request.POST.get('quantity', 1))
		product = get_object_or_404(Product, id=product_id)

		# Validate quantity
		if quantity < 1 or quantity > product.stock:
			return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)

		if request.user.is_authenticated:
			# Save to database for logged-in user
			item, created = CartItem.objects.get_or_create(
				user=request.user, 
				product=product
			)
			if created:
				item.quantity = quantity
			else:
				item.quantity += quantity  
			item.save()
		else:
			# Save to session for guest users
			cart.add(product=product, quantity=quantity)

		cart_quantity = cart.__len__()
		return JsonResponse({'success': True, 'qty': cart_quantity})

	return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)



def cart_delete(request):
	cart = Cart(request)
	if request.POST.get('action') == 'post':
		product_id = int(request.POST.get('product_id'))
		success = cart.delete(product_id)
		cart_quantity = cart.__len__()
		subtotal = cart.get_total()
		tax = subtotal * Decimal('0.1')
		total = subtotal + tax
		return JsonResponse({
			'success': success,
			'cart_quantity': cart_quantity,
			'subtotal': str(subtotal),
			'tax': str(tax),
			'total': str(total)
		})
	return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def cart_update(request):
	cart = Cart(request)
	if request.POST.get('action') == 'post':
		product_id = int(request.POST.get('product_id'))
		quantity = int(request.POST.get('quantity'))
		
		# Validate quantity
		product = get_object_or_404(Product, id=product_id)
		if quantity < 1 or quantity > product.stock:
			return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
		
		# Update cart
		success = cart.update(product_id, quantity)
		
		# Calculate new totals
		subtotal = cart.get_total()
		tax = subtotal * Decimal('0.1')
		total = subtotal + tax
		
		return JsonResponse({
			'success': success,
			'subtotal': str(subtotal),
			'tax': str(tax),
			'total': str(total)
		})
	
	return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)