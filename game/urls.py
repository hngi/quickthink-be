from django.conf.urls import url
from django.urls import path, include
from rest_framework import routers

from game.views import (
    UserDetailsApi,
    UserAPIs,
    GameCode,
    Category,
    Question,
    UserGame,
)

userRouter = routers.DefaultRouter()
userRouter.register(r"", UserAPIs, basename="user")
userRouter.register(r"", UserDetailsApi, basename="userDetails")

router = routers.DefaultRouter()
router.register(r"", GameCode, basename="game")

QuestionRouter = routers.DefaultRouter()
QuestionRouter.register(r"", Question, basename="questions")

categoryRouter = routers.DefaultRouter()
categoryRouter.register(r"", Category, basename="game")

userGameRouter = routers.DefaultRouter()
userGameRouter.register(r"", UserGame, basename="userGame")

urlpatterns = [
    url(r"^game/", include(router.urls)),
    url(r"^user/", include(userRouter.urls)),
    url(r"^category/", include(categoryRouter.urls)),
    url(r"^question/", include(QuestionRouter.urls)),
    url(r"^usergame/", include(QuestionRouter.urls)),
]
