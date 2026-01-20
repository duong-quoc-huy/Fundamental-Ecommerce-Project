from django.contrib import admin
from .models import ShippingAddress, OrderItem, Order, Coupon, CouponUsage


# Register your models here.
admin.site.register(ShippingAddress)
admin.site.register(OrderItem)
admin.site.register(Order)
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
	list_display = [
		'code', 
		'discount_type', 
		'discount_value', 
		'current_uses',
		'max_uses',
		'valid_from', 
		'valid_until', 
		'is_active',
		'min_order_value'
	]
	list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until']
	search_fields = ['code', 'description']
	readonly_fields = ['current_uses', 'created_at', 'updated_at']
	
	fieldsets = (
		('Basic Information', {
			'fields': ('code', 'description', 'is_active')
		}),
		('Discount Settings', {
			'fields': ('discount_type', 'discount_value', 'max_discount', 'min_order_value')
		}),
		('Usage Limits', {
			'fields': ('max_uses', 'max_uses_per_user', 'current_uses')
		}),
		('Validity Period', {
			'fields': ('valid_from', 'valid_until')
		}),
		('Metadata', {
			'fields': ('created_at', 'updated_at'),
			'classes': ('collapse',)
		}),
	)
	
	def save_model(self, request, obj, form, change):
		# Auto-uppercase coupon codes
		obj.code = obj.code.upper()
		super().save_model(request, obj, form, change)


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
	list_display = ['coupon', 'user', 'order', 'discount_amount', 'used_at']
	list_filter = ['coupon', 'used_at']
	search_fields = ['coupon__code', 'user__username', 'order__order_number']
	readonly_fields = ['used_at']
	
	def has_add_permission(self, request):
		# Prevent manual creation of usage records
		return False