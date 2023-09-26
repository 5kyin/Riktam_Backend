from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Message,Group

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','id'] 

class ChatGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name','id']

class ChatGroupDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name','id','members']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['group', 'content', 'timestamp','sender','id','likes']
        ordering = ['-timestamp']

#this also handles the creation sent by the view
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name','id')
    
    # responsible to create user
    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']