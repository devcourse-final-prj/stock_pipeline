from django.shortcuts import render


def calc_view(request):
    return render(request, 'viz/calc.html')

def graph_view(request):
    return render(request, 'viz/graph.html')