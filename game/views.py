import html
import random
from rest_framework import status, generics
import requests
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse

# Create your views here.
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
    action,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from django.db import IntegrityError

from quizzes.pagination.paginate import StandardResultsSetPagination
from .models import Game, Question, UserGames, Options, Category, ContactUs, Newsletter

from .serializers import (
    GameSerializer,
    QuestionSerializer,
    OptionsSerializer,
    UserGamesSerializer,
    CategorySerializer,
    UserSerializer,
    ResetUserPasswordSerializer,
    CategoryUpdateSerializer,
    NewsletterSerializer,
    ContactUsSerializer,
)

from rest_framework.authtoken.models import Token


class UserGameView(viewsets.GenericViewSet):
    serializer_class = UserGamesSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return None

    @action(detail=False, methods=["get"], url_path="category/list")
    def get_all_category(self, request):
        try:
            data = Category.objects.all()
            question = CategorySerializer(data, many=True).data
            return JsonResponse({"data": question}, status=status.HTTP_200_OK)
        except Exception as error:
            return JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="play")
    def check_if_game_code_isValid(self, request):
        if "game_code" not in request.data:
            return JsonResponse(
                {"error": "Enter game_code"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "user_name" not in request.data:
            return JsonResponse(
                {"error": "Enter user_name"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            game = Game.objects.get(game_code=request.data["game_code"])
            gameData = GameSerializer(game).data
            if gameData["user_name"] == request.data["user_name"]:
                return JsonResponse(
                    {"error": "Game creator cannot play the game"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            if gameData["active"]:
                ug = UserGames.objects.filter(
                    game_code=request.data["game_code"],
                    user_name=request.data["user_name"],
                )
                if len(ug) != 0:
                    return JsonResponse(
                        {"error": "User name is already taken"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
                qList = Question.objects.filter(
                    category=gameData["category"]
                ).values_list("id", flat=True)
                qRand = random.sample(list(qList), min(len(qList), 10))
                questions = Question.objects.filter(id__in=qRand)
                questionData = QuestionSerializer(questions, many=True).data
                questions = []
                for question in questionData:
                    options = []
                    for option in question["options"]:
                        optionQuery = Options.objects.get(option=option)
                        optionData = OptionsSerializer(optionQuery, many=False).data
                        options.append(optionData["option"])
                    question["options"] = options
                    questions.append(question)
                serializer = UserGamesSerializer(
                    data={
                        "game_code": request.data["game_code"],
                        "category": gameData["category"],
                        "user_name": request.data["user_name"],
                    }
                )
                if serializer.is_valid():
                    serializer.save()
                    return JsonResponse(
                        {
                            "data": {
                                "questions": questions,
                                "usergameData": serializer.data,
                            }
                        },
                        status=status.HTTP_200_OK,
                    )
                return JsonResponse(
                    {"error": serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            else:
                return JsonResponse(
                    {"error": "Game code is expired"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Game.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid game code"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as error:
            return
            JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="valid")
    def check_if_user_can_play_game_code(self, request):
        if "game_code" not in request.data:
            return JsonResponse(
                {"error": "Enter game_code"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "user_name" not in request.data:
            return JsonResponse(
                {"error": "Enter user_name"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            game = Game.objects.get(game_code=request.data["game_code"])
            gameData = GameSerializer(game).data
            if gameData["user_name"] == request.data["user_name"]:
                return JsonResponse(
                    {"error": "Game creator cannot play the game"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            if gameData["active"]:
                ug = UserGames.objects.filter(
                    game_code=request.data["game_code"],
                    user_name=request.data["user_name"],
                )
                if len(ug) != 0:
                    return JsonResponse(
                        {"error": "User name is already taken "},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
                return JsonResponse(
                    {"data": "User can play game"}, status=status.HTTP_200_OK
                )
            else:
                return JsonResponse(
                    {"error": "Game code is expired"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Game.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid game code"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as error:
            return
            JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(
        detail=False,
        methods=["post"],
        url_path="score/increment/(?P<user_game_id>[^/.]+)",
    )
    def update_score_usergame(self, request, user_game_id):
        try:
            ug = UserGames.objects.get(id=user_game_id)
            ug.score = ug.score + 1
            ug.save()
            # ug = UserGames.objects.filter(id=request.data['user_game_id']).update(score=F['score'] + 1)
            ugSerializer = UserGamesSerializer(ug, many=False).data
            return JsonResponse({"data": ugSerializer}, status=status.HTTP_200_OK)
        except UserGames.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid user game id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as error:
            return JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(
        detail=False,
        methods=["post"],
        url_path="score/increment/(?P<user_game_id>[^/.]+)/(?P<no_answers_crct>[^/.]+)",
    )
    def update_score_count_usergame(self, request, *args, **kwargs):
        try:
            ug = UserGames.objects.get(id=kwargs["user_game_id"])
            ug.score = ug.score + int(kwargs["no_answers_crct"])
            ug.save()
            # ug = UserGames.objects.filter(id=request.data['user_game_id']).update(score=F['score'] + 1)
            ugSerializer = UserGamesSerializer(ug, many=False).data
            return JsonResponse({"data": ugSerializer}, status=status.HTTP_200_OK)
        except UserGames.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid user game_id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as error:
            return JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path='leaderboard/inf/(?P<n>[^/.]+)')
    def get_leader_board(self, request, n=None):
        try:
            if n is not None:
                n = int(n)
            else:
                n = 10
            options = {}
            if "id" in request.data:
                options['id__gt'] = request.data['id']
            if "score" in request.data:
                options['score__lte'] = request.data['score']
            data = UserGames.objects.filter(**options
                                            ).order_by("-score", "id")[:n]

            userGames = UserGamesSerializer(data, many=True).data
            return JsonResponse({"data": userGames}, status=status.HTTP_200_OK)
        except Exception as error:
            return JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(
        detail=False,
        methods=["post"],
        url_path="leaderboard/game/(?P<game_code>[^/.]+)/(?P<n>[^/.]+)",
    )
    def get_leader_board_game_code(self, request, game_code, n):
        try:
            data = UserGames.objects.filter(game_code=game_code).order_by("-score")
            if n is not None:
                n = int(n)
                data = data[:n]
            userGames = UserGamesSerializer(data, many=True).data
            return JsonResponse({"data": userGames}, status=status.HTTP_200_OK)
        except Exception as error:
            return JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserAPIs(viewsets.GenericViewSet):
    """
        Handling user api that are dont need authentication
    """

    serializer_class = UserSerializer

    permission_classes = (AllowAny,)

    def get_queryset(self):
        return None

    @action(detail=False, methods=["post"])
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
        user = User.objects.filter(username=request.data["username"])
        if len(user) != 0:
            return JsonResponse(
                {"error": "Username already exists"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        # Validating if the email already exists
        user = User.objects.filter(email=request.data["email"])
        if len(user) != 0:
            return JsonResponse(
                {"error": "Email address already exists"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # Checking if all the valid fields are entere
        VALID_USER_FIELDS = [f.name for f in get_user_model()._meta.fields]
        # Creating user
        serialized = UserSerializer(data=request.data)
        if serialized.is_valid():
            user_data = {
                field: data
                for (field, data) in request.data.items()
                if field in VALID_USER_FIELDS
            }
            user = get_user_model().objects.create_user(**user_data)
            return Response(
                UserSerializer(instance=user).data, status=status.HTTP_200_OK
            )
        else:
            return Response(serialized.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def login(self, request):
        """
                   Login
                   User needs to enter username,password
        """
        if "username" not in request.data:
            return JsonResponse(
                {"error": "Enter username"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "password" not in request.data:
            return JsonResponse(
                {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # Checking  if the user exists using the username and also checking if the user is active
            # Here the user is inactive if the user deleted his/her account
            user = User.objects.get(
                username__exact=request.data["username"], is_active=True
            )
            # If the username matches in any of the user doc
            # checking if the passwords are matching
            if (
                    user is not None
                    and user.check_password(request.data["password"]) == True
            ):
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
                        {"token": token.key, "user": userData},
                        status=status.HTTP_200_OK,
                    )
                except IntegrityError:
                    return JsonResponse(
                        {"error": "User is already logged in"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                return JsonResponse(
                    {"error": "Invalid credentials"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except User.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid credentials"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["put"])
    def forgot_password(self, request):
        """
                          Forgot password
                          User needs to enter email,password
               """
        if "email" not in request.data:
            return JsonResponse(
                {"error": "Enter email"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "password" not in request.data:
            return JsonResponse(
                {"error": "Enter password"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # checking if the user exists with the given email id
            user = User.objects.get(email=request.data["email"])
            # setting the password
            user.set_password(request.data["password"])
            user.save()
            return JsonResponse(
                {"data": UserSerializer(user).data}, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            # if the user does not exist
            return JsonResponse(
                {"error": "Invalid email address"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as error:
            return JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailsApi(viewsets.GenericViewSet):
    """
       Adding token authentication and permission classes
       Separated this from user api view since this needs authentication where as the user api dont need it
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = (IsAuthenticated,)

    serializer_class = UserSerializer

    def get_queryset(self):
        return None

    def get_serializer_class(self):
        # TODO need to have a look if the other way is possible of separating serializers (since here there is only
        #  one put api it works fine)
        if self.request.method == "PUT":
            # for now we have only one put api i.e reset password api which is accepting password along with current
            # password
            return ResetUserPasswordSerializer
        # for info and delete apis
        return UserSerializer

    @action(detail=False, methods=["get"])
    def info(self, request):
        """
            Getting current logged in user information
        """
        # getting  token from HTTP_AUTHORIZATION and removing the bearer part from it
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
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
            return JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["delete"])
    def delete(self, request):
        """
            For deleting a user account the steps we followed are :
            1)Making the user inactive
            2)Deleting the current user token
            2)logging out the user
        """
        # getting  token from HTTP_AUTHORIZATION and removing the bearer part from it
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
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
                {"data": "Deleted account and logged out the user successfully"},
                status=status.HTTP_200_OK,
            )
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as error:
            return JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["put"])
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
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
        try:
            # getting user info from token
            user = Token.objects.get(key=token[1]).user
            # checking if the current password entered by the user is correct
            if not user.check_password(request.data["current_password"]):
                return JsonResponse(
                    {"error": "Password entered is incorrect"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            # setting a new password if the current password is matching
            user.set_password(request.data["password"])
            user.save()
            return JsonResponse(
                {"data": UserSerializer(user).data}, status=status.HTTP_200_OK
            )
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as error:
            return JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuestionView(viewsets.GenericViewSet):
    """
    Handles all Question Operations that require user token.
    """

    serializer_class = QuestionSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["GET"], url_path="list/user")
    def get_questions_user(self, request):
        # Gets token from user
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
        try:
            user = Token.objects.get(key=token[1]).user
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        # Filters questions by user ID to get all question details created by that user
        questions = Question.objects.filter(user=user.id)
        questionData = QuestionSerializer(questions, many=True).data
        questions = []
        for question in questionData:
            options = []
            for option in question["options"]:
                optionQuery = Options.objects.get(option=option)
                optionData = OptionsSerializer(optionQuery, many=False).data
                options.append(optionData["option"])
            question["options"] = options
            questions.append(question)
        return JsonResponse({"data": questions}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path="create")
    def create_question(self, request):
        """
        Creates a question given the category already exists
        Requires AUTH token
        """
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
        try:
            user = Token.objects.get(key=token[1]).user
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        # Exception handling below
        question = request.data.get("Question")
        cats = Category.objects.filter(name=question["category"])
        if len(cats) == 0:
            return JsonResponse(
                {"error": "Enter valid category"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        if "answer" not in question:
            return JsonResponse(

                {"error": "There is no answer "},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,

            )
        try:
            index = question["options"].index(question["answer"])
        except Exception as error:
            return JsonResponse(
                {"error": "There is no option with the answer "},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        category = CategorySerializer(cats, many=True).data
        options = question["options"]
        if len(options) != 4:
            return JsonResponse(
                {"error": "There should be exaclty 4 options"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        optionsList = []
        for (
                option
        ) in options:  # creates an option list and inserts all options into the list
            optionData = Options.objects.filter(option=option)
            if len(optionData) == 0:
                option = {"option": option}
                # save options using option serializers
                serializer = OptionsSerializer(data=option, many=False)
                if serializer.is_valid():
                    serializer.save()
            else:
                serializer = OptionsSerializer(optionData[0], many=False)
            optionsList.append(serializer.data["option"])
        question = {
            "question": question["question"],  # takes quesion from user
            "category": category[0][
                "name"
            ],  # takes category from existing category (create category endpoint)
            "options": optionsList,
            "user": user.id,  # takes user id from pre-existing user model
            "answer": optionsList[
                index
            ],  # takes the correct answer from the optionsList
        }
        serializer = QuestionSerializer(data=question)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({"data": serializer.data}, status=status.HTTP_200_OK)
        return JsonResponse(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["PUT"], url_path="update")
    def update_question(self, request):
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
        try:
            user = Token.objects.get(key=token[1]).user
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        question = request.data.get("Question")
        questionData = Question.objects.filter(id=question["id"])

        if len(questionData) == 0:
            return JsonResponse(
                {"error": "There is no question with this id"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        ques = QuestionSerializer(questionData[0], many=False).data
        print(ques)
        if ques["user"] != user.id:
            return JsonResponse(
                {
                    "error": "Cannot update the question .The questions can only be updated by the user who created"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        cats = Category.objects.filter(name=question["category"])
        if len(cats) == 0:
            return JsonResponse(
                {"error": "Enter valid category"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        if "answer" not in question:
            return JsonResponse(
                {"error": "There is no answer "}, status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            index = question["options"].index(question["answer"])
        except Exception as error:
            return JsonResponse(
                {"error": "There is no option with the answer "},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        category = CategorySerializer(cats, many=True).data
        options = question["options"]
        if len(options) != 4:
            return JsonResponse(
                {"error": "There should be exaclty 4 options"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        optionsList = []
        for option in options:
            optionData = Options.objects.filter(option=option)
            if len(optionData) == 0:
                option = {"option": option}
                serializer = OptionsSerializer(data=option, many=False)
                if serializer.is_valid():
                    serializer.save()
            else:
                serializer = OptionsSerializer(optionData[0], many=False)
            optionsList.append(serializer.data["option"])

        questionData = Question.objects.get(id=question["id"])
        questionData.question = question["question"]
        questionData.category = Category.objects.get(name=category[0]["name"])
        questionData.options.set(optionsList)
        questionData.user = user
        questionData.answer = Options.objects.get(option=optionsList[index])
        questionData.save()
        serializer = QuestionSerializer(questionData)
        return JsonResponse({"data": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="list")
    def get_questions(self, request):
        """
        Gets ALL the questions in the database displayed by all users.

        """
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
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
            for option in question["options"]:
                optionQuery = Options.objects.get(option=option)
                optionData = OptionsSerializer(optionQuery, many=False).data
                options.append(optionData["option"])
            question["options"] = options
            questions.append(question)
        return JsonResponse({"data": questions}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path="opendb")
    def opendb(self, request):
        """
        This endpoint populates the database with questions from the Trivia API (opendb)
        It Saves to the same models so these questions can be used exactly like the create_question endpoint (with user_id and everything)
        Hint: create category first
        """
        # User Authorization to ensure only user who adds questions can delete/edit them
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
        try:
            user = Token.objects.get(key=token[1]).user
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        data = requests.get(
            url=request.data["url"]
        ).json()  # takes in data from url and displays json response
        questionsList = []  # option list
        errorList = []
        for question in data["results"]:  # goes through option list (LOOP 2)
            optionsList = html.unescape(question["incorrect_answers"])
            optionsList.append(question["correct_answer"])
            random.shuffle(
                optionsList
            )  # adds all answers to options and randomizes it.
            try:
                index = optionsList.index(
                    question["correct_answer"]
                )  # appends the correct answer to options list
            except Exception as error:
                print(error)
            optionsListData = []
            for option in optionsList:
                optionData = Options.objects.filter(option=option)
                if len(optionData) == 0:
                    option = {"option": option}
                    serializer = OptionsSerializer(data=option, many=False)
                    if serializer.is_valid():
                        serializer.save()
                else:
                    serializer = OptionsSerializer(optionData[0], many=False)
                optionsListData.append(serializer.data["option"])
            # fixed HTML encoding errors
            escapedquestion = question["question"]
            unescapedquestion = html.unescape(escapedquestion).replace("\\", "")
            question = {
                "question": unescapedquestion,
                "category": question["category"],
                "options": optionsListData,
                "user": user.id,
                "answer": html.unescape(optionsListData[index]),
            }
            serializer = QuestionSerializer(data=question)
            if serializer.is_valid():
                serializer.save()
                questionsList.append(serializer.data)
            else:
                errorList.append(
                    {
                        "error": serializer.errors,
                        "question": html.unescape(question["question"]),
                    }
                )
        if len(errorList) != 0:
            return JsonResponse(
                {"data": questionsList, "error": errorList}, status=status.HTTP_200_OK
            )
        else:
            return JsonResponse({"data": questionsList}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path="delete")
    def delete_question(self, request):
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
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
        questionData = Question.objects.filter(id=request.data["id"])
        if len(questionData) == 0:
            return JsonResponse(
                {"error": "There is no question with this id"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        ques = QuestionSerializer(questionData[0], many=False).data
        if ques["user"] != user.id:
            return JsonResponse(
                {
                    "error": "Cannot delete the question .The questions can only be deleted by the user who created"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        Question.objects.filter(id=request.data["id"]).delete()
        return JsonResponse(
            {"question": "Question deleted sucessfully"},
            status=status.HTTP_200_OK,
        )


class GameCode(viewsets.GenericViewSet):
    serializer_class = GameSerializer

    permission_classes = (AllowAny,)

    def get_queryset(self):
        return None

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
        category = Category.objects.filter(name=request.data["category"])
        print(category)
        if len(category) == 0:
            return JsonResponse(
                {"error": "Category does not exist"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        data = {
            "category": request.data["category"],
            "user_name": request.data["user_name"],
            "active": True,
        }
        # creating game code given a username and category
        game_serializer = GameSerializer(data=data)

        if not game_serializer.is_valid():
            return JsonResponse(
                game_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        game_serializer.save()

        return JsonResponse(game_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"], url_path="end/(?P<game_code>[^/.]+)")
    def end(self, request, *args, **kwargs):
        """
             Ends the game
        """
        try:
            # Getting the game code from the query params
            game_code = int(kwargs["game_code"])
            game = Game.objects.get(game_code=game_code)
            # Updating the game active status to false
            game.active = False
            game.save()
            # Serializing the given game code data
            gameData = GameSerializer(game).data
            return JsonResponse({"data": gameData}, status=status.HTTP_200_OK)
        except Game.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid game code"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryView(viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return None

    def get_serializer_class(self):
        # TODO need to have a look if the other way is possible of separating serializers (since here there is only
        #  one put api it works fine)
        if self.request.method == "PUT":
            # for now we have only one put api i.e reset password api which is accepting password along with current
            # password
            return CategoryUpdateSerializer
        # for info and delete apis
        return CategorySerializer

    @action(detail=False, methods=["post"], url_path="create")
    def create_category(self, request):
        """
            Create Category
        """
        if "name" not in request.data:
            return JsonResponse(
                {"error": "Enter category name"}, status=status.HTTP_400_BAD_REQUEST
            )
        print(request.META["HTTP_AUTHORIZATION"].split(" "))
        # getting  token from HTTP_AUTHORIZATION and removing the bearer part from it
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
        try:
            # getting user info from token
            user = Token.objects.get(key=token[1]).user

        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
        # Creating category with name and user
        print(user.id)
        data = {"name": request.data["name"], "user": user.id}
        print(data)
        createcategory = CategorySerializer(data=data)
        if createcategory.is_valid():
            createcategory.save()
            print(createcategory.data)
            return Response(createcategory.data, status=status.HTTP_200_OK)
        return Response(createcategory.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["put"], url_path="update")
    def update_category(self, request):
        """
            Update Category
        """
        # getting  token from HTTP_AUTHORIZATION and removing the bearer part from it
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
        if "name" not in request.data:
            return JsonResponse(
                {"error": "Enter a valid category name"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if "newname" not in request.data:
            return JsonResponse(
                {"error": "Enter a valid category name"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            # getting user info from token
            user = Token.objects.get(key=token[1]).user
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid User token "}, status=status.HTTP_401_UNAUTHORIZED
            )
        # check if the given category exists
        categoryData = Category.objects.filter(name=request.data["name"])
        if len(categoryData) == 0:
            return JsonResponse(
                {"error": "There is no category with this name"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        cat = CategorySerializer(categoryData[0], many=False).data
        # checking if this category is created by authenticated user only
        if cat["user"] != user.id:
            return JsonResponse(
                {
                    "error": "Cannot delete the category .It can only be deleted by the user who created"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # updating the category with new name
        # here on updating the category with new name it creates a new one without modifying the current one
        # since we are changing the primary key
        cat = Category.objects.get(name=request.data["name"])
        cat.name = request.data["newname"]
        cat.save()
        categoryData = Category.objects.get(name=request.data["name"])
        # updating the question,usergames,game with new category name
        Question.objects.filter(category=categoryData).update(category=cat)
        UserGames.objects.filter(category=categoryData).update(category=cat)
        Game.objects.filter(category=categoryData).update(category=cat)
        # deleting the previous category name
        Category.objects.filter(name=request.data["name"]).delete()
        return JsonResponse(
            {"category": "Category name updated sucessfully"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["delete"], url_path="delete/(?P<category>[^/.]+)")
    def delete_category(self, request, *args, **kwargs):
        """
                 Deleting category
             """
        # getting  token from HTTP_AUTHORIZATION and removing the bearer part from it
        token = request.META["HTTP_AUTHORIZATION"].split(" ")
        # retreiving category name
        name = kwargs["category"]
        try:
            # getting user info
            user = Token.objects.get(key=token[1]).user
        except Token.DoesNotExist:
            return JsonResponse(
                {"error": "Invalid User token "}, status=status.HTTP_401_UNAUTHORIZED
            )
        # checking if the caetgory exists
        categoryData = Category.objects.filter(name=name)
        if len(categoryData) == 0:
            return JsonResponse(
                {"error": "There is no category with this name"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        cat = CategorySerializer(categoryData[0], many=False).data
        # checking if the category is created by the user who is logged in
        if cat["user"] != user.id:
            return JsonResponse(
                {
                    "error": "Cannot delete the category .It can only be deleted by the user who created"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        categoryData = Category.objects.get(name=name)
        # checking if the questions are created in this category
        question = Question.objects.filter(category=categoryData)
        if len(question) != 0:
            return JsonResponse(
                {
                    "error": "Cannot delete the category .Questions have refrence to this"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        # checking if the any games are played by users in this category
        ug = UserGames.objects.filter(category=categoryData)
        if len(ug) != 0:
            return JsonResponse(
                {
                    "error": "Cannot delete the category .Some players have played the game"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # checking if the any game is created in this category
        game = Game.objects.filter(category=categoryData)
        if len(game) != 0:
            return JsonResponse(
                {"error": "Cannot delete the category .Games are created"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        # if all the above conditions are applied the category then  delete category
        Category.objects.filter(name=name).delete()
        return JsonResponse(
            {"category": "Category name deleted sucessfully"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="list/user")
    def category_list(self, request):
        """
            Getting categories list that are created by logged in user
        """
        try:
            # getting  token from HTTP_AUTHORIZATION and removing the bearer part from it
            token = request.META["HTTP_AUTHORIZATION"].split(" ")
            try:
                # getting user info
                user = Token.objects.get(key=token[1]).user
            except Token.DoesNotExist:
                return JsonResponse(
                    {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
                )
            # getting category list by user id
            data = Category.objects.filter(user=user.id)
            question = CategorySerializer(data, many=True).data
            return JsonResponse({"data": question}, status=status.HTTP_200_OK)
        except Exception as error:
            return JsonResponse({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NewsletterView(viewsets.GenericViewSet):
    serializer_class = NewsletterSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return None

    @action(detail=False, methods=["post"], url_path="subscribe")
    def add_to_newsletter(self, request):
        if "email" not in request.data:
            return JsonResponse(
                {"error": "Enter your email"}, status=status.HTTP_400_BAD_REQUEST
            )
        is_subscribed = len(Newsletter.objects.filter(email=request.data["email"])) != 0
        if is_subscribed:
            return JsonResponse(
                {"error": "You have already subscribed to our Newsletter"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        newsletter = Newsletter(email=request.data["email"])
        newsletter.save()
        newsletterSerializer = NewsletterSerializer(newsletter)
        return JsonResponse(
            {"data": newsletterSerializer.data, "message": "Successfully subscribed", },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["delete"], url_path="unsubscribe")
    def unsubscribe_newsletter(self, request):
        if "email" not in request.data:
            return JsonResponse(
                {"error": "Please enter your email"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            newsletter = Newsletter.objects.get(email=request.data["email"])
        except Newsletter.DoesNotExist:
            return JsonResponse(
                {"error": "This email is not subscribed to the Newsletter"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        newsletter.delete()
        return JsonResponse(
            {"message": "Successfully unsubscribed"}, status=status.HTTP_200_OK,
        )


class ContactUsView(viewsets.GenericViewSet):
    serializer_class = ContactUsSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return None

    @action(detail=False, methods=["post"])
    def send_contact_info(self, request):
        if "email" not in request.data:
            return JsonResponse(
                {"error": "Please enter your email"}, status=status.HTTP_400_BAD_REQUEST
            )
        if "full_name" not in request.data:
            return JsonResponse(
                {"error": "Please enter your Full name"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if "message" not in request.data:
            return JsonResponse(
                {"error": "Please enter your message"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        contactUs = ContactUs(
            email=request.data["email"],
            full_name=request.data["full_name"],
            message=request.data["message"],
        )
        contactUs.save()
        return JsonResponse({"data": "Message sent"}, status=status.HTTP_200_OK)


class UserGameLeaderBoardView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    queryset = UserGames.objects.all().order_by("-score", "id")
    serializer_class = UserGamesSerializer
    pagination_class = StandardResultsSetPagination
