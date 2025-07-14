
from django.shortcuts import render

def debug_cliente_autocomplete(request):
    return render(request, 'debug_autocomplete_cliente.html')
