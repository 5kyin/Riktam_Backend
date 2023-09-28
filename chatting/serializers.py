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
        fields = ['name','id','members','owner']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)  # Make sender read-only
    group = serializers.PrimaryKeyRelatedField(read_only=True)  # Making group read-only

    class Meta:
        model = Message
        fields = ['group', 'content', 'timestamp','sender','id','likes']
        ordering = ['-timestamp']
     
        def create(self, validated_data):
            sender = self.context['request'].user
            validated_data['sender'] = sender
            message = Message.objects.create(**validated_data)
            return message

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

#this is for the login + user token back
class UserDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    token = serializers.CharField()