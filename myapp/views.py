from django.shortcuts import render, redirect
from myapp import stock_api
from django.conf import settings
from myapp.models import Stock, UserProfile
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import logout
import wikipedia as wiki
from django.core.files.storage import FileSystemStorage
import pathlib



# View for the home page - a list of 20 of the most active stocks
def index(request):
    # Query the stock table, filter for top ranked stocks and order by their rank.
    data = Stock.objects.filter(top_rank__isnull=False).order_by('top_rank')
    return render(request, 'index.html', {'page_title': 'Main', 'data': data})


# View for the single stock page
# symbol is the requested stock's symbol ('AAPL' for Apple)
def single_stock(request, symbol):
    data = stock_api.get_stock_info(symbol)
    return render(request, 'single_stock.html', {'page_title': 'Stock Page - %s' % symbol, 'data': data})


def register(request):
	# If post -> register the user and redirect to main page
	if request.method == 'POST':
		firstname = request.POST.get('firstname')
		lastname = request.POST.get('lastname')
		email = request.POST.get('email')
		password = request.POST.get('password')
		if User.objects.filter(username=email):
			error_message = f'user {email} already exist!'
			return render(request, 'register.html', {'page_title': 'Register', 'message': error_message})
		newuser = User.objects.create_user(username=email, email=email, password=password)
		newuser.first_name = firstname
		newuser.last_name = lastname
		newuser.save()
		if request.FILES and request.POST.get('avatar') and request.FILES['avatar']:
			avatar =request.FILES['avatar']
			file_ext = pathlib.Path(avatar.name).suffix
			new_file_name = str(newuser.id) + file_ext
			user_profile = UserProfile(user=newuser, avatar=new_file_name)
			fs = FileSystemStorage()
			fs.save(new_file_name, avatar)
			user_profile.save()
		return redirect('index')
	else:
		# If not post (regular request) -> render register page
		return render(request, 'register.html', {'page_title': 'Register'})

def user_profile(request):
	if request.user.is_authenticated:
		user = request.user
		profile = UserProfile.objects.filter(user_id=user.id)
		avatar = 'default.png'
		if profile:
			avatar = profile[0].avatar
		return render(request, 'profile.html', {'page_title': 'User Profile', 'user': user, 'media_url':settings.MEDIA_URL, 'avatar': avatar})
	return render(request, 'register.html', {'page_title': 'Register'})

def edit_profile(request):
	if request.method == 'POST':
		user = request.user
		user.first_name = request.POST.get('re_firstname') or user.first_name
		user.last_name = request.POST.get('re_lastname') or user.last_name
		password = request.POST.get('re_password')
		if password:
			user.set_password(password)

		user.save()
		if request.FILES and request.POST.get('avatar') and request.FILES.get('avatar'):
			avatar =request.FILES['avatar']
			fs = FileSystemStorage()
			file_ext = pathlib.Path(avatar.name).suffix
			new_file_name = str(user.id) + file_ext
			try:
				user_profile = UserProfile.objects.get(user_id=user.id)
				fs.delete(user_profile.avatar)
				user_profile.avatar = new_file_name
				
			except Exception:
				user_profile = UserProfile(user=user, avatar=new_file_name)
			fs.save(new_file_name, avatar)
			user_profile.save()
		return redirect('index')
	else:
		# If not post (regular request) -> render register page
		return render(request, 'edit_profile.html', {'page_title': 'Edit Profile'})

def change_password(request):
	if request.method == 'POST' and request.user.is_authenticated:
		user = request.user
		password = request.POST.get('password')
		user.set_password(password)
		user.save()
		return redirect('index')
	else:
		# If not post (regular request) -> render register page
		return render(request, 'register.html', {'page_title': 'Register'})

def logout_view(request):
    logout(request)
    return redirect('index')


# API for a stock's price over time
# symbol is the requested stock's symbol ('AAPL' for Apple)
# The response is JSON data of an array composed of "snapshot" objects (date + stock info + ...), usually one per day
def single_stock_historic(request, symbol, time_range='1m'):
    data = stock_api.get_stock_historic_prices(symbol, time_range=time_range)
    return JsonResponse({'data': data})


def get_wiki_info(request, company_name):
    try:
        summary = wiki.summary(company_name, sentences=3)
        return JsonResponse({'summary': summary})
    except Exception:
        return JsonResponse({'summary': "Couldn't find information"})
