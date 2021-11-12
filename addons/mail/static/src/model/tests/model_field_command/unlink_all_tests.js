/** @odoo-module **/

import { create, unlinkAll } from 'mail/static/src/model/model_field_command.js';
import {
    afterEach,
    beforeEach,
    start,
} from 'mail/static/src/utils/test_utils.js';

QUnit.module('mail', {}, function () {
QUnit.module('model', {}, function () {
QUnit.module('model_field_command', {}, function () {
QUnit.module('unlink_all_tests.js', {
    beforeEach() {
        beforeEach(this);
        this.start = async params => {
            const { env, widget } = await start(Object.assign({}, params, {
                data: this.data,
            }));
            this.env = env;
            this.widget = widget;
        };
    },
    afterEach() {
        afterEach(this);
    },
});

QUnit.test('unlinkAll: should set x2one field undefined', async function (assert) {
    assert.expect(2);
    await this.start();

    const contact = this.env.models['test.contact'].create({
        id: 10,
        address: create({ id: 20 }),
    });
    const address = this.env.models['test.address'].findFromIdentifyingData({ id: 20 });
    contact.update({ address: unlinkAll() });
    assert.strictEqual(
        contact.address,
        undefined,
        'clear: should set x2one field undefined'
    );
    assert.strictEqual(
        address.contact,
        undefined,
        'the inverse relation should be cleared as well'
    );
});

QUnit.test('unlinkAll: should set x2many field an empty array', async function (assert) {
    assert.expect(2);
    await this.start();

    const contact = this.env.models['test.contact'].create({
        id: 10,
        tasks: create({
            id: 20,
        }),
    });
    const task = this.env.models['test.task'].findFromIdentifyingData({ id:20 });
    contact.update({ tasks: unlinkAll() });
    assert.strictEqual(
        contact.tasks.length,
        0,
        'clear: should set x2many field empty array'
    );
    assert.strictEqual(
        task.responsible,
        undefined,
        'the inverse relation should be cleared as well'
    );
});

});
});
});
