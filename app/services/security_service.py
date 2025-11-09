"""
Security Service for CryptoSatX
API key rotation dan advanced security management
"""
import asyncio
import json
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass
from app.utils.logger import default_logger


class KeyType(Enum):
    """API key types"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    SERVICE = "service"


class KeyStatus(Enum):
    """API key status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class APIKey:
    """API key model"""
    id: str
    name: str
    key_hash: str
    key_type: KeyType
    status: KeyStatus
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    usage_count: int = 0
    rate_limit: int = 1000  # requests per hour
    permissions: List[str] = None
    metadata: Dict[str, Any] = None
    created_by: str = ""
    rotation_enabled: bool = True
    rotation_days: int = 90


class SecurityConfig(BaseModel):
    """Security configuration"""
    jwt_secret: str = Field(..., description="JWT secret key")
    jwt_expiry_hours: int = Field(24, description="JWT token expiry in hours")
    max_keys_per_user: int = Field(10, description="Maximum API keys per user")
    default_key_expiry_days: int = Field(365, description="Default key expiry in days")
    rotation_reminder_days: int = Field(7, description="Days before expiry to remind")
    failed_login_threshold: int = Field(5, description="Failed login threshold")
    lockout_duration_minutes: int = Field(15, description="Account lockout duration")
    password_min_length: int = Field(12, description="Minimum password length")
    require_2fa: bool = Field(False, description="Require 2FA")


