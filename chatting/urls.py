from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    
    #This is a direct route for the token removal i did not use this because i wanted a success logout message from the server
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    #AUTH
    path('login/', AuthToken.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    #USER MANAGEMENT
    path('users/', MembersView.as_view(), name='user-list'),
    path('users/edit/', UserEditView.as_view(), name='user-edit'),
    path('register/', UserRegistrationView.as_view(), name='user-registration'),

    #GROUP MANAGEMENT AND MESSAGES
    path('group/', CreateOrGetGroupView.as_view({'get': 'list','post':'create'}), name='create-or-get-group'),
    path('group/<int:group_id>/', CreateOrGetGroupView.as_view({'get': 'list'}), name='get-group-detials'),
    path('group/<int:group_id>/messages/', SendRecieveMessageView.as_view(), name='message-create-recieve-list'),
    path('group/<int:group_id>/messages/<int:pk>/like/', LikeMessageView.as_view(), name='liking-a-message'),
    path('group/<int:group_id>/members/', MembersView.as_view(), name='members-list'),
    path('group/<int:group_id>/join/<int:user_id>/',JoinGroupView.as_view(), name='join-group'),
    path('group/<int:group_id>/leave/<int:user_id>/', LeaveRemoveGroupView.as_view(), name='leave-remove-from-group'),
    path('group/<int:group_id>/delete/', DeleteGroupView.as_view({'delete': 'destroy'}), name='delete-group'),
    
]