# -*- coding: utf-8 -*-
{
    'name': 'Slack Attendance Integration',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Track employee attendance via Slack slash commands with AI summaries',
    'description': """
Slack Attendance Integration
========================================
* Check-in / Check-out via /login and /logout
* Break tracking via /break and /resume
* Login grace minutes — no clock-racing
* Minimum break threshold — short breaks not counted
* Net working hours = total minus counted breaks
* AI daily summaries — Gemini (free) or Claude
* HMAC-SHA256 Slack signature verification
* SSL via certifi — no CERT_NONE
* Per-employee timezone support
* Daily missed-logout alerts
    """,
    'author': 'Anmol Patil',
    'website': 'https://github.com/anmol6213',
    'support': 'anmol621314@gmail.com',
    'license': 'LGPL-3',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
        'views/slack_config_views.xml',
        'views/attendance_break_views.xml',
        'data/ir_cron_data.xml',
    ],
    'images': ['static/description/banner.gif'],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 0,
    'currency': 'EUR',
    'external_dependencies': {'python': ['certifi']},
}
