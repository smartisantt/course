#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
import json


from common.models import Permissions, Role, Tags
from parentscourse_server.settings import BASE_DIR


def init_permissions():
    json_file = BASE_DIR + '/manager_auth/permissions.json'
    with open(json_file, encoding='utf-8') as f:
        json_str = f.read()
        json_data = json.loads(json_str)

        create_list = []
        for item in json_data:
            permission = Permissions()
            permission.uuid = item['uuid']
            permission.icon = item['icon']
            permission.url = item['url']
            permission.remark = item['remark']
            permission.menuName = item['menuName']
            permission.parentUuid_id = item['parentUuid_id']
            permission.enable = True
            permission.sortNum = item['sortNum']
            create_list.append(permission)
        Permissions.objects.bulk_create(create_list)


def init_roles():
    json_file = BASE_DIR + '/manager_auth/roles.json'
    with open(json_file, encoding='utf-8') as f:
        json_str = f.read()
        json_data = json.loads(json_str)

        create_list = []
        for item in json_data:
            role = Role()
            role.uuid = item['uuid']
            role.remark = item['remark']
            role.name = item['name']
            role.status = item['status']
            create_list.append(role)
        Role.objects.bulk_create(create_list)


def init_role_permission():
    json_file = BASE_DIR + '/manager_auth/role_permission.json'
    with open(json_file, encoding='utf-8') as f:
        json_str = f.read()
        json_data = json.loads(json_str)

        for item in json_data:
            role = Role.objects.filter(uuid=item["role_id"]).first()
            if role:
                role.permissions.add(item['permissions_id'])


def init_tags():
    json_file = BASE_DIR + '/manager_auth/tags.json'
    with open(json_file, encoding='utf-8') as f:
        json_str = f.read()
        json_data = json.loads(json_str)

        create_list = []
        for item in json_data:
            tag = Tags()
            tag.uuid = item['uuid']
            tag.weight = item['weight']
            tag.level = item['level']
            tag.tagType = item['tagType']
            tag.name = item['name']
            # tag.parentUuid_id = item['parentUuid_id']
            create_list.append(tag)
        Tags.objects.bulk_create(create_list)
        for item in json_data:
            if item['parentUuid_id']:
                tag = Tags.objects.filter(uuid=item['uuid']).first()
                if tag:
                    tag.parentUuid_id = item['parentUuid_id']
                    tag.save()


if __name__ == '__main__':
    pass