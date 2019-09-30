# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os


def certificate():
    
    return __file_path('certificate.pem')

def plainkey():
    
    return __file_path('plainkey.pem')

def __file_path(filename):
    
    cwd = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(cwd, filename)
