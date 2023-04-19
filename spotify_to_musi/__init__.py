from __future__ import annotations

import warnings

import rich.traceback

rich.traceback.install()


# requests is installed as a sub-dependency of pyfy (& maybe more packages that are sync and async)
# pyfy imports requests even when it's not being used which will cause a  `RequestsDependencyWarning` to be raised on older versions of python
# there should be no issue with ignoring this warning as it's only raised through requests which is not actually being used

# i wasn't able to import `RequestsDependencyWarning` from `requests.exceptions` as it would raise the error immediately
# before the warning filter could be applied
# but it hopefully should be okay ignoring all warnings :3

warnings.filterwarnings("ignore")
