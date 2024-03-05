from django.shortcuts import render
from .models import DailyStockPrice
from django.http import JsonResponse
import pandas as pd


def calc_view(request):
    return render(request, 'viz/calc.html')


def graph_view(request):
    return render(request, 'viz/graph.html')


def get_all_sectors_and_stocks(request):
    sectors = DailyStockPrice.objects.values_list('sector_name', flat=True).distinct()
    stocks = DailyStockPrice.objects.values('stock_code', 'kr_stock_name').distinct()
    return JsonResponse({'sectors': list(sectors), 'stocks': list(stocks)})


def get_stocks_by_sector(request):
    sector_name = request.GET.get('sector')
    stocks = DailyStockPrice.objects.filter(sector_name=sector_name).values('stock_code', 'kr_stock_name').distinct()
    print(sector_name)
    return JsonResponse(list(stocks), safe=False)


def moving_average(request, stock_code):
    # 모델에서 데이터 가져오기
    queryset = DailyStockPrice.objects.filter(stock_code=stock_code)
    # 데이터프레임으로 변환
    data = list(queryset.values('date_column', 'closing_price'))
    df = pd.DataFrame(data)

    # 이동평균 및 교차점 로직 적용

    # 처리된 데이터를 템플릿에 전달
    context = {
        'data': df.to_dict(orient='records'),  # 또는 필요한 다른 형태로 데이터 전달
    }
    return render(request, 'your_template.html', context)
