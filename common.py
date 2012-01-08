#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

def ensure_dir(f):
	d = os.path.dirname(f)
	if not os.path.exists(d):
		os.makedirs(d)
