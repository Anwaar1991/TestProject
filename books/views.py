from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework import generics
from .serializers import *
from .models import *
import threading
from django.db import close_old_connections
from accounts.models import CustomUser
from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError
from .serializers import BookCommentSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
from django.db.models import Q

# for single book upload but that can be done by the next api
# class UploadBookView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         title = request.data.get('title', 'Untitled')
#         description = request.data.get('description', '')
#         files = request.FILES.getlist('pdf_content')
#         author = request.user

#         if not files:
#             return Response({'error': 'No PDF files provided.'}, status=status.HTTP_400_BAD_REQUEST)

#         # Create the Book object
#         book = Book.objects.create(
#             title=title,
#             description=description,
#             author=author
#         )

#         # Save each file under the Book
#         for file in files:
#             BookFile.objects.create(book=book, pdf_content=file)

#         # Construct response with all file URLs
#         pdf_urls = [file.pdf_content.url for file in book.pdf_files.all()]

#         return Response({
#             "id": book.id,
#             "title": book.title,
#             "description": book.description,
#             "pdf_content": pdf_urls,
#             "author": book.author.id
#         }, status=status.HTTP_201_CREATED)








# ==========================BOOK UPLOAD - READ - LIST - RETRIEVE STARTS==============================

# API for book upload
class BatchUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        files = request.FILES.getlist('pdf_content')
        title = request.data.get('title', 'Untitled Book')
        description = request.data.get('description', '')
        user_id = request.user.id

        # Make sure that the files uploaded are only pdf ones.

        # ❌ If no files uploaded
        if not files:
            raise ValidationError({"pdf_content": "No files uploaded."})

        # ✅ Check all files are PDFs
        for f in files:
            if not f.name.lower().endswith('.pdf'):
                raise ValidationError({"pdf_content": f"'{f.name}' is not a PDF file."})


        # Read file content to keep it in memory
        file_data_list = []
        for f in files:
            copied_file = ContentFile(f.read())
            copied_file.name = f.name
            file_data_list.append(copied_file)

        def handle_uploads(file_data_list, title, description, user_id):
            close_old_connections()
            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                print("User not found")
                return

            # ✅ Create one book object
            book = Book.objects.create(
                title=title,
                author=user,
                description=description
            )

            # ✅ Create one file entry per PDF
            for f in file_data_list:
                BookFile.objects.create(book=book, pdf_content=f)

            print(f"Book '{book.title}' created with {len(file_data_list)} PDFs.")

        threading.Thread(
            target=handle_uploads,
            args=(file_data_list, title, description, user_id)
        ).start()

        return Response({"message": "Upload started in background"}, status=status.HTTP_202_ACCEPTED)
    
# Get the whole books list
class BooksList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Book.objects.all()
    serializer_class = BookSerializer

# Get the specific book
class RetrieveBooks(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Book.objects.all()
    serializer_class = BookSerializer

# Update the specific book, only onwer of the book can do that.

class UpdateBookView(APIView): 
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, book_id):
        user = request.user
        book = Book.objects.get(id=book_id)
        if book.author != user:
            return Response({'error': 'You can only edit your own book'}, status=status.HTTP_401_UNAUTHORIZED)
        elif book.author == user:
            if request.data.get('title'): 
                book.title = request.data.get('title')
            if request.data.get('description'):
                book.description = request.data.get('description')
            if request.FILES:
                BookFile.objects.update(book = book, pdf_content = request.data.get('pdf_content'))
            book.save()
            return Response({'success': 'Updated Successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid user'}, status=status.HTTP_400_BAD_REQUEST)



# Read the book
class BookPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        pdf_files = BookFile.objects.filter(book=book)
        file_urls = [request.build_absolute_uri(f.pdf_content.url) for f in pdf_files]

        return Response({
            "book": book.title,
            "pdf_files": file_urls
        })




# ==========================BOOK UPLOAD - READ - LIST - RETRIEVE ENDS==============================










# ========================== BOOK LIKE - UNLIKE - COMMENT- REPLY A COMMENT - ALL COMMENTS STARTS ====================




