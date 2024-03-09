from django.shortcuts import render


def ml_view(request):
    return render(request, 'superset/ml.html')

def treemap_view(request):
    return render(request, 'superset/treemap.html')