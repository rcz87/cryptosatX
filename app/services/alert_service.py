"""
Alert Service for CryptoSatX
Proactive monitoring dengan Slack/Telegram integration
"""
import asyncio
import json
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass
from app.utils.logger import default_logger


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert delivery channels"""
    SLACK = "slack"
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str  # Python expression
    severity: AlertSeverity
    channels: List[AlertChannel]
    enabled: bool = True
    cooldown_minutes: int = 15
    last_triggered: Optional[datetime] = None
    message_template: str = ""
    metadata: Dict[str, Any] = None


class Alert(BaseModel):
    """Alert model"""
    id: str = Field(default_factory=lambda: f"alert_{datetime.now().timestamp()}")
    rule_name: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertService:
    """
    Comprehensive alert system dengan:
    - Multiple notification channels (Slack, Telegram, Email, Webhook)
    - Custom alert rules dengan conditions
    - Rate limiting dan cooldown
    - Alert escalation
    - Historical tracking
    """
    
    def __init__(self):
        self.logger = default_logger
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Channel configurations
        self.channel_configs = {
            AlertChannel.SLACK: {
                "webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
                "enabled": bool(os.getenv("SLACK_WEBHOOK_URL"))
            },
            AlertChannel.TELEGRAM: {
                "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
                "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
                "enabled": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))
            },
            AlertChannel.EMAIL: {
                "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "username": os.getenv("SMTP_USERNAME"),
                "password": os.getenv("SMTP_PASSWORD"),
                "from_email": os.getenv("FROM_EMAIL"),
                "to_emails": os.getenv("ALERT_EMAILS", "").split(","),
                "enabled": bool(os.getenv("SMTP_USERNAME") and os.getenv("SMTP_PASSWORD"))
            },
            AlertChannel.WEBHOOK: {
                "url": os.getenv("ALERT_WEBHOOK_URL"),
                "enabled": bool(os.getenv("ALERT_WEBHOOK_URL"))
            }
        }
        
        # Default alert rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                name="high_error_rate",
                condition="error_rate > 0.05",  # 5% error rate
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.SLACK, AlertChannel.TELEGRAM],
                message_template="🚨 High Error Rate: {error_rate:.2%} (threshold: 5%)",
                cooldown_minutes=10
            ),
            AlertRule(
                name="slow_response_time",
                condition="avg_response_time > 2.0",  # 2 seconds
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.SLACK],
                message_template="⚠️ Slow Response Time: {avg_response_time:.2f}s",
                cooldown_minutes=15
            ),
            AlertRule(
                name="low_signal_accuracy",
                condition="signal_accuracy < 0.4",  # 40% accuracy
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
                message_template="📉 Low Signal Accuracy: {signal_accuracy:.2%}",
                cooldown_minutes=30
            ),
            AlertRule(
                name="high_memory_usage",
                condition="memory_usage > 0.85",  # 85% memory usage
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.SLACK, AlertChannel.TELEGRAM, AlertChannel.EMAIL],
                message_template="💾 High Memory Usage: {memory_usage:.2%}",
                cooldown_minutes=5
            ),
            AlertRule(
                name="api_rate_limit",
                condition="rate_limit_hits > 100",  # 100 rate limit hits
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.SLACK],
                message_template="🚦 High Rate Limit Hits: {rate_limit_hits}",
                cooldown_minutes=15
            ),
            AlertRule(
                name="external_api_failure",
                condition="external_api_error_rate > 0.1",  # 10% external API error rate
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.SLACK, AlertChannel.TELEGRAM],
                message_template="🔌 External API Failure: {external_api_error_rate:.2%}",
                cooldown_minutes=10
            ),
            AlertRule(
                name="database_connection_pool",
                condition="db_connections_active > db_connections_max * 0.9",  # 90% of max connections
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
                message_template="🗄️ Database Connection Pool: {db_connections_active}/{db_connections_max}",
                cooldown_minutes=15
            ),
            AlertRule(
                name="cache_hit_ratio_low",
                condition="cache_hit_ratio < 0.7",  # 70% cache hit ratio
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.SLACK],
                message_template="💽 Low Cache Hit Ratio: {cache_hit_ratio:.2%}",
                cooldown_minutes=30
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.name] = rule
    
    async def check_alerts(self, metrics: Dict[str, Any]):
        """Check all alert rules against current metrics"""
        try:
            for rule_name, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                # Check cooldown
                if rule.last_triggered:
                    cooldown_expired = datetime.now() - rule.last_triggered > timedelta(minutes=rule.cooldown_minutes)
                    if not cooldown_expired:
                        continue
                
                # Evaluate condition
                try:
                    # Create safe namespace for evaluation
                    safe_metrics = {k: v for k, v in metrics.items() if isinstance(v, (int, float, bool, str))}
                    
                    # Evaluate condition
                    condition_met = eval(rule.condition, {"__builtins__": {}}, safe_metrics)
                    
                    if condition_met:
                        await self._trigger_alert(rule, metrics)
                        
                except Exception as e:
                    self.logger.error(f"Error evaluating alert rule {rule_name}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
    
    async def _trigger_alert(self, rule: AlertRule, metrics: Dict[str, Any]):
        """Trigger alert for rule"""
        try:
            # Update last triggered
            rule.last_triggered = datetime.now()
            
            # Format message
            try:
                message = rule.message_template.format(**metrics)
            except KeyError:
                message = f"Alert triggered: {rule.name}"
            
            # Create alert
            alert = Alert(
                rule_name=rule.name,
                severity=rule.severity,
                title=f"Alert: {rule.name}",
                message=message,
                metadata=metrics.copy()
            )
            
            # Store alert
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)
            
            # Send notifications
            await self._send_notifications(alert, rule.channels)
            
            self.logger.warning(f"Alert triggered: {rule.name} - {message}")
            
        except Exception as e:
            self.logger.error(f"Error triggering alert: {e}")
    
    async def _send_notifications(self, alert: Alert, channels: List[AlertChannel]):
        """Send alert notifications to specified channels"""
        tasks = []
        
        for channel in channels:
            if self.channel_configs[channel]["enabled"]:
                if channel == AlertChannel.SLACK:
                    tasks.append(self._send_slack_notification(alert))
                elif channel == AlertChannel.TELEGRAM:
                    tasks.append(self._send_telegram_notification(alert))
                elif channel == AlertChannel.EMAIL:
                    tasks.append(self._send_email_notification(alert))
                elif channel == AlertChannel.WEBHOOK:
                    tasks.append(self._send_webhook_notification(alert))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_slack_notification(self, alert: Alert):
        """Send Slack notification"""
        try:
            webhook_url = self.channel_configs[AlertChannel.SLACK]["webhook_url"]
            
            # Color based on severity
            color_map = {
                AlertSeverity.LOW: "good",
                AlertSeverity.MEDIUM: "warning",
                AlertSeverity.HIGH: "danger",
                AlertSeverity.CRITICAL: "#ff0000"
            }
            
            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "warning"),
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "short": True
                            }
                        ],
                        "footer": "CryptoSatX Alerts",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Slack notification sent: {alert.id}")
                    else:
                        self.logger.error(f"Slack notification failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}")
    
    async def _send_telegram_notification(self, alert: Alert):
        """Send Telegram notification"""
        try:
            bot_token = self.channel_configs[AlertChannel.TELEGRAM]["bot_token"]
            chat_id = self.channel_configs[AlertChannel.TELEGRAM]["chat_id"]
            
            # Emoji based on severity
            emoji_map = {
                AlertSeverity.LOW: "🟢",
                AlertSeverity.MEDIUM: "🟡",
                AlertSeverity.HIGH: "🟠",
                AlertSeverity.CRITICAL: "🔴"
            }
            
            message = f"{emoji_map.get(alert.severity, '⚠️')} *{alert.title}*\n\n"
            message += f"{alert.message}\n\n"
            message += f"Severity: {alert.severity.value.upper()}\n"
            message += f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Telegram notification sent: {alert.id}")
                    else:
                        self.logger.error(f"Telegram notification failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error sending Telegram notification: {e}")
    
    async def _send_email_notification(self, alert: Alert):
        """Send email notification"""
        try:
            config = self.channel_configs[AlertChannel.EMAIL]
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ", ".join(config['to_emails'])
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # Email body
            body = f"""
