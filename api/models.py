from django.db import models


# Create your models here.

class UserInfo(models.Model):
    objects = models.Manager()
    username = models.CharField(verbose_name="用户名", max_length=32, unique=True)
    password = models.CharField(verbose_name="密码", max_length=64)
    # db_index建立索引加速查询
    token = models.CharField(verbose_name="TOKEN", max_length=64, null=True, blank=True, db_index=True)


class Blog(models.Model):
    objects = models.Manager()
    category_choices = ((1, "云计算"), (2, "Python全栈"), (3, "Go开发"))
    category = models.IntegerField(verbose_name="分类", choices=category_choices)

    image = models.CharField(verbose_name="封面", max_length=255)
    title = models.CharField(verbose_name="标题", max_length=32)
    summary = models.CharField(verbose_name="简介", max_length=256)
    text = models.TextField(verbose_name="博文")
    ctime = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    creator = models.ForeignKey(verbose_name="创建者", to="UserInfo", on_delete=models.CASCADE)

    comment_count = models.PositiveIntegerField(verbose_name="评论数", default=0)
    favor_count = models.PositiveIntegerField(verbose_name="点赞数", default=0)


class Favor(models.Model):
    objects = models.Manager()
    """ 赞 """
    blog = models.ForeignKey(verbose_name="博客", to="Blog", on_delete=models.CASCADE)
    user = models.ForeignKey(verbose_name="用户", to="UserInfo", on_delete=models.CASCADE)
    create_datetime = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['blog', 'user'], name='uni_favor_blog_user')
        ]


class Comment(models.Model):
    objects = models.Manager()
    """ 评论表 """
    blog = models.ForeignKey(verbose_name="博客", to="Blog", on_delete=models.CASCADE)
    user = models.ForeignKey(verbose_name="用户", to="UserInfo", on_delete=models.CASCADE)

    content = models.CharField(verbose_name="内容", max_length=150)
    create_datetime = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