# FOR DJNAGO CHANNEL NOTIFICATION TO THE USER FOR LIKES:
def notify_user(book_owner_id, like_by_id, message):
    channel_layer = get_channel_layer()
    group_name = f"notifications_{book_owner_id}"  #This group name must be same as the Book name in consumers.py ie. notifications_
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "content": {
                "message": message,
                "liked_by": like_by_id
            }
        }
    )


# FOR DJNAGO CHANNEL NOTIFICATION TO THE USER FOR COMMENTS:
def notify_user_comment(book_owner_id, commenter, message):
    channel_layer = get_channel_layer()
    group_name = f"notifications_{book_owner_id}"  #This group name must be same as the Book name in consumers.py
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "content": {
                "message": message,
                "commented_by": commenter
            }
        }
    )

 
# Liking a book
class LikeBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        liked_by_id = user.id
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        like, created = BookLike.objects.get_or_create(book=book, user=user)
        if created:
            # 🔔 Notify the book author
            if book.author != user:  # Don't notify self-likes
                notify_user(book.author.id, liked_by_id, f"{user.first_name} liked your book '{book.title}'.")
            return Response({"message": "Book liked."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "You already liked this book."}, status=status.HTTP_200_OK)
        

# Unliking a book
class UnlikeBookView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            like = BookLike.objects.get(book=book, user=user)
            like.delete()
            return Response({"message": "Book unliked."})
        except BookLike.DoesNotExist:
            return Response({"error": "You haven't liked this book yet."}, status=status.HTTP_400_BAD_REQUEST)
        

class BookCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = BookCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        book_id = self.kwargs.get('book_id')
        return BookComment.objects.filter(book_id=book_id, parent=None).order_by('-created_at')

    def perform_create(self, serializer):
        book_id = self.kwargs.get('book_id')
        
        book = Book.objects.get(id=book_id)

        
        if not 'parent' in self.request.data and book.author == self.request.user:
            raise ValidationError("You cannot comment on your own book.")
        
        commented_by = self.request.user.id
        # 🔔 Notify the book author (if not self)

        notify_user_comment(
            book.author.id,
            commented_by,
            f"{self.request.user.first_name} commented on your book '{book.title}'."
        )

        serializer.save(user=self.request.user, book=book)





# ========================== BOOK LIKE - UNLIKE - COMMENT- REPLY A COMMENT - ALL COMMENTS ENDS ====================










# ============================= FRIEND REQUEST SEND/RECIEVE - APPROVE/REJECT - ALL FRIENDS STARTS ================




# Notification function for friend requests

# Django Channels notification for friend request
def notify_user_friend_response(to_user_id, from_user_name, message):
    channel_layer = get_channel_layer()
    group_name = f"notifications_{to_user_id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "content": {
                "message": message,
                "from": from_user_name
            }
        }
    )


# FRIEND REQUEST VIEW CLASS 

class SendFriendRequestView(APIView):

    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, user_id):
        sender = request.user
        receiver = CustomUser.objects.get(id=user_id)

        if sender == receiver:
            return Response({'message': 'Cannot send request to yourself'}, status=status.HTTP_403_FORBIDDEN)
        
        friend_request, created = FriendRequest.objects.get_or_create(from_user = sender, to_user=receiver)

        if not created:
            return Response({"error": "Friend request already sent!"}, status=status.HTTP_400_BAD_REQUEST)
        
        notify_user_friend_response(
            to_user_id=receiver.id,
            from_user_name=sender.first_name,
            message=f"You just got a friend request from {sender.first_name}"
        )

        return Response({"Success": "Friend Request sent!"}, status=status.HTTP_200_OK)


# PENDING FRIEND REQUESTS
class PendingRequestsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        if request.user.id != user_id:
            return Response({"error": "You are not authorized to view this user's pending requests."}, status=403)

        sent = FriendRequest.objects.filter(from_user=request.user, is_accepted=False, is_rejected=False)
        received = FriendRequest.objects.filter(to_user=request.user, is_accepted=False, is_rejected=False)

        data = {
            "sent": [{"id": fr.id, "to_user": fr.to_user.email} for fr in sent],
            "received": [{"id": fr.id, "from_user": fr.from_user.email} for fr in received],
        }
        return Response(data)



