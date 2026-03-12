# -*- coding: utf-8 -*-
{
    'name': 'Slack Attendance Integration',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Track employee attendance via Slack slash commands',
    'description': """
        Slack Attendance Integration
        ========================================
        * Track check-in/check-out via Slack /login and /logout commands
        * Manage breaks with /break and /resume commands
        * Automatic calculation of working hours and break duration
        * Secure webhook handling with Slack signature verification
        * Daily attendance summaries
    """,
    'author': 'Anmol Patil',
    'website': 'https://github.com/anmol6213',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'hr_attendance',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
        'views/slack_config_views.xml',
        'views/attendance_break_views.xml',
        # 'data/ir_cron_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}