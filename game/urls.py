from django.conf.urls import url
from django.urls import path, include

from game.views import create_a_game_code, check_if_game_code_isValid, end_game, update_score_usergame, \
    get_leader_board_game_code, update_score_count_usergame, get_all_category, create_category, \
    create_question, login_user, register, get_user_data, forgot_password, change_password, get_questions, \
    update_question, delete_question, delete_category, update_category, get_all_category_user, get_questions_user, \
    check_if_user_can_play_game_code, delete_user, opendb, get_all_subcategory_user

urlpatterns = [
    path('game', create_a_game_code),
    path('game/user/play/check', check_if_user_can_play_game_code),
    path('game/play', check_if_game_code_isValid),
    path('game/end', end_game),
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
    path('user/registration', register),
    path('user/login', login_user), 
    path('user/delete', delete_user),
    path('user/info', get_user_data), 
    path('user/reset_password', change_password), 
    path('user/forgot_password', forgot_password),
    path('game/questions/user',get_questions_user),
    path('game/category/user',get_all_category_user),
    path('opendb', opendb),
    path('game/category/subcategory', get_all_subcategory_user),
]
