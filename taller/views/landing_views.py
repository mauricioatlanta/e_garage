from django.shortcuts import render


def landing_workshop(request):
    return render(request, "public/landing_workshop.html")


def landing_salvage(request):
    return render(request, "public/landing_salvage.html")


def landing_parts(request):
    return render(request, "public/landing_parts.html")
