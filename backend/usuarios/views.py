from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import PublicUserSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)


class MeView(generics.RetrieveAPIView):
    serializer_class = PublicUserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
