from django.db import models
from BookManagement.settings import AUTH_USER_MODEL

 
# Book model
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='books')
    description = models.TextField()

    def __str__(self):
        return self.title
    
#Pdf Books model to realte as one to many
class BookFile(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='pdf_files')
    pdf_content = models.FileField(upload_to='books/pdfs/')

#Book Likes Model
class BookLike(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('book', 'user')  # Prevent duplicate likes

    def __str__(self):
        return f"{self.user.first_name} liked {self.book.title}"
    

# Book Comment Model
class BookComment(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name}: {self.content[:30]}"
'''

to comment on a book you have to use:
'content': 'your comment'

to reply a comment you have to do:
'content': 'you comment'
'parent' : 'id of the comment to which you are replying'


'''


# FRIEND REQUEST MODEL

class FriendRequest(models.Model):
    from_user = models.ForeignKey(AUTH_USER_MODEL, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(AUTH_USER_MODEL, related_name='received_requests', on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.first_name} ➡️ {self.to_user.first_name}"


# MESSAGING MODEL FOR LIVE CHAT
class Message(models.Model):
    sender = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.receiver}: {self.content[:30]}"
