from rest_framework import serializers
from books.models import*
from accounts.serializers import *



# Book Comment Serializer.
class BookCommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    user = serializers.StringRelatedField()

    class Meta:
        model = BookComment
        fields = ['id', 'user', 'content', 'created_at', 'replies', 'parent']

    def get_replies(self, obj):
        # Get only direct children of this comment
        replies = obj.replies.all()
        return BookCommentSerializer(replies, many=True).data
    

    
# File Serializer to add pdf books
class BookFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookFile
        fields = ['pdf_content']



# Book Serializer to add and show books
class BookSerializer(serializers.ModelSerializer): 
    pdf_files = BookFileSerializer(many=True, read_only=True)
    like_count = serializers.SerializerMethodField()
    liked_users = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ['like_count', 'liked_users', 'comments']

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_liked_users(self, obj):
        return [like.user.first_name for like in obj.likes.all()]

    def get_comments(self, obj):
        # Only fetch top-level comments (exclude replies)
        top_level_comments = obj.comments.filter(parent=None)
        return  BookCommentSerializer(top_level_comments, many=True).data

    

# FRIEND REQUEST MODEL
class FriendRequestSerializer(serializers.ModelSerializer):
    from_user_name = serializers.CharField(source='from_user.first_name', read_only=True)
    to_user_name = serializers.CharField(source='to_user.first_name', read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_user', 'to_user', 'from_user_name', 'to_user_name', 'is_accepted', 'is_rejected', 'timestamp']
        read_only_fields = ['is_accepted', 'is_rejected']

# CHAT MODULE SERIALIZER
class MessageSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp', 'is_read']