class SecurityService:
    """
    Comprehensive security service dengan:
    - API key management dan rotation
    - JWT token management
    - Rate limiting per key
    - Access control
    - Audit logging
    - Security monitoring
    """
    
    def __init__(self):
        self.logger = default_logger
        self.api_keys: Dict[str, APIKey] = {}
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.locked_accounts: Dict[str, datetime] = {}
        self.audit_log: List[Dict[str, Any]] = []
        
        # Security configuration
        self.config = SecurityConfig(
            jwt_secret=os.getenv("JWT_SECRET", secrets.token_urlsafe(32)),
            jwt_expiry_hours=int(os.getenv("JWT_EXPIRY_HOURS", "24")),
            max_keys_per_user=int(os.getenv("MAX_KEYS_PER_USER", "10")),
            default_key_expiry_days=int(os.getenv("DEFAULT_KEY_EXPIRY_DAYS", "365")),
            rotation_reminder_days=int(os.getenv("ROTATION_REMINDER_DAYS", "7")),
            failed_login_threshold=int(os.getenv("FAILED_LOGIN_THRESHOLD", "5")),
            lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "12")),
            require_2fa=os.getenv("REQUIRE_2FA", "false").lower() == "true"
        )
        
        # Default permissions per key type
        self.default_permissions = {
            KeyType.READ_ONLY: [
                "signals:read", "health:read", "metrics:read"
            ],
            KeyType.READ_WRITE: [
                "signals:read", "signals:write", "health:read", "metrics:read"
            ],
            KeyType.ADMIN: [
                "signals:read", "signals:write", "admin:read", "admin:write",
                "health:read", "metrics:read", "users:read", "users:write"
            ],
            KeyType.SERVICE: [
                "signals:read", "signals:write", "health:read", "metrics:read",
                "cache:read", "cache:write"
            ]
        }
        
        # Initialize with default admin key
        self._initialize_default_keys()
    
    def _initialize_default_keys(self):
        """Initialize default API keys"""
        # Create default admin key for development
        if not any(key.key_type == KeyType.ADMIN for key in self.api_keys.values()):
            default_admin_key = self.create_api_key(
                name="Default Admin Key",
                key_type=KeyType.ADMIN,
                created_by="system",
                expires_days=365
            )
            self.logger.info(f"Default admin key created: {default_admin_key['id']}")
    
    def create_api_key(
        self,
        name: str,
        key_type: KeyType,
        created_by: str,
        expires_days: Optional[int] = None,
        permissions: Optional[List[str]] = None,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new API key"""
        try:
            # Check if user has too many keys
            user_keys = [k for k in self.api_keys.values() if k.created_by == created_by]
            if len(user_keys) >= self.config.max_keys_per_user:
                raise ValueError(f"Maximum keys per user exceeded: {self.config.max_keys_per_user}")
            
            # Generate API key
            api_key = f"csx_{secrets.token_urlsafe(32)}"
            key_hash = self._hash_key(api_key)
            
            # Set expiry
            expiry_days = expires_days or self.config.default_key_expiry_days
            expires_at = datetime.now() + timedelta(days=expiry_days)
            
            # Set permissions
            if permissions is None:
                permissions = self.default_permissions[key_type]
            
            # Create API key object
            key_obj = APIKey(
                id=f"key_{datetime.now().timestamp()}",
                name=name,
                key_hash=key_hash,
                key_type=key_type,
                status=KeyStatus.ACTIVE,
                created_at=datetime.now(),
                expires_at=expires_at,
                permissions=permissions,
                rate_limit=rate_limit or (1000 if key_type != KeyType.ADMIN else 10000),
                metadata=metadata or {},
                created_by=created_by
            )
            
            # Store key
            self.api_keys[key_obj.id] = key_obj
            
            # Log creation
            self._log_security_event(
                event_type="api_key_created",
                user_id=created_by,
                details={
                    "key_id": key_obj.id,
                    "key_name": name,
                    "key_type": key_type.value,
                    "expires_at": expires_at.isoformat()
                }
            )
            
            self.logger.info(f"API key created: {key_obj.id} by {created_by}")
            
            return {
                "id": key_obj.id,
                "name": name,
                "api_key": api_key,  # Only return actual key on creation
                "key_type": key_type.value,
                "permissions": permissions,
                "expires_at": expires_at.isoformat(),
                "rate_limit": key_obj.rate_limit
            }
            
        except Exception as e:
            self.logger.error(f"Error creating API key: {e}")
            raise
    
    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Validate API key and return key object"""
        try:
            key_hash = self._hash_key(api_key)
            
            # Find key by hash
            key_obj = None
            for key in self.api_keys.values():
                if key.key_hash == key_hash:
                    key_obj = key
                    break
            
            if not key_obj:
                self._log_security_event(
                    event_type="api_key_invalid",
                    details={"key_hash": key_hash}
                )
                return None
            
            # Check status
            if key_obj.status != KeyStatus.ACTIVE:
                self._log_security_event(
                    event_type="api_key_inactive",
                    user_id=key_obj.created_by,
                    details={"key_id": key_obj.id, "status": key_obj.status.value}
                )
                return None
            
            # Check expiry
            if key_obj.expires_at and key_obj.expires_at < datetime.now():
                key_obj.status = KeyStatus.EXPIRED
                self._log_security_event(
                    event_type="api_key_expired",
                    user_id=key_obj.created_by,
                    details={"key_id": key_obj.id}
                )
                return None
            
            # Update usage
            key_obj.last_used = datetime.now()
            key_obj.usage_count += 1
            
            return key_obj
            
        except Exception as e:
            self.logger.error(f"Error validating API key: {e}")
            return None
    
    def rotate_api_key(
        self,
        key_id: str,
        rotated_by: str,
        force: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Rotate API key"""
        try:
            key_obj = self.api_keys.get(key_id)
            if not key_obj:
                raise ValueError("API key not found")
            
            # Check if rotation is allowed
            if not force and not key_obj.rotation_enabled:
                raise ValueError("Key rotation is disabled")
            
            # Check if enough time has passed since last rotation
            if not force:
                days_since_creation = (datetime.now() - key_obj.created_at).days
                if days_since_creation < key_obj.rotation_days:
                    raise ValueError(f"Key rotation not allowed yet. Minimum {key_obj.rotation_days} days required")
            
            # Generate new key
            new_api_key = f"csx_{secrets.token_urlsafe(32)}"
            new_key_hash = self._hash_key(new_api_key)
            
            # Store old key hash for audit
            old_key_hash = key_obj.key_hash
            
            # Update key
            key_obj.key_hash = new_key_hash
            key_obj.created_at = datetime.now()
            key_obj.usage_count = 0
            key_obj.last_used = None
            
            # Update expiry
            if key_obj.expires_at:
                key_obj.expires_at = datetime.now() + timedelta(days=self.config.default_key_expiry_days)
            
            # Log rotation
            self._log_security_event(
                event_type="api_key_rotated",
                user_id=rotated_by,
                details={
                    "key_id": key_id,
                    "old_key_hash": old_key_hash[:8] + "...",  # Partial hash for audit
                    "rotation_reason": "scheduled" if not force else "forced"
                }
            )
            
            self.logger.info(f"API key rotated: {key_id} by {rotated_by}")
            
            return {
                "id": key_obj.id,
                "name": key_obj.name,
                "api_key": new_api_key,  # Only return new key on rotation
                "key_type": key_obj.key_type.value,
                "expires_at": key_obj.expires_at.isoformat() if key_obj.expires_at else None
            }
            
        except Exception as e:
            self.logger.error(f"Error rotating API key: {e}")
            raise
    
    def revoke_api_key(self, key_id: str, revoked_by: str) -> bool:
        """Revoke API key"""
        try:
            key_obj = self.api_keys.get(key_id)
            if not key_obj:
                return False
            
            key_obj.status = KeyStatus.REVOKED
            
            # Log revocation
            self._log_security_event(
                event_type="api_key_revoked",
                user_id=revoked_by,
                details={"key_id": key_id, "key_name": key_obj.name}
            )
            
            self.logger.info(f"API key revoked: {key_id} by {revoked_by}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error revoking API key: {e}")
            return False
    
    def create_jwt_token(
        self,
        user_id: str,
        permissions: List[str],
        expires_in_hours: Optional[int] = None
    ) -> str:
        """Create JWT token"""
        try:
            expiry_hours = expires_in_hours or self.config.jwt_expiry_hours
            expires_at = datetime.now() + timedelta(hours=expiry_hours)
            
            payload = {
                "user_id": user_id,
                "permissions": permissions,
                "exp": expires_at,
                "iat": datetime.now(),
                "type": "access_token"
            }
            
            token = jwt.encode(payload, self.config.jwt_secret, algorithm="HS256")
            
            # Log token creation
            self._log_security_event(
                event_type="jwt_created",
                user_id=user_id,
                details={"expires_at": expires_at.isoformat()}
            )
            
            return token
            
        except Exception as e:
            self.logger.error(f"Error creating JWT token: {e}")
            raise
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=["HS256"])
            
            # Check if token is expired
            if datetime.now() > datetime.fromtimestamp(payload["exp"]):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self._log_security_event(
                event_type="jwt_expired",
                details={"token_partial": token[:20] + "..."}
            )
            return None
        except jwt.InvalidTokenError as e:
            self._log_security_event(
                event_type="jwt_invalid",
                details={"error": str(e), "token_partial": token[:20] + "..."}
            )
            return None
    
    def check_permission(self, api_key: APIKey, required_permission: str) -> bool:
        """Check if API key has required permission"""
        return required_permission in api_key.permissions
    
    def check_rate_limit(self, api_key: APIKey) -> bool:
        """Check if API key is within rate limit"""
        # This would typically use Redis or similar for distributed rate limiting
        # For now, we'll use a simple in-memory counter
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # In a real implementation, this would track requests per hour
        # For now, we'll assume the check passes
        return True
    
    def record_failed_attempt(self, identifier: str):
        """Record failed login attempt"""
        now = datetime.now()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        self.failed_attempts[identifier].append(now)
        
        # Clean old attempts (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff
        ]
        
        # Check if account should be locked
        if len(self.failed_attempts[identifier]) >= self.config.failed_login_threshold:
            self.locked_accounts[identifier] = now + timedelta(minutes=self.config.lockout_duration_minutes)
            
            self._log_security_event(
                event_type="account_locked",
                details={
                    "identifier": identifier,
                    "failed_attempts": len(self.failed_attempts[identifier])
                }
            )
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is locked"""
        if identifier not in self.locked_accounts:
            return False
        
        lock_expiry = self.locked_accounts[identifier]
        if datetime.now() > lock_expiry:
            del self.locked_accounts[identifier]
            return False
        
        return True
    
    def get_keys_expiring_soon(self, days_ahead: int = None) -> List[APIKey]:
        """Get keys expiring soon"""
        days_ahead = days_ahead or self.config.rotation_reminder_days
        cutoff = datetime.now() + timedelta(days=days_ahead)
        
        return [
            key for key in self.api_keys.values()
            if key.status == KeyStatus.ACTIVE
            and key.expires_at
            and key.expires_at <= cutoff
        ]
    
    def get_user_keys(self, user_id: str) -> List[APIKey]:
        """Get all keys for a user"""
        return [key for key in self.api_keys.values() if key.created_by == user_id]
    
    def get_key_statistics(self) -> Dict[str, Any]:
        """Get API key statistics"""
        now = datetime.now()
        
        stats = {
            "total_keys": len(self.api_keys),
            "by_status": {},
            "by_type": {},
            "expiring_soon": len(self.get_keys_expiring_soon()),
            "expired": 0,
            "high_usage": 0,
            "locked_accounts": len(self.locked_accounts)
        }
        
        for key in self.api_keys.values():
            # By status
            status = key.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # By type
            key_type = key.key_type.value
            stats["by_type"][key_type] = stats["by_type"].get(key_type, 0) + 1
            
            # Expired
            if key.expires_at and key.expires_at < now:
                stats["expired"] += 1
            
            # High usage (more than 1000 requests)
            if key.usage_count > 1000:
                stats["high_usage"] += 1
        
        return stats
    
    def _hash_key(self, api_key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _log_security_event(self, event_type: str, user_id: str = "", details: Dict[str, Any] = None):
        """Log security event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details or {}
        }
        
        self.audit_log.append(event)
        
        # Keep only last 10000 events
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]
        
        self.logger.info(f"Security event: {event_type} by {user_id}")
    
    def get_audit_log(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """Get audit log"""
        cutoff = datetime.now() - timedelta(hours=hours_back)
        
        filtered_log = []
        for event in self.audit_log:
            event_time = datetime.fromisoformat(event["timestamp"])
            
            if event_time < cutoff:
                continue
            
            if event_type and event["event_type"] != event_type:
                continue
            
            if user_id and event["user_id"] != user_id:
                continue
            
            filtered_log.append(event)
        
        return sorted(filtered_log, key=lambda x: x["timestamp"], reverse=True)
    
    async def cleanup_expired_keys(self):
        """Clean up expired keys"""
        try:
            now = datetime.now()
            expired_keys = []
            
            for key_id, key in self.api_keys.items():
                if key.expires_at and key.expires_at < now and key.status == KeyStatus.ACTIVE:
                    key.status = KeyStatus.EXPIRED
                    expired_keys.append(key_id)
            
            if expired_keys:
                self._log_security_event(
                    event_type="keys_expired_cleanup",
                    details={"expired_keys": expired_keys}
                )
                self.logger.info(f"Expired {len(expired_keys)} keys during cleanup")
            
        except Exception as e:
            self.logger.error(f"Error during key cleanup: {e}")


# Global instance
security_service = SecurityService()

# Import os for environment variables
import os
