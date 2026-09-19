import json
import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import CarMake, CarModel
from .populate import initiate
from .restapis import analyze_review_sentiments, get_request, post_review

logger = logging.getLogger(__name__)


# Login view
@csrf_exempt
def login_user(request):
    try:
        data = json.loads(request.body)
        username = data['userName']
        password = data['password']
    except (ValueError, KeyError):
        return JsonResponse(
            {"status": 400, "message": "Bad Request"}, status=400
        )
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)


# Logout view
def logout_request(request):
    logout(request)
    data = {"userName": ""}
    return JsonResponse(data)


# Registration view
@csrf_exempt
def registration(request):
    try:
        data = json.loads(request.body)
        username = data['userName']
        password = data['password']
        first_name = data['firstName']
        last_name = data['lastName']
        email = data['email']
    except (ValueError, KeyError):
        return JsonResponse(
            {"status": 400, "message": "Bad Request"}, status=400
        )

    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email,
        )
        login(request, user)
        return JsonResponse({"userName": username, "status": "Authenticated"})
    else:
        return JsonResponse(
            {"userName": username, "error": "Already Registered"}
        )


# Get Car Models view
def get_cars(request):
    count = CarMake.objects.filter().count()
    if count == 0:
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append(
            {"CarModel": car_model.name, "CarMake": car_model.car_make.name}
        )
    return JsonResponse({"CarModels": cars})


# Get dealerships (all or by state)
def get_dealerships(request, state="All"):
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/" + state
    dealerships = get_request(endpoint)
    if dealerships is None:
        return JsonResponse(
            {"status": 502, "message": "Dealer service unavailable"}
        )
    return JsonResponse({"status": 200, "dealers": dealerships})


# Get dealer details
def get_dealer_details(request, dealer_id):
    if dealer_id:
        endpoint = "/fetchDealer/" + str(dealer_id)
        dealer = get_request(endpoint)
        if dealer is None:
            return JsonResponse(
                {"status": 502, "message": "Dealer service unavailable"}
            )
        return JsonResponse({"status": 200, "dealer": dealer})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})


# Get dealer reviews with sentiment analysis
def get_dealer_reviews(request, dealer_id):
    if dealer_id:
        endpoint = "/fetchReviews/dealer/" + str(dealer_id)
        reviews = get_request(endpoint)
        if reviews is None:
            return JsonResponse(
                {"status": 502, "message": "Review service unavailable"}
            )
        for review_detail in reviews:
            response = analyze_review_sentiments(review_detail['review'])
            review_detail['sentiment'] = response['sentiment']
        return JsonResponse({"status": 200, "reviews": reviews})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})


# Add review for a dealer
@csrf_exempt
def add_review(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": 403, "message": "Unauthorized"})
    try:
        data = json.loads(request.body)
        post_review(data)
        return JsonResponse({"status": 200})
    except Exception:
        logger.exception("Error in posting review")
        return JsonResponse(
            {"status": 401, "message": "Error in posting review"}
        )
