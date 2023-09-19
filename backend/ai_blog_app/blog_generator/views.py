from django.shortcuts import render, HttpResponseRedirect, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
from pytube import YouTube
import os
import assemblyai as aai
import openai
from .models import BlogPost

# authentication views
@login_required
def index(request):
    return render(request, 'blog_generator/index.html')

def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'blog_generator/login.html', {'error_message': error_message})
        
    return render(request, 'blog_generator/login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_mesage = 'Error creating account'
                return render(request, 'blog_generator/signup.html', {'error_message' : error_mesage})
        else:
            error_mesage = 'Password do not match'
            return render(request, 'blog_generator/signup.html', {'error_message' : error_mesage})
    return render(request, 'blog_generator/signup.html')

# main view

@csrf_exempt # using this view we don't need csrf token in our html file
def generate_blog(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            youtube_link = data['link']

        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error' : 'Invalid data sent'}, status = 400)
        
        # get youtube link
        title = youtube_title(youtube_link)

        # get transcript
        transcription = get_transcription(youtube_link)
        if not transcription:
            return JsonResponse({'error' : "Failed to get transcript.."}, status=500)
        
        # use OpenAI to generate the blog based on the entered prompt
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error':"Failed to generate blog article"}, status=500)

        # save blog article to the database
        new_blog_article = BlogPost.objects.create(
            user = request.user,
            youtube_title = title,
            youtube_link = youtube_link,
            generate_content = blog_content
        )
        new_blog_article.save()

        # return the blog article as a response
        return JsonResponse({'content': blog_content})
    else:
        return JsonResponse({'error' : 'Invalid request method'}, status = 405)
    
def youtube_title(link):
    youtube = YouTube(link)
    title = youtube.title
    return title

def download_audio(link):
    youtube = YouTube(link)
    # extract audio from video
    video = youtube.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file

def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = "4fa1a71705f5435c921b6846facafef8"

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    return transcript.text

def generate_blog_from_transcription(transcription):

    # open ai API key visit : https://platform.openai.com/ 
    openai.api_key = "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"

    prompt = f"Based on the following transcription from the YouTube video, write a comprehensive blog article, write it based on the transcription, but don't make it like a youtube video, make it like a proper blog article:\n\n{transcription}\n\nArticle :"

    response = openai.Completion.create(
        model = "text-davinci-003",
        prompt = prompt,
        max_tokens = 1000
    )

    # extract the generated content from the responses
    generated_content = response.choices[0].text.strip()

    return generated_content

def blog_list(request):
    blog_articles = BlogPost.objects.filter(user= request.user)
    return render(request, 'blog_generator/all-blogs.html', {'blog_articles' : blog_articles})

def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id = pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog_generator/blog-details.html', {'blog_article_detail' : blog_article_detail})
    else:
        return redirect('/')