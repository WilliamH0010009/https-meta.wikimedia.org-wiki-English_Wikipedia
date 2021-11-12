# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Expenses',
    'version': '2.0',
    'category': 'Human Resources/Expenses',
    'sequence': 70,
    'summary': 'Submit, validate and reinvoice employee expenses',
    'description': """
Manage expenses by Employees
============================

This application allows you to manage your employees' daily expenses. It gives you access to your employees’ fee notes and give you the right to complete and validate or refuse the notes. After validation it creates an invoice for the employee.
Employee can encode their own expenses and the validation flow puts it automatically in the accounting after validation by managers.


The whole flow is implemented as:
---------------------------------
* Draft expense
* Submitted by the employee to his manager
* Approved by his manager
* Validation by the accountant and accounting entries creation

This module also uses analytic accounting and is compatible with the invoice on timesheet module so that you are able to automatically re-invoice your customers' expenses if your work by project.
    """,
    'website': 'https://www.odoo.com/page/expenses',
    'depends': ['hr_contract', 'account', 'web_tour'],
    'data': [
        'security/hr_expense_security.xml',
        'security/ir.model.access.csv',
        'data/digest_data.xml',
        'data/mail_data.xml',
        'data/mail_templates.xml',
        'data/hr_expense_sequence.xml',
        'data/hr_expense_data.xml',
        'wizard/hr_expense_refuse_reason_views.xml',
        'wizard/hr_expense_approve_duplicate_views.xml',
        'views/hr_expense_views.xml',
        'views/mail_activity_views.xml',
        'security/ir_rule.xml',
        'report/hr_expense_report.xml',
        'views/hr_department_views.xml',
        'views/res_config_settings_views.xml',
        'views/account_journal_dashboard.xml',
    ],
    'demo': ['data/hr_expense_demo.xml'],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'hr_expense/static/src/js/expense_views.js',
            'hr_expense/static/src/js/expense_form_view.js',
            'hr_expense/static/src/js/expense_qr_code_action.js',
            'hr_expense/static/src/js/upload_mixin.js',
            'hr_expense/static/src/scss/hr_expense.scss',
        ],
        'web.assets_tests': [
            'hr_expense/static/src/js/tours/hr_expense.js',
            'hr_expense/static/tests/tours/expense_upload_tours.js',
        ],
        'web.assets_qweb': [
            'hr_expense/static/src/xml/**/*',
        ],
    },
    'license': 'LGPL-3',
}
