from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Category, Product, ProductVariant, ProductImage, Comment, Reply, NewsletterSubscriber
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'birthday', 'gender', 'is_staff')
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'birthday', 'gender', 'profile_image')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'birthday', 'gender', 'profile_image')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'birthday', 'gender', 'phone_number', 'is_staff',  'is_active')}
        ),
    )
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'category', 'is_sale']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'price', 'sale_price', 'is_sale', 'stock')
        }),
        ('Content', {
            'fields': ('description',)
        }),
        ('SEO Settings', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),  # Makes it collapsible
        }),
    )
#admin.site.register(CustomUser)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(ProductImage)
admin.site.register(Comment)
admin.site.register(Reply)
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at', 'user']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email', 'user__email']
    readonly_fields = ['subscribed_at', 'unsubscribe_token']
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions']
    
    def activate_subscriptions(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} subscription(s) activated.')
    activate_subscriptions.short_description = 'Activate selected subscriptions'
    
    def deactivate_subscriptions(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} subscription(s) deactivated.')
    deactivate_subscriptions.short_description = 'Deactivate selected subscriptions'
#admin.site.register(Order)

