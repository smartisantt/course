#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from common.models import User, Role, Permissions, MANAGER_MODIFY_STATUS_CHOICES
from common.rePattern import TEL_PATTERN
from utils.errors import ParamError
from utils.msg import *


class UserBasicSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    @staticmethod
    def get_roles(user):
        return RoleSimpleSerializer(user.roles, many=True).data

    class Meta:
        model = User
        fields = ('uuid', 'userNum', 'nickName', 'roles', 'tel', 'managerStatus', 'createTime')


# class UserPostSerializer(serializers.Serializer):
#     userID = serializers.CharField(max_length=64, required=True,
#                                    error_messages={
#                                        'max_length': 'userID长度不要大于64个字符',
#                                        'required': 'userID必填',
#                                    }
#                                    )
#     nickName = serializers.CharField(min_length=2, max_length=14, required=True,
#                                      error_messages={
#                                          'min_length': '昵称长度不要少于2个字符',
#                                          'max_length': '昵称长度不要大于14个字符',
#                                          'required': '昵称必填'
#                                      })
#     tel = serializers.CharField(required=True, error_messages={'required': "电话不能为空"})
#     roles = serializers.SlugRelatedField(many=True,
#                                          slug_field="uuid",
#                                          queryset=Role.objects.exclude(status=3),
#                                          required=True,
#                                          error_messages={
#                                              'required': "角色不能为空"
#                                          })
#
#     def validate(self, attrs):
#         # 逻辑校验, 校验电话（格式，是否重复） 昵称（是否重复）
#         if User.objects.filter(tel=attrs['tel']).exclude(status=2).exists():
#             raise ParamError(USER_TEL_EXISTS)
#         if User.objects.filter(nickName=attrs['nickName']).exclude(status=2).exists():
#             raise ParamError(USER_NICKNAME_EXISTS)
#         if not TEL_PATTERN.match(attrs['tel']):
#             raise ParamError(USER_TEL_ERROR)
#         return attrs
#
#     def create_user(self, validated_data):
#         roles = validated_data.pop('roles')
#         if not roles:
#             raise ParamError("用户的角色不能为空")
#
#         validated_data['managerStatus'] = 1
#         user = User.objects.create(**validated_data)
#         roles = Role.objects.filter(uuid__in=roles).all()
#         user.roles.add(*roles)
#         res = {
#             'user': UserBasicSerializer(user).data
#         }
#         return res


class UserUpdateSerializer(serializers.Serializer):
    nickName = serializers.CharField(min_length=2, max_length=14, required=True,
                                     error_messages={
                                         'min_length': '昵称长度不要少于2个字符',
                                         'max_length': '昵称长度不要大于14个字符',
                                         'required': '昵称必填'
                                     })
    roles = serializers.SlugRelatedField(many=True,
                                         slug_field="uuid",
                                         queryset=Role.objects.exclude(status=3),
                                         required=True,
                                         error_messages={
                                             'required': "角色不能为空"
                                         })
    managerStatus = serializers.ChoiceField(choices=MANAGER_MODIFY_STATUS_CHOICES, required=True,
                                            error_messages={'required': "用户状态必填"})

    def update_user(self, instance, validate_data):
        instance.nickName = validate_data.get('nickName')
        if User.objects.filter(nickName=instance.nickName, status__in=[1,3,4]).exclude(uuid=instance.uuid).exists():
            raise ParamError(USER_NICKNAME_EXISTS)

        instance.managerStatus = validate_data['managerStatus']

        if not validate_data.get('roles'):
            raise ParamError("用户角色不能为空")

        roles = Role.objects.filter(uuid__in=validate_data.get('roles')).all()
        instance.roles.clear()
        instance.roles.add(*roles)
        instance.save()

        res = {
            'user': UserBasicSerializer(instance).data
        }
        return res


# 角色序列化
class RoleSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = ('uuid', 'name', 'remark')


class RoleBasicSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    @staticmethod
    def get_permissions(role):
        # return PermissionsBasicSerializer(role.permissions, many=True).data
        return PermissionsForRoleSerializer(role.permissions, many=True).data

    class Meta:
        model = Role
        fields = ('uuid', 'name', 'remark', 'permissions')


class RolePostSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=12, required=True,
                                     error_messages={
                                         'min_length': '角色名字不要小于2个字',
                                         'max_length': '角色名字不要大于12个字',
                                         'required': '角色名字必填'
                                     })
    remark = serializers.CharField(max_length=512, required=False,
                                   error_messages={
                                        'max_length': '角色备注长度大于512个字',
                                    })
    permissions = serializers.SlugRelatedField(many=True,
                                               slug_field="uuid",
                                               required=True,
                                               queryset=Permissions.objects.all(),
                                               error_messages={
                                                   'required': '权限不能为空'
                                               })

    def validate(self, attrs):
        if Role.objects.filter(name=attrs['name'], status__in=[1,2]).exists():
            raise ParamError(ROLE_NAME_EXISTS)
        # if Role.objects.filter(remark=attrs['remark']).exclude(status=3).exists():
        #     raise ParamError(ROLE_REMARK_EXISTS)
        return attrs

    def create_role(self, validated_data):
        permissions = validated_data.pop('permissions')
        if not permissions:
            raise ParamError("权限不能为空")
        # 创建角色
        role = Role.objects.create(**validated_data)

        permissions = Permissions.objects.filter(uuid__in=permissions).all()
        # 添加中间表信息
        role.permissions.add(*permissions)

        res = {
            'role': RoleBasicSerializer(role).data
        }
        return res


class RoleUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=12, required=True,
                                     error_messages={
                                         'min_length': '角色名字不要小于2个字',
                                         'max_length': '角色名字不要大于12个字',
                                         'required': '角色名字必填'
                                     })

    remark = serializers.CharField(min_length=2, max_length=12, required=True,
                                   error_messages={
                                         'min_length': '角色名字不要小于2个字',
                                         'max_length': '角色名字不要大于12个字',
                                         'required': '角色名字必填'
                                     })

    permissions = serializers.SlugRelatedField(many=True,
                                               slug_field="uuid",
                                               required=True,
                                               queryset=Permissions.objects.filter(enable=True),
                                               error_messages={
                                                   'required': '权限不能为空'
                                               })

    def update_role(self, instance, validate_data):
        qs = Role.objects.filter(name=validate_data['name'], status__in=[1,2]).exclude(uuid=instance.uuid)
        if qs.exists():
            raise ParamError(ROLE_NAME_EXISTS)

        instance.name = validate_data['name']
        instance.remark = validate_data['remark']
        permissions = Permissions.objects.filter(uuid__in=validate_data.get('permissions'), enable=True).all()
        instance.permissions.clear()
        instance.permissions.add(*permissions)
        instance.save()

        res = {
            'permission': RoleBasicSerializer(instance).data
        }
        return res


# 三级目录序列化
# class PermissionsBasicSerializer3(serializers.ModelSerializer):
#
#     class Meta:
#         model = Permissions
#         fields = "__all__"


# 二级目录序列化
class PermissionsBasicSerializer2(serializers.ModelSerializer):

    # subMenu = PermissionsBasicSerializer3(many=True)
    menuUrl = serializers.SerializerMethodField()

    @staticmethod
    def get_menuUrl(obj):
        return '/' + obj.url.split('/')[-1]

    class Meta:
        model = Permissions
        fields = ('uuid', 'sortNum', 'menuName', 'icon', 'menuUrl')


# 一级目录序列化
class PermissionsBasicSerializer(serializers.ModelSerializer):
    # subMenu = PermissionsBasicSerializer2(many=True)
    subMenu = serializers.SerializerMethodField()
    menuUrl = serializers.SerializerMethodField()

    @staticmethod
    def get_subMenu(obj):
        queryset = obj.subMenu.all().order_by("sortNum")
        return PermissionsBasicSerializer2(queryset, many=True).data

    @staticmethod
    def get_menuUrl(obj):
        return '/'+obj.url.split('/')[-1]

    class Meta:
        model = Permissions
        fields = ('uuid', 'sortNum', 'menuName', 'icon', 'menuUrl', 'subMenu')


# 角色关联权限的序列化
class PermissionsForRoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permissions
        fields = ('uuid', 'sortNum', 'menuName', 'icon')


# 用户名模糊搜索
class UserSearchSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    @staticmethod
    def get_roles(user):
        return RoleSimpleSerializer(user.roles, many=True).data

    class Meta:
        model = User
        fields = ('uuid', 'nickName', 'tel', 'managerStatus', 'roles')


