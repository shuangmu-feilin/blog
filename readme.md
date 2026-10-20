# Django DRF 博客后端接口开发文档

## 项目简介

基于 `Django 4.2 + DRF(djangorestframework) + drf-spectacular` 实现的简易博客后端，包含用户注册登录（Token认证）、博客增查、评论、点赞/取消点赞功能，接口文档自动生成（Swagger）。

> 技术栈：Python、Django4.2、DRF、drf-spectacular 数据库：SQLite(Django 内置 db.sqlite3) 认证方案：自定义Token认证

## 一、数据库模型设计（models.py）

一共4张表：用户表、博客表、点赞表、评论表

### 1. UserInfo 用户表

| 字段     | 类型          | 说明                                     |
| -------- | ------------- | ---------------------------------------- |
| username | CharField(32) | 用户名，唯一约束 unique=True，建立索引   |
| password | CharField(64) | MD5加密后的密码                          |
| token    | CharField(64) | 登录令牌，可为空，建立索引，用于身份认证 |

### 2. Blog 博客表

| 字段          | 类型                 | 说明                                  |
| ------------- | -------------------- | ------------------------------------- |
| category      | Integer              | 分类：1云计算 / 2Python全栈 / 3Go开发 |
| image         | CharField(255)       | 封面图地址                            |
| title         | CharField(32)        | 博客标题                              |
| summary       | CharField(256)       | 简介                                  |
| text          | TextField            | 博客正文                              |
| ctime         | DateTime             | 创建时间，自动填充 auto_now_add       |
| creator       | ForeignKey           | 外键关联UserInfo，博客作者，级联删除  |
| comment_count | PositiveIntegerField | 评论计数，默认0                       |
| favor_count   | PositiveIntegerField | 点赞计数，默认0                       |

### 3. Favor 点赞表

| 字段                                                         | 类型       | 说明     |
| ------------------------------------------------------------ | ---------- | -------- |
| blog                                                         | ForeignKey | 关联博客 |
| user                                                         | ForeignKey | 关联用户 |
| create_datetime                                              | DateTime   | 点赞时间 |
| 联合唯一约束：**同一个用户对同一篇博客只能点赞一次**，防止重复点赞。 |            |          |

### 4. Comment 评论表

| 字段            | 类型           | 说明         |
| --------------- | -------------- | ------------ |
| blog            | ForeignKey     | 关联博客     |
| user            | ForeignKey     | 关联评论用户 |
| content         | CharField(150) | 评论内容     |
| create_datetime | DateTime       | 评论时间     |

## 二、序列化器设计（serializers.py）

> 序列化器作用：参数校验、ORM对象转JSON、前端入参解析

1. `BlogUserSerializer`：用户简略信息序列化（博客作者展示，只返回id、username）

2. `BlogSerializer`：博客列表序列化，`ctime`格式化，分类名称转中文展示，text只写不返回

3. `BlogDetailSerializer`：博客详情序列化

4. `CommentSerializer`：评论序列化，自动展示评论人用户名

5. ```
   RegisterSerializer
   ```

   ：注册序列化器

   - 校验两次密码一致
   - 校验用户名不重复
   - 密码自动MD5加密入库

6. `LoginSerializer`：登录参数校验（username、password长度校验）

7. `FavorSerializer`：点赞接口入参序列化，只接收blog

## 三、自定义工具封装

### 1. 统一响应函数 `api_response`

所有接口统一返回格式，方便前端解析：

```
{
    "code": 200,
    "data": {},
    "msg": "提示信息",
    "error": "错误信息",
    "detail": "详细校验错误"
}
```

- `code`：业务状态码（200成功，400参数错误，404资源不存在）
- `data`：成功时返回的数据
- `msg`：操作提示（点赞成功、取消点赞成功）
- `error/detail`：错误详情

### 2. 自动文档装饰器 `auto_schema`

封装 `extend_schema`，快速给POST接口配置swagger文档入参。

### 3. 分页类

- `BlogPagination`：博客列表分页，每页默认10条，支持size调整，最大50
- `CommentPagination`：评论列表分页，规则同上

### 4. 认证组件 `BlogAuthentication`

自定义Token认证：请求头携带token，校验登录用户；部分接口配置`ForceLoginAuthentication`强制登录。

## 四、接口列表（urls.py）

访问swagger文档地址：`/api/docs/`

> 基础前缀：`/api/`

