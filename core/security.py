"""Backward-compatible security module wrapper."""

from utils.audit_security import AuditTrailSecurity

# Backward compatibility: legacy imports expect `core.security.Security`
Security = AuditTrailSecurity

__all__ = ["AuditTrailSecurity", "Security"]
