# places/views.py

from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Avg, Count, Q
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_http_methods

# Import your models here
from .models import Place, Souvenir, Comment

# Import the Collection models
from placeCollection.models import Collection, CollectionItem  # Added import

def format_price(price):
    """Formats the price with commas (e.g., 10000 -> 10,000)."""
    return "{:,}".format(price)

def place_detail(request, place_id):
    place = get_object_or_404(Place, pk=place_id)
    
    # Aggregate average rating
    average_rating = Comment.objects.filter(place=place).aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Fetch all souvenirs for the place
    souvenirs = Souvenir.objects.filter(place=place)
    
    # Calculate total and available souvenirs
    total_souvenirs_count = souvenirs.count()
    available_souvenirs_count = souvenirs.filter(stock__gt=0).count()

    # Format the price for each souvenir
    for souvenir in souvenirs:
        souvenir.formatted_price = format_price(souvenir.price)

    # Fetch the latest 10 comments
    comments = Comment.objects.filter(place=place).order_by('-created_at')[:10]  # Limit to recent 10 reviews

    # Get the user's collections if authenticated
    user_collections = Collection.objects.filter(user=request.user) if request.user.is_authenticated else []

    context = {
        'place': place,
        'average_rating': round(average_rating, 1),
        'souvenirs': souvenirs,
        'comments': comments,
        'user_collections': user_collections,  # Added to context
        'total_souvenirs_count': total_souvenirs_count,  # New context variable
        'available_souvenirs_count': available_souvenirs_count,  # New context variable
    }
    return render(request, 'places/place_detail.html', context)

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  # Path to your custom login template
    redirect_authenticated_user = True  # Redirect users who are already logged in

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or reverse_lazy('home')  # Replace 'home' with your desired default view name

