Slack Attendance Integration
============================

Track employee attendance directly from Slack — no separate app, no browser required.
Employees use simple slash commands to check in, check out, and manage breaks,
all synced automatically with Odoo's HR Attendance module.

.. contents::
   :local:
   :depth: 1


Features
--------

Slack Slash Commands
~~~~~~~~~~~~~~~~~~~~

+------------------+----------------------------------------------+
| Command          | Action                                       |
+==================+==============================================+
| ``/login``       | Check in — records attendance in Odoo        |
+------------------+----------------------------------------------+
| ``/logout``      | Check out — closes attendance record         |
+------------------+----------------------------------------------+
| ``/break``       | Start a break                                |
+------------------+----------------------------------------------+
| ``/resume``      | End a break and return to work               |
+------------------+----------------------------------------------+

Smart Login Grace Time
~~~~~~~~~~~~~~~~~~~~~~

Configure a grace window (e.g. 5 minutes) so that an employee who types
``/login`` at 10:00 AM is recorded as checking in at 9:55 AM.
This removes the pressure of racing the clock.

Break Threshold
~~~~~~~~~~~~~~~

Short interruptions (bathroom, coffee) that fall below the configured
minimum break duration are saved but **not** deducted from working hours.
Only meaningful breaks count.

Net Working Hours
~~~~~~~~~~~~~~~~~

Every attendance record shows::

    Net Working Hours = Total Hours − Counted Break Time

AI-Powered Daily Summary *(optional)*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When enabled with an Anthropic API key, each employee receives a
personalised Slack DM at end-of-day. The message references their
actual hours, streak, and target — not a generic template.

Daily Attendance Alert
~~~~~~~~~~~~~~~~~~~~~~

Employees who forgot to ``/logout`` receive an automatic reminder DM.


Installation
------------

Requirements
~~~~~~~~~~~~

* Odoo 17.0 or 18.0
* Python packages: ``certifi``, ``pytz`` (both included in standard Odoo)
* A Slack workspace with a configured App (slash commands + bot token)

Steps
~~~~~

1. Copy the ``slack_attendance_integration`` folder into your Odoo addons path.
2. Restart the Odoo server.
3. In Odoo, go to **Apps** → search for *Slack Attendance* → click **Install**.
4. Navigate to **Attendances → Configuration → Slack Settings**.
5. Fill in:

   * **Slack Signing Secret** — from your Slack app's *Basic Information* page
   * **Bot Token** — starts with ``xoxb-``
   * **Incoming Webhook URL** — from *Incoming Webhooks* in your Slack app
6. Set the **Webhook URL** in your Slack app's slash commands to::

       https://<your-odoo-domain>/slack/attendance

7. For each employee, open their HR record and add their **Slack User ID**
   (found in Slack → profile → *Copy member ID*).


Slack App Configuration
-----------------------

Create a new Slack app at https://api.slack.com/apps and configure:

Slash Commands
~~~~~~~~~~~~~~

Create four commands, all pointing to the same URL:

+------------------+--------------------------------------+
| Command          | Usage hint                           |
+==================+======================================+
| ``/login``       | Check in to office                   |
+------------------+--------------------------------------+
| ``/logout``      | Check out from office                |
+------------------+--------------------------------------+
| ``/break``       | Start a break                        |
+------------------+--------------------------------------+
| ``/resume``      | Resume work after a break            |
+------------------+--------------------------------------+

Required Bot Token Scopes
~~~~~~~~~~~~~~~~~~~~~~~~~

* ``chat:write`` — to send DMs to employees
* ``commands`` — to respond to slash commands


AI Summary Setup *(optional)*
------------------------------

1. Get an API key from https://console.anthropic.com
2. In **Slack Settings**, enable **AI Summaries** and paste the key.
3. The daily cron job will now send personalised messages instead of
   the default template.

.. note::
   The API key is visible only to Odoo System Administrators.
   Summaries are generated once per day and cached on the attendance record.


Configuration Reference
-----------------------

+-------------------------------+-------------------------------------------------------+
| Field                         | Description                                           |
+===============================+=======================================================+
| Login Grace Minutes           | Subtract N minutes from actual login time             |
+-------------------------------+-------------------------------------------------------+
| Minimum Break Minutes         | Breaks shorter than this are not counted              |
+-------------------------------+-------------------------------------------------------+
| Minimum Working Hours         | Target hours for daily summary comparison             |
+-------------------------------+-------------------------------------------------------+
| Send Daily Summary            | Enable end-of-day Slack DM                            |
+-------------------------------+-------------------------------------------------------+
| Summary Time                  | Hour (24h format) when the cron fires                 |
+-------------------------------+-------------------------------------------------------+
| Enable AI Summaries           | Use Claude AI for personalised messages               |
+-------------------------------+-------------------------------------------------------+
| Anthropic API Key             | Your sk-ant- key (admin-only)                         |
+-------------------------------+-------------------------------------------------------+


Security
--------

* Every request from Slack is verified using **HMAC-SHA256** with your
  Signing Secret before any database action is performed.
* Replay attacks are blocked — requests older than 5 minutes are rejected.
* SSL connections use the **certifi** CA bundle (no certificate verification bypass).
* The Anthropic API key is stored in an admin-only field group.


Changelog
---------

19.0.1.0.0 (2026)
~~~~~~~~~~~~~~~~~~

* Initial release
* Login / logout / break / resume slash commands
* Grace minutes and minimum break threshold
* Net working hours computation
* Daily Slack summary via cron
* AI-powered personalised summaries (Claude)
* HMAC-SHA256 Slack signature verification
* certifi-based SSL — no CERT_NONE
* Employee timezone support (no hardcoded IST)


Support
-------

* GitHub: https://github.com/anmol6213/slack_attendance_integration
* Issues: https://github.com/anmol6213/slack_attendance_integration/issues
