import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_core_security_alias_exports_audit_security():
    from core import Security
    from core.security import Security as CoreSecurityAlias
    from utils.audit_security import AuditTrailSecurity

    assert Security is AuditTrailSecurity
    assert CoreSecurityAlias is AuditTrailSecurity