# 已有用户分配角色
class UserRolesUpdateSerializer(serializers.Serializer):
    roles = serializers.SlugRelatedField(many=True,
                                         slug_field="uuid",
                                         queryset=Role.objects.exclude(status=3),
                                         required=True,
                                         error_messages={
                                             'required': "角色不能为空"
                                         })
    managerStatus = serializers.ChoiceField(choices=MANAGER_MODIFY_STATUS_CHOICES, required=True,
                                            error_messages={'required': "账号状态必填"})

    def update_user(self, instance, validate_data):
        instance.userRoles = 1              # 角色变为管理员
        instance.managerStatus = 1
        if not instance.passwd:
            instance.passwd = make_password("123456")

        if not validate_data.get('roles'):
            raise ParamError("用户角色不能为空")

        roles = validate_data.pop('roles')
        instance.roles.clear()
        instance.roles.set(roles)
        instance.save()
        return True


# 从无到有添加管理员
class UserRolesPostSerializer(serializers.Serializer):
    nickName = serializers.CharField(min_length=2, max_length=14, required=True,
                                     error_messages={
                                         'min_length': '昵称长度不要少于2个字符',
                                         'max_length': '昵称长度不要大于14个字符',
                                         'required': '昵称必填'
                                     })
    passwd = serializers.CharField(min_length=6, max_length=16, required=True,
                                     error_messages={
                                         'min_length': '密码长度不要少于6个字符',
                                         'max_length': '密码长度不要大于16个字符',
                                         'required': '密码必填'
                                     })
    tel = serializers.CharField(required=True, error_messages={'required': "电话不能为空"})
    roles = serializers.SlugRelatedField(many=True,
                                         slug_field="uuid",
                                         queryset=Role.objects.exclude(status=3),
                                         required=True,
                                         error_messages={
                                             'required': "角色不能为空"
                                         })
    managerStatus = serializers.ChoiceField(choices=MANAGER_MODIFY_STATUS_CHOICES, required=True,
                                            error_messages={'required': "账号状态必填"})

    def validate(self, attrs):
        # 逻辑校验
        if User.objects.filter(tel=attrs['tel']).exclude(status=2).exists():
            raise ParamError(USER_TEL_EXISTS)
        if User.objects.filter(tel=attrs['nickName']).exclude(status=2).exists():
            raise ParamError(USER_NICKNAME_EXISTS)
        if not TEL_PATTERN.match(attrs['tel']):
            raise ParamError(USER_TEL_ERROR)
        if not attrs['roles']:
            raise ParamError("用户的角色不能为空")
        return attrs

    def create_user(self, validated_data):
        roles = validated_data.pop('roles')
        validated_data['passwd'] = make_password(validated_data['passwd'])
        validated_data['userSource'] = 2        # 用户来源 为 新注册
        validated_data['registerPlatform'] = 5  # 注册平台 为 后台
        user = User.objects.create(**validated_data)
        user.roles.set(roles)
        return True


# 二级目录序列化
class UserPermissionsBasicSerializer2(serializers.ModelSerializer):

    # subMenu = PermissionsBasicSerializer3(many=True)
    menuUrl = serializers.SerializerMethodField()

    @staticmethod
    def get_menuUrl(obj):
        return '/' + obj.url.split('/')[-1]

    class Meta:
        model = Permissions
        fields = ('uuid', 'sortNum', 'menuName', 'icon', 'menuUrl')


# 一级目录序列化
class UserPermissionsBasicSerializer(serializers.ModelSerializer):
    # subMenu = PermissionsBasicSerializer2(many=True)
    subMenu = serializers.SerializerMethodField()
    menuUrl = serializers.SerializerMethodField()


    def get_subMenu(self, obj):
        queryset = obj.subMenu.filter(uuid__in=self.context['data']).order_by("sortNum")
        return PermissionsBasicSerializer2(queryset, many=True).data

    @staticmethod
    def get_menuUrl(obj):
        return '/'+obj.url.split('/')[-1]

    class Meta:
        model = Permissions
        fields = ('uuid', 'sortNum', 'menuName', 'icon', 'menuUrl', 'subMenu')