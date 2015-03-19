from django.db import models
from author_api.models import Author
from uuidfield import UUIDField
import ast

class ListField(models.TextField):
    __metaclass__ = models.SubfieldBase
    description = "Stores a python list"

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return ast.literal_eval(value)

    def get_prep_value(self, value):
        if value is None:
            return value

        return unicode(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

class Post(models.Model):
    """
    Post
    """
    guid = UUIDField(auto = True, primary_key = True)
    title = models.CharField(blank = False, max_length = 200)
    content = models.TextField(blank=False)
    contentType = models.CharField(blank = False, max_length = 16)
    categories = ListField(blank = True)
    pubDate = models.DateTimeField(auto_now_add=True, editable = False)
    visibility = models.CharField(blank=False, max_length=10)
    image = models.ImageField(null=True, blank=True)
    author = models.ForeignKey(Author, blank=False, editable = False)

    def __unicode__(self):
        return u'%s %s' %(self.author.user.username, self.content)

    # Use in serializers to add url source and origin information
    # Eg, where the query came from, and where you should query next time
    @property
    def source(self):
        return None

    @property
    def origin(self):
        return None

class Comment(models.Model):
    """
    Comment

    A comment's privacy is inherited from the Post public attribute
    """
    guid = UUIDField(auto = True, primary_key = True)
    content = models.TextField(blank=False)
    contentType = models.CharField(blank = True, max_length = 16)
    pubDate = models.DateTimeField(auto_now_add=True, editable = False)
    post = models.ForeignKey('Post', related_name='comments')
    author = models.ForeignKey(Author, blank=False, editable = False)

    def __unicode__(self):
        return u'%s %s' %(self.author.username, self.content)
