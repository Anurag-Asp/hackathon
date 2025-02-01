from django.http import JsonResponse
from .utils import create_qa_chain
from .models import PDFDocument, ChatMessage
from django.shortcuts import render
from django.shortcuts import render, redirect
from .utils import process_pdf
import os
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required(login_url='login')
def home(request):
    if request.method == 'POST' and request.FILES['pdf_file']:
        # Save uploaded file
        pdf = PDFDocument(
            user=request.user,
            uploaded_file=request.FILES['pdf_file']
        )
        pdf.save()

        # Process PDF
        full_vector_path = pdf.vector_db_path
        os.makedirs(full_vector_path, exist_ok=True)
        
        process_pdf(
            pdf.uploaded_file.path,  # Temporary file path
            full_vector_path
        )
        
        pdf.processed = True
        pdf.save()
        return redirect('chat', pdf_id=pdf.id)

    return render(request, 'index.html')

from django.views.decorators.http import require_http_methods
@require_http_methods(["GET", "POST"])
@login_required(login_url='login')
def chat_with_pdf(request, pdf_id):
    pdf = PDFDocument.objects.get(id=pdf_id, user=request.user)
    qa_chain = create_qa_chain(pdf.vector_db_path)
    
    if request.method == 'POST':
        query = request.POST.get('query')
        response = qa_chain.invoke({"question": query})
        # Save chat history
        ChatMessage.objects.create(
            pdf_document=pdf,
            message=query,
            response=response['result'],
            sources=[doc.metadata for doc in response['source_documents']]
        )
        return JsonResponse({
            'answer': response['result'],
            'sources': [doc.metadata for doc in response['source_documents']]
        })
    
    # Retrieve existing chat messages
    chat_messages = ChatMessage.objects.filter(pdf_document=pdf).order_by('timestamp')
    user_pdfs = PDFDocument.objects.filter(user=request.user).order_by('-uploaded_at')
    
    return render(request, 'chat.html', {
        'pdf': pdf,
        'chat_messages': chat_messages,
        'user_pdfs': user_pdfs
    })

from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                if user.email_verified:
                    login(request, user)
                    return redirect('home')
                messages.error(request, 'Verify your email first.')
                return redirect('login')
            messages.error(request, 'Invalid credentials.')
            return redirect('login')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})



@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("login")

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()
token_generator = PasswordResetTokenGenerator()

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email_verified = False
            user.save()
            
            # Send verification email
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            verification_url = request.build_absolute_uri(
                f'/verify-email/{uid}/{token}/'
            )
            send_mail(
                'Verify Your Email',
                f'Click to verify: {verification_url}',
                'noreply@example.com',
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'Check your email to verify your account.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and token_generator.check_token(user, token):
        user.email_verified = True
        user.save()
        messages.success(request, 'Email verified! You can now login.')
        return redirect('login')
    messages.error(request, 'Invalid verification link.')
    return redirect('signup')

