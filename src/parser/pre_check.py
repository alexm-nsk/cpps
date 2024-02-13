from .error import SisalError
import re


def pre_check(src_code):
    """these checks are performed before source code is parsed"""
    # remove comments:
    src_code = re.sub("/\?[^?/]*\?/", lambda match: " "*len(match.group(0)), src_code)
    return src_code
