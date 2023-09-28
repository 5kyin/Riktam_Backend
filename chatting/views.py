from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from .models import Group, Message
from .serializers import MessageSerializer,UserRegistrationSerializer,ChatGroupSerializer,MemberSerializer,ChatGroupDetailSerializer,UserEditSerializer,UserDetailSerializer

from rest_framework import generics,permissions,status,viewsets,pagination,serializers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

# Anyone can create group
# But only Owner Can delete group
class CreateOrGetGroupView(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = ChatGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    #Using this so that i do not show the members while i show groups
    def get_serializer_class(self):
        group_id = self.kwargs.get('group_id',None)
        
        if self.action == 'list' and group_id is None:
            return ChatGroupSerializer
        
        if group_id:
            return ChatGroupDetailSerializer
        return ChatGroupSerializer

    def get_queryset(self):   
        group_id = self.kwargs.get('group_id',None)
        sender = self.request.user
        if group_id:
            group = get_object_or_404(Group.objects,deleted=False,id=group_id)
            all_members = group.members.all()
            if sender in all_members:
                return [group]
        return Group.objects.filter(deleted=False,members=sender)
    
    def perform_create(self, serializer):
        # Add the owner creating the group as a member 
        serializer.save(members=[self.request.user],owner=self.request.user)

class MembersView(generics.ListAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            group_id = self.kwargs.get('group_id',None)
            if group_id:
                group = Group.objects.get(id=group_id)
                return group.members.all()
            return User.objects.all()
        except Group.DoesNotExist:
            return []

# End point to get and post message
class SendRecieveMessageView(generics.ListCreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    # pagination_class = pagination.LimitOffsetPagination
    # page_size = 50  # Adjust this value to control the number of records per page

    def perform_create(self, serializer):
        # group_id = self.request.data.get('group')
        group_id = self.kwargs.get('group_id',None)
        content = self.request.data.get('content',None)
        sender = self.request.user
        group = get_object_or_404(Group.objects,deleted=False,id=group_id)
        all_members = group.members.all()
        if sender not in all_members:
            raise serializers.ValidationError({'message': F"You are not allowed to send text on this group."})
        if len(content) == 0:
            raise serializers.ValidationError({'message': F"Empty message are not allowed."})
        serializer.save(sender=sender,group=group)

    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(Group.objects,deleted=False,id=group_id)
        all_members = group.members.all()
        if self.request.user not in all_members:
            # return Response({'message': F"You are not a participant of this group."},status=status.HTTP_403_FORBIDDEN)
            return []
        return Message.objects.filter(group_id=group_id)

class LikeMessageView(generics.UpdateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def partial_update(self, serializer,group_id=None,pk=None):
        group = get_object_or_404(Group.objects,deleted=False,id=group_id)
        message = get_object_or_404(Message.objects.filter(group=group), id=pk)
        user = self.request.user
        if user not in group.members.all():
            return Response({'message': "You cannot like a messege you're not a part of."}, status=status.HTTP_403_FORBIDDEN)
        if user in message.likes.all():
            message.likes.remove(user)
            return Response({'message': "Unliked Message"}) 
        message.likes.add(user)
        return Response({'message': F"Liked Message"})
        # serializer.save(likes=[self.request.user])

class DeleteGroupView(viewsets.ModelViewSet):
    queryset = Group.objects.filter(deleted=False)
    serializer_class = ChatGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        group_id = self.kwargs.get('group_id',None)
        group = Group.objects.get(deleted=False,pk=group_id)
        return group

    def destroy(self, request,group_id):
        group = self.get_object()
        #If user is the owner 
        if request.user.id == group.owner.id:
            group.deleted = True
            group.save()
            return Response({'message': 'Group deleted successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'You do not have permission to delete this group.'}, status=status.HTTP_403_FORBIDDEN)
    # For Forever Delete // But need to the make a reusable group ID allocation for memeory and DB conservation 
    # The PID is incremental so soft delete is advisable
    # @action(detail=True, methods=['delete'])
    # def delete_group(self, request, pk=None):
    #     group = self.get_object()
    #     # Check permissions to delete the group (e.g., only group admin or owner)
    #     if request.user != group.owner:
    #         return Response({'message': 'You do not have permission to delete this group.'}, status=403)
    #     group.delete()
    #     return Response({'message': 'Group deleted successfully.'})

#Only owner can invite the person to his group
class JoinGroupView(generics.UpdateAPIView):
    queryset = Group.objects.filter(deleted=False)
    serializer_class = ChatGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def partial_update(self,request,user_id=None,group_id=None):
        user = get_object_or_404(User.objects, id=user_id)
        group = Group.objects.get(deleted=False,id=group_id)
        all_members = group.members.all()
        if self.request.user != group.owner:
            return Response({'message': F"Only Owners can add members to the group : {group}."},status=status.HTTP_403_FORBIDDEN)
        if user not in all_members:
            group.members.add(user)
            return Response({'message': F"User added to {group}."})
        return Response({'message': F"User already a member of {'group'}."},status=status.HTTP_403_FORBIDDEN)

# If user Wantes to leave a group
#TODO: if admin wants to leave a group then what to do ?
class LeaveRemoveGroupView(generics.UpdateAPIView):
    queryset = Group.objects.filter(deleted=False)
    serializer_class = ChatGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Handle when you want to remove someone else and you're the group owner.
    def partial_update(self, request, user_id=None,group_id=None):
        user = get_object_or_404(User.objects, id=user_id)
        group = get_object_or_404(Group.objects,deleted=False,id=group_id)
        all_members = group.members.all()
        if self.request.user == group.owner and self.request.user == user:
            return Response({'message': "Action not possible you're the group owner."},status=status.HTTP_403_FORBIDDEN)
        if self.request.user != group.owner and self.request.user != user:
            return Response({'message': F"Only Owners can remove other members from the group : {group}."},status=status.HTTP_403_FORBIDDEN)
        if self.request.user == group.owner and self.request.user != user and user in all_members:
            group.members.remove(user)
            return Response({'message': F"{user} is no longer a participant of group : {group}"})
        if self.request.user != group.owner and self.request.user in all_members:
            group.members.remove(user)    
            return Response({'message': F"{user} is no longer a participant of group : {group}"})
        return Response({'message': F"{user} is not a participant of this group : {group}"},status=status.HTTP_404_NOT_FOUND)
        
    
    # Handle when you want to remove yourself and you're the group owner.
    # DO NOT TRIGGER THIS
    # def perform_update(self, serializer):
    #     group = self.get_object()
    #     user = self.request.user 
    #     if group.owner.id == user.id:
    #         return Response({'message': "Action not possible you're the group owner."}) #need to work up the logic where we can decide what to do if the owner wants to delete the group
    #     group.members.remove(user)

# User Registration Any one can register 
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)

class UserEditView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Retrieve the authenticated user
        return self.request.user   

# Auth Token generation  
class AuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        user_info = request.data
        serializer = self.serializer_class(data=user_info,context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        print(user)
        token, created = Token.objects.get_or_create(user=user)
        serializer = UserDetailSerializer({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'token': "Token "+token.key, 
        })
        return Response(serializer.data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        token = Token.objects.get(user=request.user)
        if token:
            token.delete()
            return Response({'message': "You've been logged out"},status=status.HTTP_200_OK)