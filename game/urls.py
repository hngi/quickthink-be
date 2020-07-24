from django.conf.urls import url
from django.urls import path, include
from rest_framework import routers

from .views import (
    UserDetailsApi,
    UserAPIs,
    GameCode,
    CategoryView,
    QuestionView,
    UserGameView,
    NewsletterView,
    ContactUsView,
)

userRouter = routers.DefaultRouter()
userRouter.register(r"", UserAPIs, basename="user")
userRouter.register(r"", UserDetailsApi, basename="userDetails")

router = routers.DefaultRouter()
router.register(r"", GameCode, basename="game")

QuestionRouter = routers.DefaultRouter()
QuestionRouter.register(r"", QuestionView, basename="questions")

categoryRouter = routers.DefaultRouter()
categoryRouter.register(r"", CategoryView, basename="game")

userGameRouter = routers.DefaultRouter()
userGameRouter.register(r"", UserGameView, basename="userGame")

newsletterRouter = routers.DefaultRouter()
newsletterRouter.register(r"", NewsletterView, basename="newsletter")

contactUsRouter = routers.DefaultRouter()
contactUsRouter.register(r"", ContactUsiew, basename="contactus")


urlpatterns = [
    url(r"^game/", include(router.urls)),
    url(r"^user/", include(userRouter.urls)),
    url(r"^category/", include(categoryRouter.urls)),
    url(r"^question/", include(QuestionRouter.urls)),
    url(r"^usergame/", include(userGameRouter.urls)),
    url(r"^newsletter/", include(newsletterRouter.urls)),
    url(r"^contactus/", include(newsletterRouter.urls)),
]
