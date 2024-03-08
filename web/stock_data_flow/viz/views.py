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

    # 종료 날짜는 오늘로 설정
    end_date = datetime.today()

    # 오늘까지의 해당 주식의 전체 데이터셋 검색
    full_dataset_query = DailyStockPrice.objects.filter(
        stock_code=stock_code, 
        date_column__lte=end_date
    ).order_by('date_column')

    # 데이터셋이 존재하지 않는 경우 에러 반환
    if not full_dataset_query.exists():
        return JsonResponse({"error": "No data found for the specified stock code"}, status=404)

    # 데이터를 리스트로 변환
    full_data = list(full_dataset_query.values('date_column', 'closing_price'))
    df_full = pd.DataFrame(full_data)

    # 전체 데이터셋에 대해 이동 평균 계산
    moving_average_data = {}
    for ma in moving_averages:
        period = int(ma)
        df_full[f'ma_{period}'] = df_full['closing_price'].rolling(window=period, min_periods=1).mean()

    # 선택된 범위에 대한 시작 날짜 결정
    if selected_range == '1m':
        range_start_date = end_date - relativedelta(months=1)
    elif selected_range == '3m':
        range_start_date = end_date - relativedelta(months=3)
    elif selected_range == '6m':
        range_start_date = end_date - relativedelta(months=6)
    elif selected_range == '1y':
        range_start_date = end_date - relativedelta(years=1)
    elif selected_range == '2y':
        range_start_date = end_date - relativedelta(years=2)
    elif selected_range == '3y':
        range_start_date = end_date - relativedelta(years=3)
    else:  # default to 1 month
        range_start_date = end_date - relativedelta(months=1)

    # 선택된 범위에 따라 데이터프레임 필터링
    df = df_full[(df_full['date_column'] >= range_start_date.date()) & (df_full['date_column'] <= end_date.date())]

    # 각 기간에 대한 이동 평균 데이터를 응답에 추가
    for ma in moving_averages:
        period = int(ma)
        moving_average_data[f'ma_{period}'] = df[f'ma_{period}'].tolist()

    # 요청된 날짜 범위에 포함된 데이터만을 JSON 형태로 변환하여 반환
    response_data = {
        'date_column': df['date_column'].tolist(),
        'closing_price': df['closing_price'].tolist(),
        'moving_averages': moving_average_data,
    }

    return JsonResponse(response_data)
