odoo.define("hr_timesheet.timesheet_uom_tests_env", function (require) {
"use strict";

const session = require('web.session');
const AbstractWebClient = require('web.AbstractWebClient');
const { createView } = require("web.test_utils");
const ListView = require('web.ListView');

/**
 * Sets the timesheet related widgets testing environment up.
 */
const SetupTimesheetUOMWidgetsTestEnvironment = function () {
    this.allowedCompanies = {
        1: {
            id: 1,
            name: 'Company 1',
            timesheet_uom_id: 1,
            timesheet_uom_factor: 1,
        },
        2: {
            id: 2,
            name: 'Company 2',
            timesheet_uom_id: 2,
            timesheet_uom_factor: 0.125,
        },
        3: {
            id: 3,
            name: 'Company 3',
            timesheet_uom_id: 2,
            timesheet_uom_factor: 0.125,
        },
    };
    this.uomIds = {
        1: {
            id: 1,
            name: 'hour',
            rounding: 0.01,
            timesheet_widget: 'float_time',
        },
        2: {
            id: 2,
            name: 'day',
            rounding: 0.01,
            timesheet_widget: 'float_toggle',
        },
    };
    this.singleCompanyHourUOMUser = {
        allowed_company_ids: [this.allowedCompanies[1].id],
    };
    this.singleCompanyDayUOMUser = {
        allowed_company_ids: [this.allowedCompanies[2].id],
    };
    this.multiCompanyHourUOMUser = {
        allowed_company_ids: [
            this.allowedCompanies[1].id,
            this.allowedCompanies[3].id,
        ],
    };
    this.multiCompanyDayUOMUser = {
        allowed_company_ids: [
            this.allowedCompanies[3].id,
            this.allowedCompanies[1].id,
        ],
    };
    this.session = {
        uid: 0, // In order to avoid bbqState and cookies to be taken into account in AbstractWebClient.
        user_companies: {
            current_company: 1,
            allowed_companies: this.allowedCompanies,
        },
        user_context: this.singleCompanyHourUOMUser,
        uom_ids: this.uomIds,
    };
    this.data = {
        'account.analytic.line': {
            fields: {
                project_id: {
                    string: "Project",
                    type: "many2one",
                    relation: "project.project",
                },
                task_id: {
                    string:"Task",
                    type: "many2one",
                    relation: "project.task",
                },
                date: {
                    string: "Date",
                    type: "date",
                },
                unit_amount: {
                    string: "Unit Amount",
                    type: "float",
                },
            },
            records: [
                {
                    id: 1,
                    project_id: 1,
                    task_id: 1,
                    date: "2021-01-12",
                    unit_amount: 8,
                },
            ],
        },
        'project.project': {
            fields: {
                name: {
                    string: "Project Name",
                    type: "char",
                },
            },
            records: [
                {
                    id: 1,
                    display_name: "P1",
                },
            ],
        },
        'project.task': {
            fields: {
                name: {
                    string: "Task Name",
                    type: "char",
                },
                project_id: {
                    string: "Project",
                    type: "many2one",
                    relation: "project.project",
                },
            },
            records: [
                {
                    id: 1,
                    display_name: "T1",
                    project_id: 1,
                },
            ],
        },
    };
    this.triggerAbstractWebClientInit = function (sessionToApply, doNotUseEnvSession = false) {
        /*
        Adds the timesheet_uom to the fieldRegistry by setting the session and
        instantiating AbstractWebClient as the process of adding the right widget
        is included in the init function of AbstractWebClient.
        */
        session.user_companies = Object.assign(
            { },
            !doNotUseEnvSession && this.session.user_companies || { },
            sessionToApply && sessionToApply.user_companies);
        session.user_context = Object.assign(
            { },
            !doNotUseEnvSession && this.session.user_context || { },
            sessionToApply && sessionToApply.user_context);
        session.uom_ids = Object.assign(
            { },
            !doNotUseEnvSession && this.session.uom_ids || { },
            sessionToApply && sessionToApply.uom_ids);
        if (!doNotUseEnvSession && 'uid' in this.session) {
            session.uid = this.session.uid;
        }
        if (sessionToApply && 'uid' in sessionToApply) {
            session.uid = sessionToApply.uid;
        }
        if (!this.abstractWebClient) {
            this.abstractWebClient = new AbstractWebClient();
        } else {
            this.abstractWebClient.init();
        }
    };
    this.createView = async function(options) {
        const sessionToApply = options && options.session || { };
        this.triggerAbstractWebClientInit(sessionToApply);
        return await createView(Object.assign(
            {
                View: ListView,
                data: this.data,
                model: 'account.analytic.line',
                arch: `
                    <tree>
                        <field name="unit_amount" widget="timesheet_uom"/>
                    </tree>`,
            },
            options || { },
        ));
    };
};

return SetupTimesheetUOMWidgetsTestEnvironment;

});
