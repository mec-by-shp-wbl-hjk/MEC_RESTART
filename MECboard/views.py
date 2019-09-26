from django.shortcuts import render, redirect, render_to_response, get_object_or_404
from MECboard.models import Board, Comment, Profile
import os
import math
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.http import urlquote
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from MECboard.forms import UserForm, LoginForm
from django.contrib.auth.models import User
from django.contrib.auth import (authenticate, login as django_login, logout as django_logout, )
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score

UPLOAD_DIR = "C:/Users/John/Documents/GitHub/MEC_RESTART/MECboard/media/images"
login_failure = False

@csrf_exempt
def list(request):
    
    try:
        search_option=request.POST["search_option"]
    except:
        search_option="writer"
    try:
        search=request.POST["search"]
    except:
        search=""
        
    if search_option=="all":
        boardCount=Board.objects.filter(Q(writer__contains=search)
        |Q(title__contains=search)|Q(content__contains=search)).count()
    elif search_option=="writer":
        boardCount=Board.objects.filter(Q(writer__contains=search)).count()
    elif search_option=="title":
        boardCount=Board.objects.filter(Q(title__contains=search)).count()
    elif search_option=="content":
        boardCount=Board.objects.filter(Q(content__contains=search)).count()
       
    try:
        start=int(request.GET["start"])
    except:
        start=0
    page_size = 10
    page_list_size = 10
    end = start + page_size
    total_page = math.ceil(boardCount / page_size)
    current_page=math.ceil( (start+1) / page_size )
    start_page = math.floor( (current_page - 1) / page_list_size)\
        * page_list_size + 1
    end_page = start_page + page_list_size - 1
    
    if total_page < end_page:
        end_page = total_page
    if start_page >= page_list_size:
        prev_list = (start_page - 2) * page_size
    else:
        prev_list = 0
    if total_page > end_page:
        next_list = end_page * page_size
    else:
        next_list = 0
    
    if search_option=="all":
        boardList=Board.objects.filter(Q(writer__contains=search)
        |Q(title__contains=search)|Q(content__contains=search)).order_by("-idx")[start:end]
    elif search_option=="writer":
        boardList=Board.objects.filter(Q(writer__contains=search)).order_by("-idx")[start:end]
    elif search_option=="title":
        boardList=Board.objects.filter(Q(title__contains=search)).order_by("-idx")[start:end]
    elif search_option=="content":
        boardList=Board.objects.filter(Q(content__contains=search)).order_by("-idx")[start:end]
        
    links = []
    for i in range(start_page, end_page+1):
        page = (i-1) * page_size
        links.append("<a href='?start="+str(page)+"'>"+str(i)+"</a>")
        
    if not request.user.is_authenticated:
        username = request.user
        is_authenticated = request.user.is_authenticated
    else:
        username = request.user.username
        is_authenticated = request.user.is_authenticated
    
    return render_to_response("list.html", 
                    {"boardList":boardList, "boardCount":boardCount,
                     "search_option":search_option, "search":search,
                     "range":range(start_page-1, end_page),
                     "start_page":start_page, "end_page":end_page,
                     "page_list_size":page_list_size, "total_page":total_page,
                     "prev_list":prev_list, "next_list":next_list,
                     "links":links, "username":username, "is_authenticated":is_authenticated,})

def write(request):
    username = request.user
    is_authenticated = True
    return render_to_response("write.html", {"username":username, "is_authenticated":is_authenticated})

@csrf_exempt
def insert(request):
    fname=""
    fsize=0

    if "file" in request.FILES:
        file = request.FILES["file"]
        print(file)
        fname = file._name
        print(UPLOAD_DIR+fname)
        with open("%s%s" % (UPLOAD_DIR, fname), "wb") as fp:
            for chunk in file.chunks():
                fp.write(chunk)
            
        fsize = os.path.getsize(UPLOAD_DIR+fname)

    if "thumbnail" in request.FILES:
        file = request.FILES["thumbnail"]
        print(file)
        thumbnail_name = file._name
        print(UPLOAD_DIR + thumbnail_name)
        with open("%s%s" % (UPLOAD_DIR, thumbnail_name), "wb") as fp:
            for chunk in file.chunks():
                fp.write(chunk)

        dto = Board(writer=request.POST["writer"],
                    title=request.POST["title"],
                    content=request.POST["content"],
                    filename=fname, filesize=fsize,
                    image_thumbnail=request.FILES["thumbnail"])
        dto.save()
    else:
        dto = Board(writer=request.POST["writer"],
                    title=request.POST["title"],
                    content=request.POST["content"],
                    filename=fname, filesize=fsize)
        dto.save()

    id = str(dto.idx)

    username = request.POST["username"]
    is_authenticated = request.POST["is_authenticated"]
    return HttpResponseRedirect("detail?idx="+id+"&username="+username+"&is_authenticated="+is_authenticated)


