odoo.define('project.task_kanban_examples', function (require) {
'use strict';

var core = require('web.core');
var kanbanExamplesRegistry = require('web.kanban_examples_registry');

var _lt = core._lt;

var greenBullet = '<span class="o_status o_status_green"></span>';
var redBullet = '<span class="o_status o_status_red"></span>';
var star = '<a style="color: gold;" class="fa fa-star"/>';
var clock = '<a class="fa fa-clock-o" />'

var description_activities = escFormat(_lt('%s Use the %s icon to organize your daily activities.'), '<br/>', clock);
var description = escFormat(_lt('Prioritize Tasks by using the %s icon.'+
            '%s Use the %s button to signalize to your colleagues that a task is ready for the next stage.'+
            '%s Use the %s to signalize a problem or a need for discussion on a task.'+
            '%s'), star, '<br/>', greenBullet, '<br/>', redBullet, description_activities);

/**
 * Helper function to escape a text before formatting it.
 *
 * First argument is the string to format and the other arguments are the values
 * to inject into the string.
 *
 * Sort of 'lazy escaping' as it is used alongside _lt.
 *
 * @returns {string} the formatted and escaped string
 */
function escFormat() {
    var args = arguments;
    return {
        toString: function () {
            args[0] = _.escape(args[0]);
            return _.str.sprintf.apply(_.str, args);
        },
    };
}

kanbanExamplesRegistry.add('project', {
    ghostColumns: [_lt('New'), _lt('Assigned'), _lt('In Progress'), _lt('Done')],
    applyExamplesText: _lt("Use This For My Project"),
    examples:[{
        name: _lt('Software Development'),
        columns: [_lt('Backlog'), _lt('Specifications'), _lt('Development'), _lt('Tests'), _lt('Delivered')],
        description: escFormat(_lt('Prioritize Tasks by using the %s icon.'+
            '%s Use the %s button to inform your colleagues that a task is ready for the next stage.'+
            '%s Use the %s to indicate a problem or a need for discussion on a task.'+
            '%s'), star, '<br/>', greenBullet, '<br/>', redBullet, description_activities),
        bullets: [greenBullet, redBullet, star],
    }, {
        name: _lt('Agile Scrum'),
        columns: [_lt('Backlog'), _lt('Sprint Backlog'), _lt('Sprint in Progress'), _lt('Sprint Complete'), _lt('Old Completed Sprint')],
        description: escFormat(_lt('Waiting for the next stage: use %s and %s bullets. %s'), greenBullet, redBullet, description_activities),
        bullets: [greenBullet, redBullet],
    }, {
        name: _lt('Digital Marketing'),
        columns: [_lt('Ideas'), _lt('Researching'), _lt('Writing'), _lt('Editing'), _lt('Done')],
        description: escFormat(_lt('Everyone can propose ideas, and the Editor marks the best ones ' +
            'as %s. Attach all documents or links to the task directly, to have all information about ' +
            'a research centralized. %s'), greenBullet, description_activities),
        bullets: [greenBullet, redBullet],
    }, {
        name: _lt('Customer Feedback'),
        columns: [_lt('New'), _lt('In development'), _lt('Done'), _lt('Refused')],
        description: escFormat(_lt('Customers propose feedbacks by email; Odoo creates tasks ' +
            'automatically, and you can communicate on the task directly. Your managers decide which ' +
            'feedback is accepted %s and which feedback is moved to the %s column. %s'), greenBullet, _lt('"Refused"'), description_activities),
        bullets: [greenBullet, redBullet],
    }, {
        name: _lt('Getting Things Done (GTD)'),
        columns: [_lt('Inbox'), _lt('Today'), _lt('This Week'), _lt('This Month'), _lt('Long Term')],
        description: escFormat(_lt('Fill your Inbox easily with the email gateway. Periodically review your ' +
            'Inbox and schedule tasks by moving them to others columns. Every day, you review the ' +
            '%s column to move important tasks %s. Every Monday, you review the %s column. %s'), _lt('"This Week"'), _lt('"Today"'), _lt('"This Month"'), description_activities),
    }, {
        name: _lt('Consulting'),
        columns: [_lt('New Projects'), _lt('Resources Allocation'), _lt('In Progress'), _lt('Done')],
        description: escFormat(_lt('Manage the lifecycle of your project using the kanban view. Add newly acquired project, assign them and use the %s and %s to define if the project is ready for the next step. %s'), greenBullet, redBullet, description_activities),
        bullets: [greenBullet, redBullet],
    }, {
        name: _lt('Research Project'),
        columns: [_lt('Brainstorm'), _lt('Research'), _lt('Draft'), _lt('Final Document')],
        description: escFormat(_lt('Handle your idea gathering within Tasks of your new Project and discuss them in the chatter of the tasks. Use the %s and %s to signalize what is the current status of your Idea. %s'), greenBullet, redBullet, description_activities),
        bullets: [greenBullet, redBullet],
    }, {
        name: _lt('Website Redesign'),
        columns: [_lt('Page Ideas'), _lt('Copywriting'), _lt('Design'), _lt('Live')],
        description: escFormat(_lt('Handle your idea gathering within Tasks of your new Project and discuss them in the chatter of the tasks. Use the %s and %s to signalize what is the current status of your Idea. %s'), greenBullet, redBullet, description_activities),
    }, {
        name: _lt('T-shirt Printing'),
        columns: [_lt('New Orders'), _lt('Logo Design'), _lt('To Print'), _lt('Done')],
        description: escFormat(_lt('Communicate with customers on the task using the email gateway. ' +
            'Attach logo designs to the task, so that information flow from designers to the workers ' +
            'who print the t-shirt. Organize priorities amongst orders %s using the icon. %s'), star, description_activities),
        bullets: [star],
    }, {
        name: _lt('Design'),
        columns: [_lt('New Request'), _lt('Design'), _lt('Client Review'), _lt('Handoff')],
        description: description,
        bullets: [greenBullet, redBullet, star, clock],
    }, {
        name: _lt('Publishing'),
        columns: [_lt('Ideas'), _lt('Writing'), _lt('Editing'), _lt('Published')],
        description: description,
        bullets: [greenBullet, redBullet, star, clock],
    }, {
        name: _lt('Manufacturing'),
        columns: [_lt('New Orders'), _lt('Material Sourcing'), _lt('Manufacturing'), _lt('Assembling'), _lt('Delivered')],
        description: description,
        bullets: [greenBullet, redBullet, star, clock],
    }, {
        name: _lt('Podcast and Video Production'),
        columns: [_lt('Research'), _lt('Script'), _lt('Recording'), _lt('Mixing'), _lt('Publishing')],
        description: description,
        bullets: [greenBullet, redBullet, star, clock],
    }],
});

});
