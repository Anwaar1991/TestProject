from rest_framework import serializers
from .models import CustomUser
from books.models import*
from books.serializers import BookSerializer



class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = '__all__'

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

 

class ProfileSerializer(serializers.ModelSerializer):
    books_shared = BookSerializer(source='books', many=True, read_only=True)  
    total_likes = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'profile_picture', 'total_likes', 'books_shared']

    def get_books_shared(self, user):
        return Book.objects.filter(author=user).count()

    def get_total_likes(self, user):
        return Book.objects.filter(author=user).aggregate(models.Sum('likes'))['likes__sum'] or 0
