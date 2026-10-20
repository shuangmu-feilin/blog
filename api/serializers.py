import hashlib
from rest_framework import serializers
from api import models
from ext.hook import NbHookSerializer


# 博客列表creator字段显示序列化器
class BlogUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserInfo
        fields = ['id', 'username']


# 博客列表序列化器
class BlogSerializer(NbHookSerializer, serializers.ModelSerializer):
    ctime = serializers.DateTimeField(format='%Y-%m-%d', read_only=True)
    creator = BlogUserSerializer(read_only=True)

    class Meta:
        model = models.Blog
        fields = ['id', 'category', 'image', 'title', 'text', 'summary', 'ctime', 'comment_count', 'favor_count',
                  'creator', ]
        extra_kwargs = {
            'text': {'write_only': True},
            'comment_count': {'read_only': True},
            'favor_count': {'read_only': True},
        }

    def nb_category(self, obj):
        return obj.get_category_display()


# 博客详情序列化器
class BlogDetailSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='get_category_display')
    ctime = serializers.DateTimeField(format='%Y-%m-%d')
    creator = BlogUserSerializer()

    class Meta:
        model = models.Blog
        # 详情页写__all__新增字段会自动暴露给前端，不推荐,推荐手写
        fields = ['id', 'category', 'image', 'title', 'summary', 'text', 'ctime', 'creator', 'comment_count',
                  'favor_count']


# 评论列表序列化器
class CommentSerializer(NbHookSerializer, serializers.ModelSerializer):
    class Meta:
        model = models.Comment
        fields = ['id', 'content', 'user']
        extra_kwargs = {
            # id是主键默认只读
            'id': {'read_only': True},
            'user': {'read_only': True},
        }

    def nb_user(self, obj):
        return obj.user.username


# 注册视图的序列化器
class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, min_length=3, max_length=16)

    class Meta:
        model = models.UserInfo
        fields = ['id', 'username', 'password', 'confirm_password']
        extra_kwargs = {
            'username': {'min_length': 2, 'max_length': 32},
            'id': {'read_only': True},
            'password': {'write_only': True, "min_length": 3, "max_length": 16}
        }

    def validate(self, data):
        # 判断密码是否一直
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "密码不一致"})
        # 用户名查重
        if models.UserInfo.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError({"username": "用户名已存在"})
        # 密码哈希
        raw_pwd = data['password']
        data['password'] = hashlib.md5(raw_pwd.encode('utf-8')).hexdigest()
        return data


# 登录视图的序列化器
# models的user加了unique这里就不能用ModelSerializer,要用Serializer
# 不如会触发像注册相同用户名一样的报错信息
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    # 登录加上长度限制,减轻查库的压力
    password = serializers.CharField(min_length=3, max_length=16)


# 点赞视图序列化器
class FavorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Favor
        fields = ['blog']