def download(request):
    id = request.GET["idx"]
    dto = Board.objects.get(idx=id)
    path = UPLOAD_DIR+dto.filename
    filename = os.path.basename(path)
    filename=urlquote(filename)
    with open(path, "rb") as file:
        response = HttpResponse(file.read(),
                content_type="application/octet-stream")
        response["Content-Disposition"]=\
        "attachment;filename*=UTF-8''{0}".format(filename)
        dto.down_up()
        dto.save()
    return response
  
@csrf_exempt        
def detail(request):
    id = request.GET["idx"]
    username = request.GET["username"]
    is_authenticated = request.GET["is_authenticated"]
    is_superuser = request.user.is_superuser
    dto = Board.objects.get(idx=id)
    dto.hit_up()
    dto.save()
    filesize="%.2f" % (dto.filesize / 1024)
    
    try:
        search_option=request.POST["array_option"]
    except:
        search_option="written"
    if search_option=="written":
        commentList=Comment.objects.filter(board_idx=id).order_by("idx")
    elif search_option=="rating":
        commentList=Comment.objects.filter(board_idx=id).order_by("-rating")
        
    return render_to_response("detail.html", 
        {"dto":dto, "filesize":filesize, "commentList":commentList, "username":username,
          "is_authenticated":is_authenticated, "is_superuser":is_superuser, "search_option":search_option})

@csrf_exempt    
def update_page(request):
    id = request.POST['idx']
    dto = Board.objects.get(idx=id)
    filesize="%.2f" % (dto.filesize / 1024)
    username = request.user
    is_authenticated = True
    return render_to_response("update_page.html", {"username":username, "dto":dto, "filesize":filesize, "is_authenticated":is_authenticated})

@csrf_exempt
def update(request):
    id = request.POST["idx"]
    dto_src=Board.objects.get(idx=id)
    username = request.POST["username"]
    is_authenticated = request.POST["is_authenticated"]
    fname = dto_src.filename
    fsize = dto_src.filesize
    if "file" in request.FILES:
        file = request.FILES["file"]
        fname = file._name
        fp = open("%s%s" % (UPLOAD_DIR, fname), "wb")
        for chunk in file.chunks():
            fp.write(chunk)
        fp.close()
        fsize = os.path.getsize(UPLOAD_DIR+fname)
        
    dto_new = Board(idx=id, writer=request.POST["writer"],
        title=request.POST["title"], content=request.POST["content"],
        filename=fname, filesize=fsize, hit=request.POST["hit"],
        rating=request.POST["rating"], ratings_up=request.POST["ratings_up"], ratings_down=request.POST["ratings_down"])
    dto_new.save()
    return HttpResponseRedirect("detail?idx="+id+"&username="+username+"&is_authenticated="+is_authenticated)


@csrf_exempt
def delete(request):
    id = request.POST["idx"]
    Board.objects.get(idx=id).delete()
    return redirect("/")

@csrf_exempt
def reply_insert(request):
    id = request.POST["idx"]
    username = request.POST["username"]
    is_authenticated = request.POST["is_authenticated"]
    vote=request.POST["vote"]
    dto_board = Board.objects.get(idx=id)
    fname=""
    fsize=0

    if "file" in request.FILES:
        file = request.FILES["file"]
        print(file)
        fname = file._name
        
        print(UPLOAD_DIR+fname)
        with open("%s%s" %(UPLOAD_DIR,fname), "wb") as fp:
            for chunk in file.chunks():
                fp.write(chunk)
            
        fsize = os.path.getsize(UPLOAD_DIR+fname)
        dto = Comment(board_idx=id, writer=request.POST["writer"],
                    content=request.POST["content"], vote=request.POST["vote"],filename = fname, filesize = fsize, image=request.FILES["file"], evidence=request.POST["evidence"])
    else:
        dto = Comment(board_idx=id, writer=request.POST["writer"],
                      content=request.POST["content"], vote=request.POST["vote"], filename=fname, filesize=fsize, evidence=request.POST["evidence"])
    dto.save()

    post = get_object_or_404(Comment, idx=dto.idx)
    user = request.user
    profile = Profile.objects.get(user=user)
    profile.user_commentlist.add(post)

    if vote == '1' or vote == '2':
        dto_board.rate_up()
    else:
        dto_board.rate_down()
    dto_board.rating = dto_board.ratings_up - dto_board.ratings_down
    dto_board.save()

    return HttpResponseRedirect("detail?idx="+id+"&username="+username+"&is_authenticated="+is_authenticated)

@csrf_exempt
@login_required
def reply_rating(request):
    cid = request.GET["cid"]
    id = request.GET["idx"]
    username = request.GET["username"]
    is_authenticated = request.GET["is_authenticated"]
    cdto = Comment.objects.get(idx=cid)

    post = get_object_or_404(Comment, idx=cid)
    user = request.user
    profile = Profile.objects.get(user=user)

    check_like_post = profile.user_likelist.filter(idx=post.idx)

    if check_like_post.exists():
        profile.user_likelist.remove(post)
        cdto.rating -= 1
        cdto.save()
    else:
        profile.user_likelist.add(post)
        cdto.rating += 1
        cdto.save()
    #예전꺼
    # if rate == '1':
    #     cdto.rate_up()
    # else:
    #     cdto.rate_down()
    # cdto.rating = cdto.ratings_up - cdto.ratings_down
    # cdto.save()

    return HttpResponseRedirect("detail?idx="+id+"&username="+username+"&is_authenticated="+is_authenticated)

