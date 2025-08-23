from django.shortcuts import render
from django.views import View

class EmailConfirmEmptyView(View):
    def get(self, request):
        return render(request, "account/email_confirm_empty.html")
