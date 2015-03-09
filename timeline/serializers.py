from rest_framework import serializers
from timeline.models import Post, Comment
import time
import datetime
from author.serializers import CompactUserSerializer


class UnixDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        """
        Return epoch time for datetime model field.
        """
        try:
            return int(time.mktime(value.timetuple()))
        except(AttributeError, TypeError):
            return None


class PostSerializer(serializers.ModelSerializer):
    """
    Multiple posts are deserialized as a list object

    JSON Representation:
        [
            {
                user:{username:'', first_name:'', last_name:''},
                id:'',
                text:'',
                date:'',
                image:''
            }
        ]

    Only for retrieval. Should not be used for insertion.
    """
    user = CompactUserSerializer(many=False, read_only=True)
    date = UnixDateTimeField(read_only=True)
    class Meta:
        model = Post
        fields = ('user', 'id', 'text', 'public', 'fof', 'date', 'image')

        # Fields that must not be set in HTTP request body
        read_only_fields = ('user' 'id', 'date',)


class CommentSerializer(serializers.ModelSerializer):
    date = UnixDateTimeField(read_only=True)
    class Meta:
        model = Comment
        fields = ('id', 'text', 'date')
        read_only_fields = ('date',)
