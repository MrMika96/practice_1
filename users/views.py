from django.db.models import Count, Case, When, CharField, Value
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from users.models import User
from users.serializers import (
    UserTokenObtainPairSerializer, UserRegisterSerializer,
    UserSerializer, UserCredentialsUpdateSerializer
)


@extend_schema_view(
    post=extend_schema(description="Takes a set of user credentials and returns "
                                   "an access and refresh JSON web token pair "
                                   "to prove the authentication of those credentials.",
                       summary="User authorization in the system"
                       )
)
class UserAuthView(TokenObtainPairView):
    serializer_class = UserTokenObtainPairSerializer


@extend_schema_view(
    post=extend_schema(description="User system registration, takes users email, "
                                   "password and profile data and saves it in our system",
                       summary="User registration in the system"
                       )
)
class UserRegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer


@extend_schema_view(
    retrieve=extend_schema(description="Route for viewing your own information",
                           summary="Get authorized user data"),
    update=extend_schema(description="Route for updating your profile information",
                         summary="Update authorized user data"),
    destroy=extend_schema(description="Route for deletion of your own account from system",
                          summary="delete authorized user")
)
class UserMeViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.queryset.filter(
            id=self.request.user.id
        ).select_related(
            "profile"
        ).prefetch_related(
            "application_set"
        ).annotate(
            vps_count=Count("vps"),
            workload=Case(
                When(vps_count__range=[1, 3], then=Value("EASY", output_field=CharField())),
                When(vps_count__range=[3, 8], then=Value("MEDIUM", output_field=CharField())),
                When(vps_count__gte=9, then=Value("HARD", output_field=CharField())),
                default=Value("VERY_EASY", output_field=CharField())
            ),
            applications_deployed=Count("application", distinct=True)
        ).first()


@extend_schema_view(
    list=extend_schema(description="Route for viewing all users who have been registered in the system",
                       summary="View all users"),
    retrieve=extend_schema(description="Route for viewing specific users, via user id,  "
                                       "who have been registered in the system",
                           summary="View specific user")
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.select_related("profile").prefetch_related("application_set").annotate(
            vps_count=Count("vps"),
            workload=Case(
                When(vps_count__range=[1, 3], then=Value("EASY", output_field=CharField())),
                When(vps_count__range=[3, 8], then=Value("MEDIUM", output_field=CharField())),
                When(vps_count__gte=9, then=Value("HARD", output_field=CharField())),
                default=Value("VERY_EASY", output_field=CharField())
            ),
            applications_deployed=Count("application", distinct=True)
        )


@extend_schema_view(
    put=extend_schema(description="This route is only for changing authorized user email and password",
                      summary="Authorized user credentials update")
)
class UserCredentialsUpdateView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCredentialsUpdateSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["put"]

    def get_object(self):
        return self.request.user
