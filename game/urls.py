from django.conf.urls import url
from django.urls import path, include
from rest_framework import routers

from game.views import  check_if_game_code_isValid, update_score_usergame,get_leader_board_game_code, update_score_count_usergame, get_all_category, \
     \
    check_if_user_can_play_game_code, UserDetailsApi, UserAPIs, GameCode, Category, Question

userRouter = routers.DefaultRouter()
userRouter.register(r'', UserAPIs, basename='user')
userRouter.register(r'',UserDetailsApi,basename='userDetails')

router = routers.DefaultRouter()
router.register(r'', GameCode, basename='game')

QuestionRouter = routers.DefaultRouter()
QuestionRouter.register(r'', Question, basename='questions')

categoryRouter = routers.DefaultRouter()
categoryRouter.register(r'', Category, basename='game')

urlpatterns = [
    url(r'^game/', include(router.urls)),
    url(r'^user/', include(userRouter.urls)),
    url(r'^category/', include(categoryRouter.urls)),
    url(r'^question/', include(QuestionRouter.urls)),
    path('game/user/play/check', check_if_user_can_play_game_code),  #update in usergame class
    path('game/play', check_if_game_code_isValid),  #update in usergame class
    path('game/score', update_score_usergame), #update in usergame class
    path('game/score/count', update_score_count_usergame),  #update in usergame class
    path('game/code/leaderboard', get_leader_board_game_code), #update in usergame class
    path('game/category', get_all_category),  #update in usergame class
]
