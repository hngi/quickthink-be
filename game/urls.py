from django.conf.urls import url
from django.urls import path, include
from rest_framework import routers

from game.views import create_a_game_code, check_if_game_code_isValid, end_game, update_score_usergame, \
    get_leader_board_game_code, update_score_count_usergame, get_all_category, create_category, \
    create_question, login_user, register, get_user_data, forgot_password, change_password, get_questions, \
    update_question, delete_question, delete_category, update_category, get_all_category_user, get_questions_user, \
    check_if_user_can_play_game_code, delete_user, opendb, UserDetailsApi, UserAPIs, GameCode

userRouter = routers.DefaultRouter()
userRouter.register(r'', UserAPIs, basename='user')
userRouter.register(r'',UserDetailsApi,basename='userDetails')

router = routers.DefaultRouter()
router.register(r'', GameCode, basename='game')

urlpatterns = [
    url(r'^game/', include(router.urls)),
    url(r'^user/', include(userRouter.urls)),
    path('game/user/play/check', check_if_user_can_play_game_code),
    path('game/play', check_if_game_code_isValid), 
    path('game/score', update_score_usergame),
    path('game/score/count', update_score_count_usergame), 
    path('game/code/leaderboard', get_leader_board_game_code),
    path('game/category', get_all_category),  
    path('game/create/category', create_category), 
    path('game/create/question', create_question),
    path('game/update/question', update_question),
    path('game/update/category', update_category),
    path('game/delete/category', delete_category),
    path('game/delete/question', delete_question),
    path('game/question', get_questions),
    path('game/questions/user',get_questions_user),
    path('game/category/user',get_all_category_user),
    path('opendb', opendb),
]
