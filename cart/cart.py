from store.models import Product, CartItem

class Cart():
	def __init__(self, request):
		self.session = request.session
		self.request = request

		# For non-authenticated users, use session
		cart = self.session.get('session_key')

		if 'session_key' not in request.session:
			cart = self.session['session_key'] = {}

		self.cart = cart

	def add(self, product, quantity=1):
		product_id = str(product.id)

		# Logic for session-based cart
		if product_id in self.cart:
			self.cart[product_id]['quantity'] = int(self.cart[product_id].get('quantity', 0)) + quantity
		else:
			self.cart[product_id] = {
				'price': str(product.price),
				'quantity': quantity
			}

		self.session.modified = True

	def __len__(self):
		# Return total number of items
		if self.request.user.is_authenticated:
			# Count from database
			return CartItem.objects.filter(user=self.request.user).count()
		else:
			# Count from session
			return len(self.cart)

	def get_prods(self):
		if self.request.user.is_authenticated:
			# Get cart items from database for authenticated users
			cart_items = CartItem.objects.filter(user=self.request.user).select_related('product')
			
			# Return products with their quantities
			products = []
			for item in cart_items:
				product = item.product
				product.cart_quantity = item.quantity  # Add quantity to product object
				product.cart_item_id = item.id  # Add cart item id for updates/deletes
				products.append(product)
			
			return products
		else:
			# Get products from session for non-authenticated users
			product_ids = self.cart.keys()
			products = Product.objects.filter(id__in=product_ids)
			
			# Add quantity info from session
			for product in products:
				product.cart_quantity = self.cart[str(product.id)].get('quantity', 1)
			
			return products

	def get_quantities(self):
		"""Get dictionary of product quantities"""
		if self.request.user.is_authenticated:
			cart_items = CartItem.objects.filter(user=self.request.user)
			return {str(item.product.id): item.quantity for item in cart_items}
		else:
			return {pid: data.get('quantity', 1) for pid, data in self.cart.items()}

	def update(self, product_id, quantity):
		"""Update quantity of a cart item"""
		if self.request.user.is_authenticated:
			try:
				cart_item = CartItem.objects.get(user=self.request.user, product_id=product_id)
				cart_item.quantity = quantity
				cart_item.save()
				return True
			except CartItem.DoesNotExist:
				return False
		else:
			product_id = str(product_id)
			if product_id in self.cart:
				self.cart[product_id]['quantity'] = quantity
				self.session.modified = True
				return True
			return False

	def delete(self, product_id):
		"""Remove item from cart"""
		if self.request.user.is_authenticated:
			try:
				cart_item = CartItem.objects.get(user=self.request.user, product_id=product_id)
				cart_item.delete()
				return True
			except CartItem.DoesNotExist:
				return False
		else:
			product_id = str(product_id)
			if product_id in self.cart:
				del self.cart[product_id]
				self.session.modified = True
				return True
			return False

	def get_total(self):
		"""Calculate cart total"""
		if self.request.user.is_authenticated:
			cart_items = CartItem.objects.filter(user=self.request.user).select_related('product')
			total = sum(item.product.sale_price * item.quantity if item.product.is_sale 
					   else item.product.price * item.quantity 
					   for item in cart_items)
		else:
			product_ids = self.cart.keys()
			products = Product.objects.filter(id__in=product_ids)
			total = sum((product.sale_price if product.is_sale else product.price) * 
					   self.cart[str(product.id)].get('quantity', 1)
					   for product in products)
		
		return total

	def merge_to_database(self, user):
		"""Merge session cart to database when user logs in"""
		# Store session cart before it gets cleared
		session_cart_data = dict(self.cart) if self.cart else {}
		
		if not session_cart_data:
			return
		
		for product_id, data in session_cart_data.items():
			try:
				product = Product.objects.get(id=product_id)
				quantity = data.get('quantity', 1)
				
				cart_item, created = CartItem.objects.get_or_create(
					user=user,
					product=product
				)
				
				if created:
					cart_item.quantity = quantity
				else:
					cart_item.quantity += quantity
				
				cart_item.save()
				
			except Product.DoesNotExist:
				continue
		
		# Clear session cart
		self.cart.clear()
		self.session.modified = True