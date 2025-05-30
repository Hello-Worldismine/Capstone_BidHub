# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile

def index(request):
    return render(request, 'main/pages/index.html')

def login_view(request):
    return render(request, 'main/pages/login.html')

def join(request):
    return render(request, 'main/pages/join.html')

def tender(request):
    return render(request, 'main/pages/tender.html')

def auto_bid(request):
    return render(request, 'main/pages/auto_bid.html')

def mypage(request):
    return render(request, 'main/pages/mypage.html')

def bidform(request):
    return render(request, 'main/pages/bidform.html')

def bid_submit(request):
    if request.method == 'POST':
        # 폼 처리 로직
        print(request.POST)  # 임시: 콘솔에 데이터 출력
        return redirect('bidform')  # 제출 후 다시 폼 페이지로 이동
    return redirect('bidform')  # GET으로 접근하면 다시 폼 페이지로

def bid_history(request):
    return render(request, 'main/pages/bid_history.html') 

def favlist(request):
    return render(request, 'main/pages/favlist.html') 

def fsearch(request):
    return render(request, 'main/pages/fsearch.html') 

def csearch(request):
    return render(request, 'main/pages/csearch.html') 

def register(request):
    if request.method == "POST":
        # 회원가입 처리 로직 (ex: 유효성 검사, DB 저장)
        return redirect('login')  # 회원가입 후 이동할 페이지
    return HttpResponse("Invalid access")

@login_required
def charge(request):
    if request.method == 'POST':
        amount = int(request.POST.get('amount'))
        profile = request.user.profile
        profile.balance += amount
        profile.save()
        return redirect('charge')

    return render(request, 'main/pages/charge.html')