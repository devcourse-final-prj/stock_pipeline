from django.urls import path
from .views import get_all_sectors_and_stocks
from .views import get_stocks_by_sector
from .views import get_stock_data
from . import views

urlpatterns = [
    path('get-all-sectors-and-stocks/', get_all_sectors_and_stocks, name='get_all_sectors_and_stocks'),
    path('get-stocks-by-sector/', get_stocks_by_sector, name='get_stocks_by_sector'),
    path('get-stock-data/', get_stock_data, name='get_stock_data'),
]
