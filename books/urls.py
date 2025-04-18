from .views import BatchUploadView
from django.urls import path
from .views import *

urlpatterns =  [
  
    # UPLOAD - RETRIEVE - LIST - READ A BOOK
    path('upload-books/', BatchUploadView.as_view(), name='upload-books'),
    path('retrieve/<int:pk>/', RetrieveBooks.as_view() , name='retrieve-books'),
    path('update/<int:book_id>/', UpdateBookView.as_view() , name='update-book'),
    path('book-list/', BooksList.as_view() , name='books-list'),
    path('read-book/<int:pk>/', BookPDFView.as_view(), name='read-book'),

    # LIKE - UNLIKE - COMMENT ON A BOOK
    path('book/<int:pk>/like/', LikeBookView.as_view(), name='like-book'),
    path('book/<int:pk>/unlike/', UnlikeBookView.as_view(), name='unlike-book'),
    path('book/<int:book_id>/comments/', BookCommentListCreateView.as_view(), name='book-comments'),


    # SEND/RECIEVE FRIEND REQUEST - APPROVE/REJECT FRIEND REQUEST - SHOW FRIEND LIST
    path('friend-request/send/<int:user_id>/', SendFriendRequestView.as_view()),
    path('pending-requests/<int:user_id>/', PendingRequestsView.as_view()),
    path('friend-request/respond/<int:request_id>/', RespondFriendRequestView.as_view()),
    path('users/friends/', FriendsListView.as_view()),

    # SEND/RECIEVE MESSAGES - VIEW ALL MESSAGES (CHATS)
    # path('messages/send/<int:receiver_id>/', SendMessageView.as_view()),
    path('messages/inbox/<int:friend_id>/', InboxView.as_view()),


]



'''
COMMENT API DETAILS

to comment on a book you have to use:
'content': 'your comment'

to reply a comment you have to do:
'content': 'you comment'
'parent' : 'id of the comment to which you are replying'


'''

