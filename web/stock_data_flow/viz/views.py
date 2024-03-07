from django.shortcuts import render
from .models import DailyStockPrice
from django.http import JsonResponse
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta


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
    selected_range = request.GET.get('range', '1y')

    # range에 따른 시작 날짜 계산
    end_date = datetime.today()
    if selected_range == '1m':
        start_date = end_date - relativedelta(months=1)
    if selected_range == '3m':
        start_date = end_date - relativedelta(months=3)
    elif selected_range == '6m':
        start_date = end_date - relativedelta(months=6)
    elif selected_range == '1y':
        start_date = end_date - relativedelta(years=1)
    elif selected_range == '2y':
        start_date = end_date - relativedelta(years=2)
    elif selected_range == '3y':
        start_date = end_date - relativedelta(years=3)
    else:
        start_date = end_date - relativedelta(months=1)

    # 해당 종목의 데이터 조회
    queryset = DailyStockPrice.objects.filter(stock_code=stock_code, date_column__range=[start_date, end_date]).order_by('date_column')
    if not queryset.exists():
        return JsonResponse({"error": "No data found for the specified stock code and date range"}, status=404)

    data = list(queryset.values('date_column', 'closing_price'))

    # DataFrame으로 변환
    df = pd.DataFrame(data)

    # 이동평균선 데이터 계산
    moving_average_data = {}
    for ma in moving_averages:
        period = int(ma)
        df[f'ma_{period}'] = df['closing_price'].rolling(window=period, min_periods=1).mean()

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
