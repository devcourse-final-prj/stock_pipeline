from django.shortcuts import render
from .models import DailyStockPrice
from django.http import JsonResponse
import pandas as pd


def calc_view(request):
    return render(request, 'viz/calc.html')


def graph_view(request):
    return render(request, 'viz/graph.html')


def get_all_sectors_and_stocks(request):
    # 모든 섹터와 종목 가져오기
    sectors = DailyStockPrice.objects.values_list('sector_name', flat=True).distinct()
    stocks = DailyStockPrice.objects.values('stock_code', 'kr_stock_name').distinct()
    return JsonResponse({'sectors': list(sectors), 'stocks': list(stocks)})


def get_stocks_by_sector(request):
    # 선택한 섹터의 종목들 가져오기
    sector_name = request.GET.get('sector')
    stocks = DailyStockPrice.objects.filter(sector_name=sector_name).values('stock_code', 'kr_stock_name').distinct()
    return JsonResponse(list(stocks), safe=False)


def get_stock_data(request):
    # 클라이언트로부터 받은 종목 코드와 이동평균 기간
    stock_code = request.GET.get('stock_code', '')
    moving_averages = request.GET.getlist('moving_averages[]', [])  # 이동평균 기간이 여러 개일 수 있으므로 리스트로 받음

    # 해당 종목의 데이터 조회
    queryset = DailyStockPrice.objects.filter(stock_code=stock_code).order_by('date_column')
    data = list(queryset.values('date_column', 'closing_price'))

    # DataFrame으로 변환
    df = pd.DataFrame(data)

    # 이동평균선 데이터 계산
    moving_average_data = {}
    for ma in moving_averages:
        period = int(ma)
        df[f'ma_{period}'] = df['closing_price'].rolling(window=period).mean()

        # NaN 값을 처리
        df[f'ma_{period}'].fillna(0, inplace=True) 

        # 이동평균선 데이터를 딕셔너리 형태로 저장
        moving_average_data[f'ma_{period}'] = df[f'ma_{period}'].tolist()

    # 최종 데이터를 JSON 형태로 변환하여 반환
    response_data = {
        'date_column': df['date_column'].tolist(),
        'closing_price': df['closing_price'].tolist(),
        'moving_averages': moving_average_data,
    }

    return JsonResponse(response_data)
