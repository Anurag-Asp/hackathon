from django.shortcuts import render
from django.shortcuts import render, redirect
from .models import PDFDocument
from .utils import process_pdf
import os
from django.views.decorators.csrf import csrf_exempt

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

# pdfprocessor/views.py
from django.http import JsonResponse
from .utils import create_qa_chain

@csrf_exempt
def chat_with_pdf(request, pdf_id):
    pdf = PDFDocument.objects.get(id=pdf_id, user=request.user)
    qa_chain = create_qa_chain(pdf.vector_db_path)
    
    if request.method == 'POST':
        query = request.POST.get('query')
        response = qa_chain.invoke({"query": query})
        return JsonResponse({
            'answer': response['result'],
            'sources': [doc.metadata for doc in response['source_documents']]
        })
    
    return render(request, 'chat.html', {'pdf': pdf})

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
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})