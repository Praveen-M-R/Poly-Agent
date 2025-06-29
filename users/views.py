from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer, PasswordChangeSerializer

User = get_user_model()

class RegisterView(APIView):
    """
    API view for user registration
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Returning user data without sensitive fields
            return_serializer = UserSerializer(user)
            return Response(return_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    API view for user login
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Remove authentication requirement for login

    @csrf_exempt
    def post(self, request):
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')

        # Allow login with either email or username
        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not (email or username):
            return Response({'error': 'Username or email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to authenticate with email first if provided
        if email:
            user = authenticate(request, email=email, password=password)
        else:
            # Try with username
            user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    """
    API view for user logout
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'success': 'Successfully logged out'}, status=status.HTTP_200_OK)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class UserProfileView(APIView):
    """
    API view for retrieving and updating user profile
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Return the full user data
            return_serializer = UserSerializer(request.user)
            return Response(return_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordChangeView(APIView):
    """
    API view for changing user password
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            # Check current password
            if not request.user.check_password(serializer.validated_data['current_password']):
                return Response({'current_password': ['Wrong password.']}, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            
            # Update session auth hash to prevent logging out
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            
            return Response({'success': 'Password updated successfully'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