@login_required
@csrf_exempt
def add_comment_ajax(request, place_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        place = get_object_or_404(Place, pk=place_id)
        content = request.POST.get('comment')
        rating = request.POST.get('rating')
        if content and rating:
            comment = Comment.objects.create(
                place=place,
                user=request.user,
                content=content,
                rating=int(rating),
                created_at=timezone.now()
            )
            # Update average rating
            average_rating = Comment.objects.filter(place=place).aggregate(Avg('rating'))['rating__avg'] or 0
            average_rating = round(average_rating, 1)
            # Return the rendered HTML for the new comment and updated average rating
            rendered_comment = render_to_string('places/comment_partial.html', {'comment': comment, 'user': request.user})
            return JsonResponse({
                'message': 'Your review has been submitted successfully.',
                'comment_html': rendered_comment,
                'average_rating': average_rating
            })
        else:
            return JsonResponse({'error': 'Please provide both a comment and a rating.'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

@login_required
@csrf_exempt
def edit_comment_ajax(request, comment_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        comment = get_object_or_404(Comment, pk=comment_id, user=request.user)
        content = request.POST.get('content')
        rating = request.POST.get('rating')
        if content and rating:
            comment.content = content
            comment.rating = int(rating)
            comment.save()
            # Update average rating
            average_rating = Comment.objects.filter(place=comment.place).aggregate(Avg('rating'))['rating__avg'] or 0
            average_rating = round(average_rating, 1)
            # Return the rendered HTML for the updated comment and updated average rating
            rendered_comment = render_to_string('places/comment_partial.html', {'comment': comment, 'user': request.user})
            return JsonResponse({
                'message': 'Your review has been updated successfully.',
                'comment_html': rendered_comment,
                'comment_id': comment_id,
                'average_rating': average_rating
            })
        else:
            return JsonResponse({'error': 'Please provide both a comment and a rating.'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

@login_required
@csrf_exempt
def delete_comment_ajax(request, comment_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        comment = get_object_or_404(Comment, pk=comment_id, user=request.user)
        place = comment.place
        comment.delete()
        # Update average rating
        average_rating = Comment.objects.filter(place=place).aggregate(Avg('rating'))['rating__avg'] or 0
        average_rating = round(average_rating, 1)
        return JsonResponse({
            'message': 'Your review has been deleted.',
            'comment_id': comment_id,
            'average_rating': average_rating
        })
    else:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

# New view for adding a place to collections
import json

@login_required
@csrf_exempt
def add_to_collection_ajax(request, place_id):
    if request.method == 'POST':
        try:
            # Try to get collections from POST data first
            collections = request.POST.getlist('collections[]', request.POST.getlist('collections'))
            
            # If not in POST, try to get from JSON body
            if not collections and request.body:
                try:
                    body = json.loads(request.body)
                    collections = body.get('collections', [])
                except json.JSONDecodeError:
                    pass
            
            print("Received collections:", collections)
            
            # Validasi place_id dan collections
            place = get_object_or_404(Place, pk=place_id)
            if collections:
                for collection_id in collections:
                    collection = get_object_or_404(Collection, pk=collection_id, user=request.user)
                    existing_item = CollectionItem.objects.filter(collection=collection, place=place).first()
                    if not existing_item:
                        CollectionItem.objects.create(collection=collection, place=place)
                
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': 'No collections selected.'}, status=400)
        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request.'}, status=400)
    
# New view for buying a souvenir
@login_required
@csrf_exempt
def buy_souvenir_ajax(request, souvenir_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        souvenir = get_object_or_404(Souvenir, pk=souvenir_id)
        if souvenir.stock > 0:
            souvenir.stock -= 1
            souvenir.save()
            
            # Recalculate available and total souvenirs
            place = souvenir.place
            souvenirs = Souvenir.objects.filter(place=place)
            total_souvenirs_count = souvenirs.count()
            available_souvenirs_count = souvenirs.filter(stock__gt=0).count()
            
            return JsonResponse({
                'success': True,
                'new_stock': souvenir.stock,
                'available_souvenirs_count': available_souvenirs_count,
                'total_souvenirs_count': total_souvenirs_count
            })
        else:
            return JsonResponse({'error': 'Souvenir is out of stock.'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request.'}, status=400)
    
    # Add this new view to views.py
@csrf_exempt
@require_http_methods(["GET"])  # Only allow GET requests
def place_detail_json(request, place_id):
    try:
        place = get_object_or_404(Place, pk=place_id)
        
        # Get comments for the place
        comments = Comment.objects.filter(place=place).order_by('-created_at')
        comments_data = [{
            'id': comment.id,
            'username': comment.user.username,
            'content': comment.content,
            'rating': comment.rating,
            'created_at': comment.created_at.isoformat()
        } for comment in comments]
        
        # Get souvenirs for the place
        souvenirs = Souvenir.objects.filter(place=place)
        souvenirs_data = [{
            'id': souvenir.id,
            'name': souvenir.name,
            'price': souvenir.price,
            'stock': souvenir.stock
        } for souvenir in souvenirs]
        
        # Aggregate average rating
        average_rating = Comment.objects.filter(place=place).aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Format the place data as a dictionary
        place_data = {
            'id': place.id,
            'name': place.name,
            'description': place.description,
            'average_rating': round(average_rating),
            'comments': comments_data,
            'souvenirs': souvenirs_data
        }
        
        response = JsonResponse(place_data, encoder=DjangoJSONEncoder)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Max-Age"] = "1000"
        response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"
        
        return response
        
    except Exception as e:
        # Return error as JSON instead of HTML
        error_response = JsonResponse({
            'error': str(e),
            'detail': 'Failed to fetch place details'
        }, status=400)
        error_response["Access-Control-Allow-Origin"] = "*"
        return error_response
    
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from .models import Place, Comment

@login_required
@csrf_exempt
def add_comment_dart(request, place_id):
    if request.method == 'POST':  # Cek jika permintaan POST
        try:
            place = get_object_or_404(Place, pk=place_id)
            
            # Ambil data dari body request (JSON)
            data = json.loads(request.body)
            content = data.get('comment')
            rating = data.get('rating')

            # Validasi data
            if not content or not rating:
                return JsonResponse({'error': 'Please provide both a comment and a rating.'}, status=400)

            # Buat komentar baru
            comment = Comment.objects.create(
                place=place,
                user=request.user,
                content=content,
                rating=int(rating),
                created_at=timezone.now()
            )

            # Hitung ulang rata-rata rating
            average_rating = Comment.objects.filter(place=place).aggregate(Avg('rating'))['rating__avg'] or 0
            average_rating = round(average_rating, 1)

            # Kirimkan respons JSON ke Dart
            return JsonResponse({
                'message': 'Your review has been submitted successfully.',
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'rating': comment.rating,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'user': request.user.username,
                },
                'average_rating': average_rating,
            }, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)
