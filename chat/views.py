from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from cryptography.fernet import Fernet
from .models import ChatRoom, Message, DiaryEntry, ScheduledMessage, CustomSticker, RoomInvitation
import json
import base64
from datetime import datetime
import pytz
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import logout
import os
from django.conf import settings

def home(request):
    if request.user.is_authenticated:
        rooms = ChatRoom.objects.filter(participants=request.user)
        return render(request, 'chat/home.html', {'rooms': rooms})
    return render(request, 'chat/home.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def chat_room(request, room_id):
    try:
        room = get_object_or_404(ChatRoom, id=room_id)
        if request.user not in room.participants.all():
            return redirect('home')
        
        # Filter out messages with invalid file references
        messages_list = []
        for msg in Message.objects.filter(room=room):
            try:
                # For messages with files
                if msg.file:
                    try:
                        # Test if file is accessible
                        msg.file.size
                        messages_list.append(msg)
                    except Exception as file_error:
                        print(f"File error for message {msg.id}: {str(file_error)}")
                        # Only append if it's a text message
                        if msg.message_type == 'text':
                            messages_list.append(msg)
                else:
                    # No file attached, safe to append
                    messages_list.append(msg)
            except Exception as msg_error:
                print(f"Message processing error for message {msg.id}: {str(msg_error)}")
                continue
                
        # Get stickers with error handling
        try:
            stickers = CustomSticker.objects.all()
        except Exception as sticker_error:
            print(f"Error fetching stickers: {str(sticker_error)}")
            stickers = []
        
        return render(request, 'chat/room.html', {
            'room': room,
            'messages': messages_list,
            'stickers': stickers,
            'room_id': room_id,
        })
    except Exception as e:
        import traceback
        print(f"Error in chat_room view for room {room_id}: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, "There was an error loading the chat room. Please try again.")
        return redirect('home')

@login_required
def create_room(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        room = ChatRoom.objects.create(name=name)
        room.participants.add(request.user)
        return redirect('chat_room', room_id=room.id)
    return render(request, 'chat/create_room.html')

@csrf_exempt
@login_required
def send_message(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(ChatRoom, id=room_id)
        if request.user not in room.participants.all():
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        try:
            message_type = 'text'
            content = ''
            file = None
            reply_to_id = None

            # Handle file uploads
            if request.FILES:
                file = request.FILES.get('file')
                if not file:
                    return JsonResponse({'error': 'No file provided'}, status=400)
                
                message_type = request.POST.get('type', 'text')
                content = request.POST.get('content', file.name)
                reply_to_id = request.POST.get('reply_to')

                # Validate file upload
                if message_type == 'image':
                    if not file.content_type.startswith('image/'):
                        return JsonResponse({'error': 'Invalid image file'}, status=400)
                elif message_type == 'voice':
                    if not file.content_type.startswith('audio/'):
                        return JsonResponse({'error': 'Invalid audio file'}, status=400)
                
                if file.size > 20 * 1024 * 1024:  # 20MB limit
                    return JsonResponse({'error': f'File too large. Maximum size is 20MB. Your file is {round(file.size/1024/1024, 2)}MB'}, status=400)

                # Generate a unique filename
                file_extension = os.path.splitext(file.name)[1]
                unique_filename = f"{message_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
                file.name = unique_filename

            # Handle JSON data
            elif request.content_type == 'application/json':
                data = json.loads(request.body)
                content = data.get('content', '')
                message_type = data.get('type', 'text')
                reply_to_id = data.get('reply_to')
            # Handle form data
            else:
                content = request.POST.get('content', '')
                message_type = request.POST.get('type', 'text')
                reply_to_id = request.POST.get('reply_to')

            # Get reply_to message if provided
            reply_to = None
            if reply_to_id:
                try:
                    reply_to = Message.objects.get(id=reply_to_id, room=room)
                except Message.DoesNotExist:
                    pass

            # Encrypt the message content
            f = Fernet(room.encryption_key.encode())
            encrypted_content = f.encrypt(content.encode()).decode()

            # Create the message
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content=content,
                encrypted_content=encrypted_content,
                message_type=message_type,
                file=file,
                reply_to=reply_to
            )

            response_data = {
                'status': 'success',
                'message_id': message.id,
                'sender': request.user.username,
                'created_at': message.created_at.isoformat(),
            }

            # Add file URL if present
            if file and message.file:
                try:
                    response_data['file_url'] = message.file.url
                except ValueError as e:
                    print(f"Error getting file URL: {str(e)}")
                    response_data['file_url'] = None
                except Exception as e:
                    print(f"Unexpected error with file URL: {str(e)}")
                    response_data['file_url'] = None

            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            import traceback
            print(f"Error in send_message: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def diary_entry(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        # Encrypt the diary content
        f = Fernet(room.encryption_key.encode())
        encrypted_content = f.encrypt(content.encode()).decode()

        DiaryEntry.objects.create(
            room=room,
            author=request.user,
            title=title,
            content=content,
            encrypted_content=encrypted_content
        )
        return redirect('chat_room', room_id=room_id)

    entries = DiaryEntry.objects.filter(room=room)
    return render(request, 'chat/diary.html', {'room': room, 'entries': entries})

@login_required
def schedule_message(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    indian_tz = pytz.timezone('Asia/Kolkata')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        scheduled_time = request.POST.get('scheduled_time')
        
        if not content or not scheduled_time:
            return JsonResponse({'error': 'Both content and scheduled time are required'}, status=400)

        try:
            # Parse the datetime string and make it timezone-aware in Indian timezone
            naive_dt = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
            aware_dt = indian_tz.localize(naive_dt)

            # Don't allow scheduling in the past
            now = timezone.now().astimezone(indian_tz)
            if aware_dt <= now:
                return JsonResponse({'error': 'Cannot schedule messages in the past'}, status=400)

            # Encrypt the message content
            f = Fernet(room.encryption_key.encode())
            encrypted_content = f.encrypt(content.encode()).decode()

            scheduled_message = ScheduledMessage.objects.create(
                room=room,
                sender=request.user,
                content=content,
                encrypted_content=encrypted_content,
                scheduled_time=aware_dt
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': f'Message scheduled for {aware_dt.strftime("%I:%M %p")}'
                })
            return redirect('chat_room', room_id=room_id)
        except ValueError as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=400)
            return render(request, 'chat/schedule_message.html', {
                'room': room,
                'error': str(e)
            })

    # Get all scheduled messages for this room
    scheduled_messages = ScheduledMessage.objects.filter(
        room=room,
        sent=False
    ).order_by('scheduled_time')

    # Convert scheduled times to Indian timezone for display
    for message in scheduled_messages:
        message.scheduled_time = message.scheduled_time.astimezone(indian_tz)

    return render(request, 'chat/schedule_message.html', {
        'room': room,
        'scheduled_messages': scheduled_messages
    })

@login_required
def upload_sticker(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        
        sticker = CustomSticker.objects.create(
            name=name,
            image=image,
            uploaded_by=request.user
        )
        return JsonResponse({
            'status': 'success',
            'sticker_id': sticker.id,
            'url': sticker.image.url
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.user not in room.participants.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    messages = Message.objects.filter(room=room).order_by('-created_at')[:50]
    
    message_list = []
    for message in reversed(messages):
        try:
            file_url = None
            if message.file and hasattr(message.file, 'url'):
                try:
                    file_url = message.file.url
                except ValueError:
                    file_url = None
                    
            message_list.append({
                'id': message.id,
                'sender': message.sender.username,
                'content': message.get_decrypted_content(),
                'type': message.message_type,
                'file_url': file_url,
                'created_at': message.created_at.isoformat()
            })
        except Exception as e:
            print(f"Error processing message {message.id}: {e}")
            continue
    
    return JsonResponse({'messages': message_list})

@login_required
def generate_invite(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if request.user not in room.participants.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Create a new invitation
    invitation = RoomInvitation.objects.create(
        room=room,
        created_by=request.user
    )
    
    invite_url = request.build_absolute_uri(
        reverse('join_room', kwargs={'invite_code': invitation.invite_code})
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'invite_url': invite_url,
            'invite_code': invitation.invite_code
        })
    
    messages.success(request, f'Invitation link created: {invite_url}')
    return redirect('chat_room', room_id=room.id)

def join_room(request, invite_code):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    
    invitation = get_object_or_404(RoomInvitation, invite_code=invite_code, is_active=True)
    room = invitation.room
    
    if request.user not in room.participants.all():
        room.participants.add(request.user)
        messages.success(request, f'You have joined the room: {room.name}')
    else:
        messages.info(request, f'You are already a member of {room.name}')
    
    return redirect('chat_room', room_id=room.id)

def logout_view(request):
    logout(request)
    return redirect('home')