Alert Details:

Title: {alert.title}
Severity: {alert.severity.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{alert.message}

Metadata:
{json.dumps(alert.metadata, indent=2, default=str)}

---
CryptoSatX Alert System
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['username'], config['password'])
            
            for to_email in config['to_emails']:
                if to_email.strip():
                    server.send_message(msg, to_addrs=[to_email.strip()])
            
            server.quit()
            self.logger.info(f"Email notification sent: {alert.id}")
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")
    
    async def _send_webhook_notification(self, alert: Alert):
        """Send webhook notification"""
        try:
            webhook_url = self.channel_configs[AlertChannel.WEBHOOK]["url"]
            
            payload = {
                "alert_id": alert.id,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity.value,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Webhook notification sent: {alert.id}")
                    else:
                        self.logger.error(f"Webhook notification failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error sending webhook notification: {e}")
    
    def add_alert_rule(self, rule: AlertRule):
        """Add new alert rule"""
        self.alert_rules[rule.name] = rule
        self.logger.info(f"Alert rule added: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            self.logger.info(f"Alert rule removed: {rule_name}")
    
    def enable_rule(self, rule_name: str):
        """Enable alert rule"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = True
            self.logger.info(f"Alert rule enabled: {rule_name}")
    
    def disable_rule(self, rule_name: str):
        """Disable alert rule"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = False
            self.logger.info(f"Alert rule disabled: {rule_name}")
    
    def resolve_alert(self, alert_id: str):
        """Resolve alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            # Move to history
            self.alert_history.append(alert)
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Alert resolved: {alert_id}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(
        self, 
        hours_back: int = 24,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get alert history"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        history = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
        
        if severity:
            history = [alert for alert in history if alert.severity == severity]
        
        return sorted(history, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        recent_24h = [a for a in self.alert_history if a.timestamp >= last_24h]
        recent_7d = [a for a in self.alert_history if a.timestamp >= last_7d]
        
        severity_counts_24h = {}
        severity_counts_7d = {}
        
        for alert in recent_24h:
            severity_counts_24h[alert.severity.value] = severity_counts_24h.get(alert.severity.value, 0) + 1
        
        for alert in recent_7d:
            severity_counts_7d[alert.severity.value] = severity_counts_7d.get(alert.severity.value, 0) + 1
        
        return {
            "active_alerts": len(self.active_alerts),
            "last_24_hours": {
                "total": len(recent_24h),
                "by_severity": severity_counts_24h
            },
            "last_7_days": {
                "total": len(recent_7d),
                "by_severity": severity_counts_7d
            },
            "total_rules": len(self.alert_rules),
            "enabled_rules": len([r for r in self.alert_rules.values() if r.enabled]),
            "channel_status": {
                channel.value: config["enabled"]
                for channel, config in self.channel_configs.items()
            }
        }
    
    async def test_notifications(self):
        """Test all notification channels"""
        test_alert = Alert(
            rule_name="test",
            severity=AlertSeverity.LOW,
            title="Test Alert",
            message="This is a test alert from CryptoSatX",
            metadata={"test": True}
        )
        
        channels = [
            channel for channel, config in self.channel_configs.items()
            if config["enabled"]
        ]
        
        await self._send_notifications(test_alert, channels)
        
        return {
            "message": "Test notifications sent",
            "channels": [c.value for c in channels]
        }


# Global instance
alert_service = AlertService()

# Import os for environment variables
import os