@csrf_exempt
def reply_update(request):
    cid = request.POST["cid"]
    id = request.POST["idx"]
    username = request.POST["username"]
    is_authenticated = request.POST["is_authenticated"]
    dto_src=Comment.objects.get(idx=cid)
    fname = dto_src.filename
    fsize = dto_src.filesize
    if "file" in request.FILES:
        file = request.FILES["file"]
        fname = file._name
        fp = open("%s%s" % (UPLOAD_DIR, fname), "wb")
        for chunk in file.chunks():
            fp.write(chunk)
        fp.close()
        fsize = os.path.getsize(UPLOAD_DIR+fname)
    dto_new = Comment(idx=cid, board_idx=id, writer=request.POST["writer"], content=request.POST["content"],
        rating=request.POST["rating"], ratings_up=request.POST["ratings_up"], ratings_down=request.POST["ratings_down"],
        filename=fname, filesize=fsize, vote=request.POST["vote"],)
    dto_new.save()
    return HttpResponseRedirect("detail?idx="+id+"&username="+username+"&is_authenticated="+is_authenticated)

@csrf_exempt
def reply_delete(request):
    cid = request.GET["cid"]
    id = request.GET["idx"]
    username = request.GET["username"]
    is_authenticated = request.GET["is_authenticated"]
    dto = Board.objects.get(idx=id)
    cdto = Comment.objects.get(idx=cid)
    if cdto.vote == 1:
        dto.ratings_up -= 1
        dto.rating -= 1
    else:
        dto.ratings_down -= 1
        dto.rating += 1
    dto.save()
    cdto.delete()
    return HttpResponseRedirect("detail?idx="+id+"&username="+username+"&is_authenticated="+is_authenticated)

@csrf_exempt    
def reply_update_page(request):
    id = request.GET['cid']
    dto = Comment.objects.get(idx=id)
    username = request.GET["username"]
    is_authenticated = request.GET["is_authenticated"]
    filesize="%.2f" % (dto.filesize / 1024)

    return render_to_response("reply_update_page.html", {"username":username, "dto":dto, "filesize":filesize, "is_authenticated":is_authenticated})
@csrf_exempt
def evidence_insert(request):
    id = request.GET["idx"]
    username = request.GET["username"]
    is_authenticated = request.GET["is_authenticated"]
    is_superuser = request.user.is_superuser
    profile = Profile.objects.get(user=request.user)
    dto = Board.objects.get(idx=id)
    dto.hit_up()
    dto.save()

    filesize = "%.2f" % (dto.filesize / 1024)

    try:
        search_option = request.POST["array_option"]
    except:
        search_option = "written"
    if search_option == "written":
        commentList = Comment.objects.filter(board_idx=id).order_by("idx")
    elif search_option == "rating":
        commentList = Comment.objects.filter(board_idx=id).order_by("-rating")

    return render_to_response("evidence_insert.html",
                              {"dto": dto, "filesize": filesize, "commentList": commentList, "username": username,
                               "is_authenticated": is_authenticated, "is_superuser": is_superuser,
                               "search_option": search_option, "profile":profile})

def create_profile(request):
    user = request.user
    Profile.objects.create(user=user)

def join(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            new_user = User.objects.create_user(**form.cleaned_data)
            django_login(request, new_user)
            return redirect("/")
        else:
            return render_to_response("index.html", 
                                      {"msg":"failed to sign up..."})
    else:
        form = UserForm()
    return render(request, "join.html", {"form":form})

def logout(request):
    django_logout(request)
    return redirect("/")

def login_check(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        name = request.POST["username"]
        pwd = request.POST["password"]
        user = authenticate(username=name, password=pwd)
        if user is not None:
            django_login(request, user)
            return redirect("/")
        else:
            return render(request, "login.html", {"form":form, "msg":"failed to login..."})
    else:
        form = LoginForm()
    return render(request, "login.html", {"form":form, "msg":"no error"})

def muchin_learning(request):
    vec = TfidfVectorizer(min_df=2, tokenizer=None, norm='l2')
    conn = sqlite3.connect("db.sqlite3")
    df = pd.read_sql_query("select * from rating")
    rf = RandomForestClassifier(n_estimators=50)

    df = df.dropna(subset=['rating'])
    df.index = range(0, len(df))
    reviews_data = df['gaming'].astype(str).tolist()
    reviews_rating = df['rating'].astype(str).tolist()
    train_size = int(round(len(reviews_data) * 0.8))

    x_train = np.array([''.join(data) for data in reviews_data[0:train_size]])
    y_train = np.array([''.join(data) for data in reviews_rating[0:train_size]])

    x_test = np.array([''.join(data) for data in reviews_data[train_size:]])
    y_test = np.array([''.join(data) for data in reviews_rating[train_size:]])

    x_train = vec.fit_transform(x_train)
    x_test = vec.transform(x_test)
    rf.fit(x_train, y_train)
    pred = rf.predict(x_test)


