from .cart import Cart

#Create context processors so cart will work on all pages
def cart(request):
	return {'cart': Cart(request)}

