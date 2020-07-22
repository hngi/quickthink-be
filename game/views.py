import html
import random

import requests
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse

# Create your views here.
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from django.db import IntegrityError

from game.models import Game, Question, UserGames, Options, Category
from game.serializers import GameSerializer, QuestionSerializer, OptionsSerializer, UserGamesSerializer, \
    CategorySerializer, UserSerializer, ResetUserPasswordSerializer

from rest_framework.authtoken.models import Token


@api_view(['GET'])
def get_all_category(request):
    try:
        data = Category.objects.all()
        question = CategorySerializer(data, many=True).data
        return JsonResponse({
            "data": question
        }, status=status.HTTP_200_OK)
    except Exception as error:
        return JsonResponse({
            "error": error
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def create_category(request):
    if request.method == "POST":
        if 'name' not in request.data:
            return JsonResponse({
                "error": "Enter category name"
            }, status=status.HTTP_400_BAD_REQUEST)
        token = request.META['HTTP_AUTHORIZATION'].split(' ')
        try:
            user = Token.objects.get(key=token[1]).user
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        data = {
            'name': request.data['name'],
            'user': user.id
        }
        createcategory = CategorySerializer(data=data)
        if createcategory.is_valid():
            createcategory.save()
            return Response(createcategory.data, status=status.HTTP_201_CREATED)
        return Response(createcategory.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def create_question(request):
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    try:
        user = Token.objects.get(key=token[1]).user
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
        )
    question = request.data.get('Question')
    cats = Category.objects.filter(name=question['category'])
    if len(cats) == 0:
        return JsonResponse(
            {"error": "Enter valid category"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        index = question['options'].index(question['answer'])
    except Exception as error:
        return JsonResponse(
            {"error": "There is no option with the answer "}, status=status.HTTP_400_BAD_REQUEST
        )
    category = CategorySerializer(cats, many=True).data
    options = question['options']
    if len(options) != 4:
        return JsonResponse(
            {"error": "There should be exaclty 4 options"}, status=status.HTTP_400_BAD_REQUEST
        )
    optionsList = []
    for option in options:
        optionData = Options.objects.filter(option=option)
        if len(optionData) == 0:
            option = {
                'option': option
            }
            serializer = OptionsSerializer(data=option, many=False)
            if serializer.is_valid():
                serializer.save()
        else:
            serializer = OptionsSerializer(optionData[0], many=False)
        optionsList.append(serializer.data['option'])
    question = {
        "question": question['question'],
        "category": category[0]['name'],
        "options": optionsList,
        "user": user.id,
        "answer": optionsList[index]
    }
    serializer = QuestionSerializer(data=question)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse({
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@authentication_classes((TokenAuthentication,))
def update_question(request):
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    try:
        user = Token.objects.get(key=token[1]).user
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
        )
    question = request.data.get('Question')
    questionData = Question.objects.filter(id=question['id'])

    if len(questionData) == 0:
        return JsonResponse(
            {"error": "There is no question with this id"}, status=status.HTTP_401_UNAUTHORIZED
        )
    ques = QuestionSerializer(questionData[0], many=False).data
    print(ques)
    if ques['user'] != user.id:
        return JsonResponse(
            {"error": "Cannot update the question .The questions can only be updated by the user who created"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    cats = Category.objects.filter(name=question['category'])
    if len(cats) == 0:
        return JsonResponse(
            {"error": "Enter valid category"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        index = question['options'].index(question['answer'])
    except Exception as error:
        return JsonResponse(
            {"error": "There is no option with the answer "}, status=status.HTTP_400_BAD_REQUEST
        )

    category = CategorySerializer(cats, many=True).data
    options = question['options']
    if len(options) != 4:
        return JsonResponse(
            {"error": "There should be exaclty 4 options"}, status=status.HTTP_400_BAD_REQUEST
        )
    optionsList = []
    for option in options:
        optionData = Options.objects.filter(option=option)
        if len(optionData) == 0:
            option = {
                'option': option
            }
            serializer = OptionsSerializer(data=option, many=False)
            if serializer.is_valid():
                serializer.save()
        else:
            serializer = OptionsSerializer(optionData[0], many=False)
        optionsList.append(serializer.data['option'])

    questionData = Question.objects.get(id=question['id'])
    questionData.question = question['question']
    questionData.category = Category.objects.get(name=category[0]['name'])
    questionData.options.set(optionsList)
    questionData.user = user
    questionData.answer = Options.objects.get(option=optionsList[index])
    questionData.save()
    serializer = QuestionSerializer(questionData)
    return JsonResponse({
        "data": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_questions(request):
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    try:
        user = Token.objects.get(key=token[1]).user
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
        )
    questions = Question.objects.filter()
    questionData = QuestionSerializer(questions, many=True).data
    questions = []
    for question in questionData:
        options = []
        for option in question['options']:
            optionQuery = Options.objects.get(option=option)
            optionData = OptionsSerializer(optionQuery, many=False).data
            options.append(optionData['option'])
        question['options'] = options
        questions.append(question)
    return JsonResponse({
        "data": questions
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_questions_user(request):
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    try:
        user = Token.objects.get(key=token[1]).user
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
        )
    questions = Question.objects.filter(user=user.id)
    questionData = QuestionSerializer(questions, many=True).data
    questions = []
    for question in questionData:
        options = []
        for option in question['options']:
            optionQuery = Options.objects.get(option=option)
            optionData = OptionsSerializer(optionQuery, many=False).data
            options.append(optionData['option'])
        question['options'] = options
        questions.append(question)
    return JsonResponse({
        "data": questions
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_all_category_user(request):
    try:
        token = request.META['HTTP_AUTHORIZATION'].split(' ')
        try:
            user = Token.objects.get(key=token[1]).user
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        data = Category.objects.filter(user=user.id)
        question = CategorySerializer(data, many=True).data
        return JsonResponse({
            "data": question
        }, status=status.HTTP_200_OK)
    except Exception as error:
        return JsonResponse({
            "error": error
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def create_a_game_code(request):
    if "user_name" not in request.data:
        return JsonResponse(
            {"error": "Enter user_name"}, status=status.HTTP_400_BAD_REQUEST
        )
    if "category" not in request.data:
        return JsonResponse(
            {"error": "Enter category"}, status=status.HTTP_400_BAD_REQUEST
        )

    data = {
        'user_name': request.data['user_name'],
        'category': request.data['category']
    }
    game = GameSerializer(data=data)
    if game.is_valid():
        game.save()
        return JsonResponse(game.data, status=status.HTTP_200_OK)
    return JsonResponse(game.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def check_if_game_code_isValid(request):
    if "game_code" not in request.data:
        return JsonResponse(
            {"error": "Enter game_code"}, status=status.HTTP_400_BAD_REQUEST
        )
    if "user_name" not in request.data:
        return JsonResponse(
            {"error": "Enter user_name"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        game = Game.objects.get(game_code=request.data['game_code'])
        gameData = GameSerializer(game).data
        if gameData['user_name'] == request.data['user_name']:
            return JsonResponse({"error": "Admin cannot play the game"}, status=status.HTTP_400_BAD_REQUEST)
        if gameData['active']:
            ug = UserGames.objects.filter(game_code=request.data['game_code'], user_name=request.data['user_name'])
            if len(ug) != 0:
                return JsonResponse({
                    "error": "Already played game"
                }, status=status.HTTP_400_BAD_REQUEST)
            qList = Question.objects.filter(category=gameData['category']).values_list('id', flat=True)
            qRand = random.sample(list(qList), min(len(qList), 10))
            questions = Question.objects.filter(id__in=qRand)
            questionData = QuestionSerializer(questions, many=True).data
            questions = []
            for question in questionData:
                options = []
                for option in question['options']:
                    optionQuery = Options.objects.get(option=option)
                    optionData = OptionsSerializer(optionQuery, many=False).data
                    options.append(optionData['option'])
                question['options'] = options
                questions.append(question)
            serializer = UserGamesSerializer(data={
                'game_code': request.data['game_code'],
                'category': gameData['category'],
                'user_name': request.data['user_name']
            })
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "data": {
                        'questions': questions,
                        'usergameData': serializer.data
                    }
                }, status=status.HTTP_200_OK)
            return JsonResponse({
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return JsonResponse({"error": "Game code is expired"}, status=status.HTTP_400_BAD_REQUEST)
    except Game.DoesNotExist:
        return JsonResponse({
            "error": "Invalid game code"
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as error:
        return
        JsonResponse({"error": error}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def check_if_user_can_play_game_code(request):
    if "game_code" not in request.data:
        return JsonResponse(
            {"error": "Enter game_code"}, status=status.HTTP_400_BAD_REQUEST
        )
    if "user_name" not in request.data:
        return JsonResponse(
            {"error": "Enter user_name"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        game = Game.objects.get(game_code=request.data['game_code'])
        gameData = GameSerializer(game).data
        if gameData['user_name'] == request.data['user_name']:
            return JsonResponse({"error": "User cannot play the game"}, status=status.HTTP_400_BAD_REQUEST)
        if gameData['active']:
            ug = UserGames.objects.filter(game_code=request.data['game_code'], user_name=request.data['user_name'])
            if len(ug) != 0:
                return JsonResponse({
                    "error": "Already played game"
                }, status=status.HTTP_400_BAD_REQUEST)
            return JsonResponse({
                "data": "User can play game"
            }, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"error": "Game code is expired"}, status=status.HTTP_400_BAD_REQUEST)
    except Game.DoesNotExist:
        return JsonResponse({
            "error": "Invalid game code"
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as error:
        return
        JsonResponse({"error": error}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def end_game(request):
    if "game_code" not in request.data:
        return JsonResponse(
            {"error": "Enter game_code"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        game = Game.objects.get(game_code=request.data['game_code'])
        updated = Game.objects.filter(game_code=request.data['game_code']).update(active=False)
        game = Game.objects.get(game_code=request.data['game_code'])
        gameData = GameSerializer(game).data
        return JsonResponse({
            "data": gameData
        }, status=status.HTTP_200_OK)
    except Game.DoesNotExist:
        return JsonResponse({
            "error": "Invalid game code"
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def update_score_usergame(request):
    if "user_game_id" not in request.data:
        return JsonResponse(
            {"error": "Enter user_game_id"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        ug = UserGames.objects.get(id=request.data['user_game_id'])
        ug.score = ug.score + 1
        ug.save()
        # ug = UserGames.objects.filter(id=request.data['user_game_id']).update(score=F['score'] + 1)
        ugSerializer = UserGamesSerializer(ug, many=False).data
        return JsonResponse({
            "data": ugSerializer
        }, status=status.HTTP_200_OK)
    except UserGames.DoesNotExist:
        return JsonResponse({
            "error": "Invalid user_game_id"
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as error:
        return JsonResponse({
            "error": error
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def update_score_count_usergame(request):
    if "user_game_id" not in request.data:
        return JsonResponse(
            {"error": "Enter user_game_id"}, status=status.HTTP_400_BAD_REQUEST
        )
    if "no_answers_crct" not in request.data:
        return JsonResponse(
            {"error": "Enter no_answers_crct"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        ug = UserGames.objects.get(id=request.data['user_game_id'])
        ug.score = ug.score + int(request.data['no_answers_crct'])
        ug.save()
        # ug = UserGames.objects.filter(id=request.data['user_game_id']).update(score=F['score'] + 1)
        ugSerializer = UserGamesSerializer(ug, many=False).data
        return JsonResponse({
            "data": ugSerializer
        }, status=status.HTTP_200_OK)
    except UserGames.DoesNotExist:
        return JsonResponse({
            "error": "Invalid user_game_id"
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as error:
        return JsonResponse({
            "error": error
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_leader_board_game_code(request):
    if request.query_params.get("game_code") is None:
        return JsonResponse(
            {"error": "Enter game_code"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        data = UserGames.objects.filter(game_code=request.query_params.get("game_code")).order_by('-score')
        if request.query_params.get("n") is not None:
            n = int(request.query_params.get("n"))
            data = data[:n]
        userGames = UserGamesSerializer(data, many=True).data
        return JsonResponse({
            "data": userGames
        }, status=status.HTTP_200_OK)
    except Exception as error:
        return JsonResponse({
            "error": error
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def register(request):
    if "username" not in request.data:
        return JsonResponse(
            {"error": "Enter username"}, status=status.HTTP_400_BAD_REQUEST
        )
    if "email" not in request.data:
        return JsonResponse(
            {"error": "Enter email"}, status=status.HTTP_400_BAD_REQUEST
        )
    if "password" not in request.data:
        return JsonResponse(
            {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
        )
    user = User.objects.filter(username=request.data['username'])
    if len(user) != 0:
        return JsonResponse(
            {"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST
        )
    user = User.objects.filter(email=request.data['email'])
    if len(user) != 0:
        return JsonResponse(
            {"error": "Email address already exists"}, status=status.HTTP_400_BAD_REQUEST
        )
    VALID_USER_FIELDS = [f.name for f in get_user_model()._meta.fields]
    serialized = UserSerializer(data=request.data)
    if serialized.is_valid():
        user_data = {field: data for (field, data) in request.data.items() if field in VALID_USER_FIELDS}
        user = get_user_model().objects.create_user(
            **user_data
        )
        return Response(UserSerializer(instance=user).data, status=status.HTTP_201_CREATED)
    else:
        return Response(serialized.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_user(request):
    if "user_name" not in request.data:
        return JsonResponse(
            {"error": "Enter user_name"}, status=status.HTTP_400_BAD_REQUEST
        )
    if "password" not in request.data:
        return JsonResponse(
            {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = User.objects.get(username__exact=request.data['user_name'], is_active=True)
        if user is not None and user.check_password(request.data['password']) == True:
            token = Token.objects.filter(user=user)
            if len(token) != 0:
                token.delete()
            login(request, user)
            userData = UserSerializer(user).data
            try:
                token = Token.objects.create(user=request.user)
                return JsonResponse(
                    {"token": token.key, "user": userData}, status=status.HTTP_200_OK
                )
            except IntegrityError:
                return JsonResponse(
                    {"error": "User is already logged in"}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return JsonResponse(
                {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
            )
    except User.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def delete_user(request):
    print(request.META['HTTP_AUTHORIZATION'])
    print(request.user)
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    try:
        token = Token.objects.get(key=token[1])
        user = token.user
        token.delete()
        userData = User.objects.get(id=user.id)
        userData.is_active = False
        userData.save()
        logout(request)
        # print(request.META['HTTP_AUTHORIZATION'])
        # token = request.META['HTTP_AUTHORIZATION'].split(' ')
        # user = Token.objects.get(key=token[1]).user
        return JsonResponse(
            {"data": "Deleted account and logged out the user successfully"}, status=status.HTTP_200_OK
        )
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as error:
        return JsonResponse(
            {"error": error}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_user_data(request):
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    try:
        # print(request.META['HTTP_AUTHORIZATION'])
        # token = request.META['HTTP_AUTHORIZATION'].split(' ')
        user = Token.objects.get(key=token[1]).user
        return JsonResponse(
            {"data": UserSerializer(user).data}, status=status.HTTP_200_OK
        )
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as error:
        return JsonResponse(
            {"error": error}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['PUT'])
@authentication_classes((TokenAuthentication,))
def change_password(request):
    if "current_password" not in request.data:
        return JsonResponse(
            {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
        )
    if "password" not in request.data:
        return JsonResponse(
            {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
        )
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    try:
        user = Token.objects.get(key=token[1]).user
        if not user.check_password(request.data['current_password']):
            return JsonResponse(
                {"error": "Password entered is incorrect"}, status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(request.data['password'])
        user.save()
        return JsonResponse(
            {"data": UserSerializer(user).data}, status=status.HTTP_200_OK
        )
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as error:
        return JsonResponse(
            {"error": error}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['PUT'])
def forgot_password(request):
    if "email" not in request.data:
        return JsonResponse(
            {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
        )
    if "password" not in request.data:
        return JsonResponse(
            {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = User.objects.get(email=request.data['email'])
        user.set_password(request.data['password'])
        user.save()
        return JsonResponse(
            {"data": UserSerializer(user).data}, status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid email address"}, status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as error:
        return JsonResponse(
            {"error": error}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def delete_question(request):
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    if "id" not in request.data:
        return JsonResponse(
            {"error": "Enter question ID"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = Token.objects.get(key=token[1]).user
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
        )
    questionData = Question.objects.filter(id=request.data['id'])
    if len(questionData) == 0:
        return JsonResponse(
            {"error": "There is no question with this id"}, status=status.HTTP_401_UNAUTHORIZED
        )
    ques = QuestionSerializer(questionData[0], many=False).data
    if ques['user'] != user.id:
        return JsonResponse(
            {"error": "Cannot delete the question .The questions can only be deleted by the user who created"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    Question.objects.filter(id=request.data['id']).delete()
    return JsonResponse(
        {"question": "Question deleted sucessfully"}, status=status.HTTP_204_NO_CONTENT
    )


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def delete_category(request):
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    if "name" not in request.data:
        return JsonResponse(
            {"error": "Enter a valid category name"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = Token.objects.get(key=token[1]).user
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid User token "}, status=status.HTTP_401_UNAUTHORIZED
        )
    categoryData = Category.objects.filter(name=request.data['name'])
    if len(categoryData) == 0:
        return JsonResponse(
            {"error": "There is no category with this name"}, status=status.HTTP_401_UNAUTHORIZED
        )
    cat = CategorySerializer(categoryData[0], many=False).data
    if cat['user'] != user.id:
        return JsonResponse(
            {"error": "Cannot delete the category .It can only be deleted by the user who created"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    categoryData = Category.objects.get(name=request.data['name'])
    question = Question.objects.filter(category=categoryData)
    if len(question) != 0:
        return JsonResponse(
            {"error": "Cannot delete the category .Questions have refrence to this"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    ug = UserGames.objects.filter(category=categoryData)
    if len(ug) != 0:
        return JsonResponse(
            {"error": "Cannot delete the category .Some players have played the game"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    game = Game.objects.filter(category=categoryData)
    if len(game) != 0:
        return JsonResponse(
            {"error": "Cannot delete the category .Games are created"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    Category.objects.filter(name=request.data['name']).delete()
    return JsonResponse(
        {"category": "Category name deleted sucessfully"}, status=status.HTTP_204_NO_CONTENT
    )


@api_view(['PUT'])
@authentication_classes((TokenAuthentication,))
def update_category(request):
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    if "name" not in request.data:
        return JsonResponse(
            {"error": "Enter a valid category name"}, status=status.HTTP_400_BAD_REQUEST
        )
    if "newname" not in request.data:
        return JsonResponse(
            {"error": "Enter a valid category name"}, status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = Token.objects.get(key=token[1]).user
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid User token "}, status=status.HTTP_401_UNAUTHORIZED
        )
    categoryData = Category.objects.filter(name=request.data['name'])
    if len(categoryData) == 0:
        return JsonResponse(
            {"error": "There is no category with this name"}, status=status.HTTP_401_UNAUTHORIZED
        )
    cat = CategorySerializer(categoryData[0], many=False).data
    if cat['user'] != user.id:
        return JsonResponse(
            {"error": "Cannot delete the category .It can only be deleted by the user who created"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    cat = Category.objects.get(name=request.data['name'])
    cat.name = request.data['newname']
    cat.save()
    categoryData = Category.objects.get(name=request.data['name'])
    Question.objects.filter(category=categoryData).update(category=cat)
    UserGames.objects.filter(category=categoryData).update(category=cat)
    Game.objects.filter(category=categoryData).update(category=cat)
    Category.objects.filter(name=request.data['name']).delete()
    return JsonResponse(
        {"category": "Category name updated sucessfully"}, status=status.HTTP_201_CREATED
    )

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def opendb(request):
    # User Authorization to ensure only user who adds questions can delete/edit them
    token = request.META['HTTP_AUTHORIZATION'].split(' ')
    try:
        user = Token.objects.get(key=token[1]).user
    except Token.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
        )
    data = requests.get(url=request.data['url']).json()  # takes in data from url and displays json response
    questionsList = []  # option list
    errorList = []
    for question in data['results']:  # goes through option list (LOOP 2)
        optionsList = html.unescape(question['incorrect_answers'])
        optionsList.append(question['correct_answer'])
        random.shuffle(optionsList)
        try:
            index = optionsList.index(question['correct_answer'])
        except Exception as error:
            print(error)
        optionsListData = []
        for option in optionsList:
            optionData = Options.objects.filter(option=option)
            if len(optionData) == 0:
                option = {
                    'option': option
                }
                serializer = OptionsSerializer(data=option, many=False)
                if serializer.is_valid():
                    serializer.save()
            else:
                serializer = OptionsSerializer(optionData[0], many=False)
            optionsListData.append(serializer.data['option'])
        escapedquestion = question['question']
        unescapedquestion = html.unescape(escapedquestion).replace("\\","")
        question = {
            "question": unescapedquestion,
            "category": question['category'],
            "options": optionsListData,
            "user": user.id,
            "answer": html.unescape(optionsListData[index])
        }
        serializer = QuestionSerializer(data=question)
        if serializer.is_valid():
            serializer.save()
            questionsList.append(serializer.data)
        else:
            errorList.append({'error':serializer.errors,'question':html.unescape(question['question'])})
    if len(errorList) != 0:
        return JsonResponse({
            "data": questionsList,
            'error': errorList
        }, status=status.HTTP_200_OK)
    else:
        return JsonResponse({
            "data": questionsList
        }, status=status.HTTP_200_OK)

class UserAPIs(viewsets.GenericViewSet):
    """
        Handling user api that are dont need authentication
    """
    serializer_class = UserSerializer

    permission_classes = (AllowAny,)

    @action(detail=False, methods=['post'])
    def register(self, request):
        """
            Registering user
            User needs to enter username,email,password
        """
        if "username" not in request.data:
            return JsonResponse(
                {"error": "Enter username"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "email" not in request.data:
            return JsonResponse(
                {"error": "Enter email"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "password" not in request.data:
            return JsonResponse(
                {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
            )
        # Validating if the username already exists
        user = User.objects.filter(username=request.data['username'])
        if len(user) != 0:
            return JsonResponse(
                {"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST
            )
        # Validating if the email already exists
        user = User.objects.filter(email=request.data['email'])
        if len(user) != 0:
            return JsonResponse(
                {"error": "Email address already exists"}, status=status.HTTP_400_BAD_REQUEST
            )
        # Checking if all the valid fields are entere
        VALID_USER_FIELDS = [f.name for f in get_user_model()._meta.fields]
        # Creating user
        serialized = UserSerializer(data=request.data)
        if serialized.is_valid():
            user_data = {field: data for (field, data) in request.data.items() if field in VALID_USER_FIELDS}
            user = get_user_model().objects.create_user(
                **user_data
            )
            return Response(UserSerializer(instance=user).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serialized.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
                   Login
                   User needs to enter username,password
        """
        if "username" not in request.data:
            return JsonResponse(
                {"error": "Enter user_name"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "password" not in request.data:
            return JsonResponse(
                {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # Checking  if the user exists using the username and also checking if the user is active
            # Here the user is inactive if the user deleted his/her account
            user = User.objects.get(username__exact=request.data['username'], is_active=True)
            # If the username matches in any of the user doc
            # checking if the passwords are matching
            if user is not None and user.check_password(request.data['password']) == True:
                # deleting the token if the user has already one
                token = Token.objects.filter(user=user)
                if len(token) != 0:
                    token.delete()
                #  authenticating the user
                login(request, user)
                userData = UserSerializer(user).data
                try:
                    # creating the token and giving it to user
                    token = Token.objects.create(user=request.user)
                    return JsonResponse(
                        {"token": token.key, "user": userData}, status=status.HTTP_200_OK
                    )
                except IntegrityError:
                    return JsonResponse(
                        {"error": "User is already logged in"}, status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return JsonResponse(
                    {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['put'])
    def forgot_password(self, request):
        """
                          Forgot password
                          User needs to enter email,password
               """
        if "email" not in request.data:
            return JsonResponse(
                {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "password" not in request.data:
            return JsonResponse(
                {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # checking if the user exists with the given email id
            user = User.objects.get(email=request.data['email'])
            # setting the password
            user.set_password(request.data['password'])
            user.save()
            return JsonResponse(
                {"data": UserSerializer(user).data}, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            # if the user does not exist
            return JsonResponse(
                {"error": "Invalid email address"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as error:
            return JsonResponse(
                {"error": error}, status=status.HTTP_400_BAD_REQUEST
            )


class UserDetailsApi(viewsets.GenericViewSet):
    """
       Adding token authentication and permission classes
       Separated this from user api view since this needs authentication where as the user api dont need it
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = (IsAuthenticated,)

    serializer_class = UserSerializer

    def get_serializer_class(self):
        # TODO need to have a look if the other way is possible of separating serializers (since here there is only
        #  one put api it works fine)
        if self.request.method == 'PUT':
            # for now we have only one put api i.e reset password api which is accepting password along with current
            # password
            return ResetUserPasswordSerializer
        # for info and delete apis
        return UserSerializer

    @action(detail=False, methods=['get'])
    def info(self, request):
        """
            Getting current logged in user information
        """
        # getting  token from HTTP_AUTHORIZATION and removing the bearer part from it
        token = request.META['HTTP_AUTHORIZATION'].split(' ')
        try:
            # getting user info from token
            user = Token.objects.get(key=token[1]).user
            # the user info here is  retreived from token
            return JsonResponse(
                {"data": UserSerializer(user).data}, status=status.HTTP_200_OK
            )
        except Token.DoesNotExist:
            # if this is not a valid token
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as error:
            return JsonResponse(
                {"error": error}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['delete'])
    def delete(self, request):
        """
            For deleting a user account the steps we followed are :
            1)Making the user inactive
            2)Deleting the current user token
            2)logging out the user
        """
        # getting  token from HTTP_AUTHORIZATION and removing the bearer part from it
        token = request.META['HTTP_AUTHORIZATION'].split(' ')
        try:
            # getting token
            token = Token.objects.get(key=token[1])
            # getting user info from token
            user = token.user
            # deleting token
            token.delete()
            userData = User.objects.get(id=user.id)
            # making user inactive
            userData.is_active = False
            userData.save()
            # logging out the user
            logout(request)
            return JsonResponse(
                {"data": "Deleted account and logged out the user successfully"}, status=status.HTTP_200_OK
            )
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as error:
            return JsonResponse(
                {"error": error}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['put'])
    def reset_password(self, request):
        """
            Need to send the current password that the user is having along with the password the user want to change
        """
        if "current_password" not in request.data:
            return JsonResponse(
                {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "password" not in request.data:
            return JsonResponse(
                {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
            )
        # getting  token from HTTP_AUTHORIZATION and removing the bearer part from it
        token = request.META['HTTP_AUTHORIZATION'].split(' ')
        try:
            # getting user info from token
            user = Token.objects.get(key=token[1]).user
            # checking if the current password entered by the user is correct
            if not user.check_password(request.data['current_password']):
                return JsonResponse(
                    {"error": "Password entered is incorrect"}, status=status.HTTP_400_BAD_REQUEST
                )
            # setting a new password if the current password is matching
            user.set_password(request.data['password'])
            user.save()
            return JsonResponse(
                {"data": UserSerializer(user).data}, status=status.HTTP_200_OK
            )
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as error:
            return JsonResponse(
                {"error": error}, status=status.HTTP_400_BAD_REQUEST
            )


class GameCode(viewsets.GenericViewSet):
    serializer_class = GameSerializer

    permission_classes= (AllowAny,)

    def create(self, request):
        """
            Generates game code given a user name and category.
            While creating a game for a particular user  we also make sure the category exists
        """
        # checking if the required fields user name and category are entered
        if "user_name" not in request.data:
            return JsonResponse(
                {"error": "Enter user_name"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "category" not in request.data:
            return JsonResponse(
                {"error": "Enter category"}, status=status.HTTP_400_BAD_REQUEST
            )
        # checking if the category exists
        category = Category.objects.filter(name=request.data['category'])
        print(category)
        if len(category) == 0:
            return JsonResponse(
                {"error": "Category does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        # creating game code given a username and category
        game_serializer = GameSerializer(data=request.data)

        if not game_serializer.is_valid():
            return JsonResponse(game_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        game_serializer.save()

        return JsonResponse(game_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='end/(?P<game_code>[^/.]+)')
    def end(self, request, *args, **kwargs):
        """
             Ends the game
        """
        try:
            # Getting the game code from the query params
            game_code = int(kwargs['game_code'])
            game = Game.objects.get(game_code=game_code)
            # Updating the game active status to false
            game.active = False
            game.save()
            # Serializing the given game code data
            gameData = GameSerializer(game).data
            return JsonResponse({
                "data": gameData
            }, status=status.HTTP_200_OK)
        except Game.DoesNotExist:
            return JsonResponse({
                "error": "Invalid game code"
            }, status=status.HTTP_400_BAD_REQUEST)
