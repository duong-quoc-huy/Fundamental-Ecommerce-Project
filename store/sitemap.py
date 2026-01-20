from django.contrib.sitemaps import Sitemap
from .models import Product

class ProductSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Product.objects.all()

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f'/product/{obj.slug}/'

class StaticViewSitemap(Sitemap):
    protocol = 'https'
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['home', 'about', 'contact']  # Your static page names

    def location(self, item):
        return f'/{item}/'