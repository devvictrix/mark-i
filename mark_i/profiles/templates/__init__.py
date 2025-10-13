"""
Profile Templates

Pre-built automation profile templates for common tasks.
Provides ready-to-use profiles that can be customized for specific needs.
"""

from .email_templates import (
    EmailSendingTemplate,
    EmailReadingTemplate,
    EmailManagementTemplate,
    create_email_templates
)

from .web_templates import (
    WebSearchTemplate,
    FormFillingTemplate,
    DataExtractionTemplate,
    create_web_templates
)

from .system_templates import (
    FileManagementTemplate,
    ApplicationLaunchTemplate,
    SystemMonitoringTemplate,
    create_system_templates
)

from .template_manager import TemplateManager

__all__ = [
    'EmailSendingTemplate',
    'EmailReadingTemplate', 
    'EmailManagementTemplate',
    'WebSearchTemplate',
    'FormFillingTemplate',
    'DataExtractionTemplate',
    'FileManagementTemplate',
    'ApplicationLaunchTemplate',
    'SystemMonitoringTemplate',
    'TemplateManager',
    'create_email_templates',
    'create_web_templates',
    'create_system_templates'
]