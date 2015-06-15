#!/usr/bin/env python

# Copyright 2015 Jason Edelman <jedelman8@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import textfsm

def get_structured_data(template, rawtxt):
    """Returns structured data given raw text using
    TextFSM templates
    """

    # return os.getcwd()
    # return os.path.abspath(__file__)

    path = os.path.dirname(os.path.abspath(__file__)) + '/textfsm_templates/' + template
    fsm = textfsm.TextFSM(open(path))

    # an object is what is being extracted
    # based on the template, it may be one object or multiple
    # as is the case with neighbors, interfaces, etc.
    objects = fsm.ParseText(rawtxt)

    structured_data = []
    for each in objects:
        index = 0
        temp = {}
        for template_value in each:
            temp[fsm.header[index].lower()] = str(template_value)
            index += 1
        structured_data.append(temp)

    return structured_data
