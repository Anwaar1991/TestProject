from rest_framework import generics
from .models import CustomUser
from .serializers import UserSerializer, ProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from books.models import Book
from books.serializers import BookSerializer
from django.contrib.auth import login


# CREATING SIGNUP VIEW WITH OTP VERIFICATON
import random
from django.core.cache import cache
from .models import CustomUser

class SignupAPIView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            # Create the user, setting them as inactive until OTP verification
            user = serializer.save(is_active=False)

            # Generate a 6-digit OTP
            otp = str(random.randint(100000, 999999))

            # Store OTP in Redis (keyed by user's email) with a 5-minute expiration, when user will write the otp we will match it with the OTP in cache
            cache.set(f"otp:{user.email}", otp, timeout=300)

            # Simulate sending the OTP (e.g., via email or SMS)
            print(f"OTP for {user.email}: {otp}")

            return Response({'message': 'User created. Please verify the OTP sent to your email.', 'otp': otp, 'user_created' : serializer.data}, status=status.HTTP_201_CREATED )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Checking and comparing the OTP now and activating the user.

class VerifyOTPAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({'error': 'Email and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

        cached_otp = cache.get(f"otp:{email}")
        if cached_otp == otp:
            try:
                user = CustomUser.objects.get(email=email)
                user.is_active = True  # Activate the user
                user.save()
                # Remove the OTP from cache after successful verification
                cache.delete(f"otp:{email}")
                return Response({'message': 'OTP verified. Your account is now activated.'})
            except CustomUser.DoesNotExist:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

# resend OTP API view

class ResendOTPAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # If the account is already active, there's no need for OTP
        if user.is_active:
            return Response({'message': 'Account is already activated.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate a new 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        # Store the new OTP in Redis with a 5-minute expiry
        cache.set(f"otp:{user.email}", otp, timeout=300)
        
        # Simulate sending the OTP (replace with real email/SMS sending in production)
        print(f"New OTP for {user.email}: {otp}")
        
        return Response({'message': 'A new OTP has been generated and sent.', 'otp' : otp }, status=status.HTTP_200_OK)

#Loggigng In a user and using APIView because it gives fulll control over the data.
from rest_framework_simplejwt.tokens import RefreshToken

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user) #It is jut to trigger the middleware so that middleware may detect and trigger last login fucntion.
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)

        except KeyError:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

class ListUsers(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class  = UserSerializer


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


from rest_framework.parsers import MultiPartParser, FormParser

class EditProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):
        user = request.user
        data = request.data
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        user.save()
        return Response({"message": "Profile updated successfully."})
    

class UserBookDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id, author=request.user)
        except Book.DoesNotExist:
            return Response({"error": "Book not found."}, status=404)

        serializer = BookSerializer(book)
        return Response(serializer.data)

