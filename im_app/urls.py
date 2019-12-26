#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from django.urls import path

from im_app.views import login, getRole, sendMsg, mute, recall

urlpatterns = [
    path('login/', login, name='login'),
    path('getRole/', getRole, name='getRole'),
    path('sendMsg/', sendMsg, name='sendMsg'),
    path('mute/', mute, name='mute'),
    path('recall/', recall, name='recall'),
]

