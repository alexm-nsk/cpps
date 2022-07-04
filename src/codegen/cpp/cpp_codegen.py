#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
"""C++ code generation"""

CPP_MODULE_HEADER = """\
#include <stdio.h>
#include <vector>
#include <iostream>
#include <fstream>
#include <json/json.h>// uses jsoncpp library

using namespace std;

template <typename Iterable>

Json::Value iterable_to_json(Iterable const& cont) {
    Json::Value v;
    for (auto&& element: cont) {
        v.append(element);
    }
    return v;
}

template <typename I>
vector<I> operator || (const vector<I>& lhs, const vector<I>& rhs){
    vector<I> result = lhs;
    result.insert(result.end(), rhs.begin(), rhs.end());
    return result;
}

inline int size (vector<int> A)
{
    return A.size();
}

//------------------------------------------------------------


"""


class CppModule:

    def __init__(self, name: str, functions: dict, definitions: list = []):
        self.modules = []
        for name, f in functions.items():
            self.modules += [f.to_cpp()]

    def __str__(self):
        return CPP_MODULE_HEADER + "\n\n".join(self.modules)
