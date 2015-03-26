from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import generics, viewsets, mixins, exceptions
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from ..models.content import Post, Comment
from ..serializers.content import PostSerializer, CommentSerializer
from ..permissions.permissions import IsAuthor, Custom
from ..permissions.author import IsEnabled
from ..models.author import Author
from ..serializers.author import AuthorSerializer
from ..renderers.content import PostsJSONRenderer
from ..integrations import Aggregator

#
# Delete Posts and Comments
#
class BaseDeleteView(generics.DestroyAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsAuthor,)
    pass

class DeleteComment(BaseDeleteView):
    lookup_url_kwarg = "commentid"

    def get_queryset(self):
        return Comment.objects.filter(guid = self.kwargs.get(
            self.lookup_url_kwarg))

#
# Create Post and Comments
#
class CreateComment(generics.CreateAPIView):
    """
    Create a comment in the given post using postid.
    Can only create comments on posts you have permission to view.
    """
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, Custom,)
    serializer_class = CommentSerializer
    lookup_url_kwarg = "postid"

    def get_serializer_context(self):
        """
        Provide the serializer_class with Post model context needed to create a Comment
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
            'post': Post.objects.get(guid = self.kwargs.get(self.lookup_url_kwarg))
        }

#
# Post Retrieval for authors and timeline
#
class PostBaseView(object):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


# Handles permissions pertaining to posts and their various methods
class PostPermissionsMixin(object):
    """
    Authentication may take one of two values:
        BasicAuthentication: An external node is accessing posts.
        TokenAuthentication: A 'home' node user is accessing posts.
    """
    authentication_classes = (IsEnabled, TokenAuthentication, )
    permission_classes = (IsAuthenticated, Custom,)


class AuthorPostViewSet(
    PostBaseView,
    viewsets.ViewSet
):
    # authentication_classes = [BasicAuthentication, TokenAuthentication]
    permission_classes = [Custom]

    """
    Returns a listing of posts for the given author ID

    Takes:
        id: The uuid of an author model.
    """
    def list(self, request, author_pk=None):
        author = get_object_or_404(Author, id=author_pk)
        posts = self.queryset.filter(author=author)
        guids = []
        for post in posts:
            # We still want to return posts, but only those that we have permissions
            # for
            try:
                self.check_object_permissions(self.request, post)
            except exceptions.NotAuthenticated, exceptions.PermissionDenied:
                guids.append(post.guid)

        serializer = PostSerializer(posts.exclude(guid__in=guids), many=True)
        return Response({"posts": serializer.data})

    def retrieve(self, request, author_pk=None, pk=None):
        # Careful, gotchya here, if author_pk is none, it means we are dealing with
        # /author/:id and that the author id is going to be in pk
        if author_pk is None:
            author = get_object_or_404(Author, id=pk)
            data = AuthorSerializer(author).data

            # append author posts to this object
            posts = Post.objects.filter(author__id=pk)
            if posts is not None:
                posts = PostSerializer(posts, many=True)
                data["posts"] = posts.data

        # otherwise fetch a specific post
        else:
            post = self.queryset.get(author__id=author_pk, guid=pk)
            self.check_object_permissions(self.request, post)
            data = PostSerializer(post).data

        return Response(data)

    # TIMELINE call
    @list_route(methods=['get'], permission_classes=[IsAuthenticated, IsAuthor])
    def posts(self, request):
        user = self.request.user
        # TODO: filter by author id and following ids as well
        # author = Author.objects.get(user__id=user.id)
        # followers = author.followers
        queryset = Post.objects.all().filter(author__user__id=user.id)
        serializer = PostSerializer(queryset, many=True)
        return Response({"posts": serializer.data})


# Handles all interactions with post objects
class PostViewSet(
  PostBaseView,
  mixins.CreateModelMixin,
  mixins.RetrieveModelMixin,
  mixins.UpdateModelMixin,
  mixins.DestroyModelMixin,
  viewsets.GenericViewSet
):
    authentication_classes = [IsEnabled, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, Custom]
    parser_classes = (MultiPartParser, FormParser, JSONParser)


class PublicPostsViewSet(
    PostBaseView,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    renderer_classes = (PostsJSONRenderer,)

    def list(self, request):
        internal_posts = Post.objects.filter(visibility="PUBLIC")
        serializer = PostSerializer(internal_posts, many=True)
        posts = serializer.data

        # dont return public posts of other nodes in node-to-node calls
        if request.auth is None or request.user.type is not "Node":
            foreign_posts = Aggregator.get_public_posts()
            posts.extend(foreign_posts)

        return Response(posts)