# Accept or reject friend request IF REJECTED, USER CANNOT SEND REQUEST AGAIN


# class RespondFriendRequestView(APIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request, request_id):
#         action = request.data.get('action')  # 'accept' or 'reject'
#         try:
#             friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user)
#         except FriendRequest.DoesNotExist:
#             return Response({"error": "Friend request not found or you're not authorized to respond."}, status=404)


#         if action == 'accept':
#             friend_request.is_accepted = True
#             friend_request.save()

#             # ✅ Add mutual friendship - So that both must be shown in each other's friend list.
#             request.user.friends.add(friend_request.from_user)
#             friend_request.from_user.friends.add(request.user)

#             # 🔔 Notify sender
#             notify_user_friend_response(
#                 to_user_id=friend_request.from_user.id,
#                 from_user_name=friend_request.to_user.first_name,
#                 message=f"{friend_request.to_user.first_name} accepted your friend request."
#             )

#             return Response({"message": "Friend request accepted."})

#         elif action == 'reject':
#             friend_request.is_rejected = True
#             friend_request.save()

#             # 🔔 Send notification to sender that request was rejected
#             notify_user_friend_response(
#                 to_user_id=friend_request.from_user.id,
#                 from_user_name=friend_request.to_user.first_name,
#                 message=f"{friend_request.to_user.first_name} rejected your friend request."
#             )

#             return Response({"message": "Friend request rejected."})

#         else:
#             return Response({"error": "Invalid action."}, status=400)
        

# Accept or reject friend request IF REJECTED, USER CAN SEND REQUEST AGAIN
class RespondFriendRequestView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, request_id):
        action = request.data.get('action')
        try:
            friend_request = FriendRequest.objects.get(id=request_id, to_user= request.user)
        except FriendRequest.DoesNotExist:
            return Response({'error': 'Sorry! either you are not authorized to see this request or the request doesnot exists'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        if action == 'accept':
            friend_request.is_accepted = True
            friend_request.save()

            # Add both users in eachother's friend list
            request.user.friends.add(friend_request.from_user)
            friend_request.from_user.friends.add(request.user)

            notify_user_friend_response(
                to_user_id=friend_request.from_user.id,
                from_user_name=request.user.first_name,
                message= f"Your Request Accepted by {friend_request.to_user.first_name}"
            )

            return Response({'success': ' request accepted!'}, status=status.HTTP_200_OK )


        elif action == 'reject':
            friend_request.delete()

            notify_user_friend_response(
                to_user_id=friend_request.to_user.id,
                from_user_name=friend_request.from_user.first_name,
                message = f"{friend_request.to_user.first_name} has rejected your Request!"
            )

            return Response({'success': ' request rejected!'}, status=status.HTTP_200_OK )


            
        
        else:
            return Response({'error': 'Invalid input, please select accpet or reject to move forward'}, status=status.HTTP_400_BAD_REQUEST )
            
        
# TO SEE ALL FRIEND LIST

class FriendsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        friends = user.friends.all().values('id', 'email', 'first_name', 'last_name')
        return Response(friends)

        





# ============================= FRIEND REQUEST SEND/RECIEVE - APPROVE/REJECT - ALL FRIENDS ENDS ================













# ============================= MESSAGING BETWEEN FRIENDS IS HANDLED BY SOCKETS - ALL MESSAGES (INBOX) STARTS HERE ========================





class InboxView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, friend_id):
        user = request.user
        friend = CustomUser.objects.filter(id=friend_id).first()

        # check if user is the friend
        is_friend = FriendRequest.objects.filter(Q(from_user=friend, to_user=user) | Q(from_user=user, to_user=friend)).exists()
        if not is_friend:
            return Response({"error": "Your can only messages with your friends!"})
        
        messaage_data = Message.objects.filter(Q(sender=friend, receiver=user) | Q(sender=user, receiver=friend)).order_by('timestamp')
        serializer = MessageSerializer(messaage_data, many=True)
        return Response(serializer.data)






# ============================= MESSAGING BETWEEN FRIENDS - ALL MESSAGES (INBOX) ENDS ========================

