"""
Deprecated module. Image records are no longer stored in a separate table and
local /media saving is not supported. This file remains as a stub to avoid
import errors if referenced inadvertently.

All image uploads must go through Object Storage (S3) via /api/images/save.
"""

__all__ = ()