| 接口地址                      | 请求方式 | 接口说明                 | 是否需要登录 |
| ----------------------------- | -------- | ------------------------ | ------------ |
| `/api/schema/`                | GET      | openapi schema原始文件   | 否           |
| `/api/docs/`                  | GET      | Swagger在线接口文档      | 否           |
| `/api/register/`              | POST     | 用户注册                 | 否           |
| `/api/login/`                 | POST     | 用户登录，返回token      | 否           |
| `/api/blog/`                  | GET      | 获取博客列表（分页）     | 是           |
| `/api/blog/`                  | POST     | 新建博客                 | 是           |
| `/api/blog/<int:pk>/`         | GET      | 获取博客详情             | 否           |
| `/api/comment/<int:blog_id>/` | GET      | 获取博客评论列表（分页） | 是           |
| `/api/comment/<int:blog_id>/` | POST     | 发表评论                 | 是           |
| `/api/favor/`                 | POST     | 点赞 / 取消点赞          | 是           |

## 五、接口业务逻辑说明

### 1. 用户注册 RegisterView

1. 接收 username、password、confirm_password
2. 序列化器校验：两次密码一致、用户名不重复、长度校验
3. 密码MD5加密
4. 捕获并发注册的 `IntegrityError`，兜底防止同名用户
5. 注册成功返回用户信息

### 2. 用户登录 LoginView

1. 接收用户名、原始密码

2. 密码MD5加密后和数据库比对

3. 校验成功：清空旧token，生成uuid新token存入用户表

4. 返回token给前端，后续请求头部携带token认证

   > 登录逻辑：`token = str(uuid.uuid4())`

### 3. 博客列表 BlogView GET

1. 查询所有博客，id倒序
2. 分页处理
3. 返回：博客列表、总条数、当前页码

```
{
    "code":200,
    "data":{
        "list":[...],
        "total": 100,
        "page": 1
    }
}
```

### 4. 新建博客 BlogView POST

1. 校验登录状态
2. 接收博客参数，序列化校验
3. 保存博客，自动绑定当前登录用户为creator

### 5. 博客详情 BlogDetailView GET

1. 根据pk查询博客，不存在返回404
2. 返回博客完整详情

### 6. 评论列表 CommentView GET

1. 根据blog_id过滤评论，按评论时间倒序
2. 分页返回评论数据

### 7. 发表评论 CommentView POST

1. 校验登录
2. 判断博客是否存在
3. 参数校验，保存评论，自动绑定user、blog

### 8. 点赞接口 FavorView POST（核心）

业务：**点一次点赞，再点一次取消点赞**

1. 校验入参，校验博客是否存在

2. 查询当前用户是否已经存在点赞记录

   - 已存在：删除点赞记录，博客点赞计数 `-1`（使用`F表达式`，解决并发计数丢失）

   - 不存在：新增点赞记录，点赞计数 

     ```
     +1
     ```

     ，捕获并发重复点赞的唯一约束异常

     > 重点：`F("favor_count") ±1` 在数据库层面计算，避免多用户同时点赞计数不准的并发问题

## 六、并发&兜底设计

1. 点赞表设置联合唯一约束：数据库层面兜底防重复点赞，序列化器校验+数据库双重保障
2. 点赞计数使用Django F表达式，解决并发超量问题
3. 用户名设置unique，注册接口捕获IntegrityError，防止并发注册同名用户
4. 所有删除、计数操作遵循：**先取出关联对象，再删除主记录**，规避内存对象风险

## 七、项目启动与依赖

### requirements.txt

```
Django==4.2.30
djangorestframework==3.16.1
drf-spectacular==0.30.0
```

### 启动步骤

1. 创建虚拟环境，安装依赖

```
pip install -r requirements.txt
```

2. 数据库迁移

```
python manage.py makemigrations
python manage.py migrate
```

3. 启动服务

```
python manage.py runserver
```

4. 浏览器打开接口文档：```http://127.0.0.1:8000/api/docs/```
5. 备注:本项目 SECRET_KEY 优先读取环境变量 DJANGO_SECRET_KEY；未配置时会自动生成临时密钥，开发环境可直接运行

## 八、待优化（学习备注）

1. 密码使用MD5加密，仅学习演示，生产环境推荐Django自带PBKDF2加密
2. Token永久有效，没有过期时间，生产应该增加过期时间、刷新token逻辑
3. 没有权限控制：只有登录/未登录区分，没有管理员权限
4. 图片只存url，没有对接oss/文件上传接口
5. 评论没有删除、修改接口