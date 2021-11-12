# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.http import route, request
from odoo.addons.mass_mailing.controllers.main import MassMailController


class MassMailController(MassMailController):

    @route('/website_mass_mailing/is_subscriber', type='json', website=True, auth="public")
    def is_subscriber(self, list_id, **post):
        email = None
        if not request.env.user._is_public():
            email = request.env.user.email
        elif request.session.get('mass_mailing_email'):
            email = request.session['mass_mailing_email']

        is_subscriber = False
        if email:
            contacts_count = request.env['mail.mass_mailing.list_contact_rel'].sudo().search_count([('list_id', 'in', [int(list_id)]), ('contact_id.email', '=', email), ('opt_out', '=', False)])
            is_subscriber = contacts_count > 0

        return {'is_subscriber': is_subscriber, 'email': email}

    @route('/website_mass_mailing/subscribe', type='json', website=True, auth="public")
    def subscribe(self, list_id, email, **post):
        List_contact_rel = request.env['mail.mass_mailing.list_contact_rel'].sudo()
        Contacts = request.env['mail.mass_mailing.contact'].sudo()
        name, email = Contacts.get_name_email(email)

        list_contact_rel = List_contact_rel.search([('list_id', '=', int(list_id)), ('contact_id.email', '=', email)], limit=1)
        if not list_contact_rel:
            # inline add_to_list as we've already called half of it
            contact_id = Contacts.search([('email', '=', email)], limit=1)
            if not contact_id:
                contact_id = Contacts.create({'name': name, 'email': email})
            List_contact_rel.create({'contact_id': contact_id.id, 'list_id': int(list_id)})
        elif list_contact_rel.opt_out:
            list_contact_rel.opt_out = False
        # add email to session
        request.session['mass_mailing_email'] = email
        return True

    @route(['/website_mass_mailing/get_content'], type='json', website=True, auth="public")
    def get_mass_mailing_content(self, newsletter_id, **post):
        data = self.is_subscriber(newsletter_id, **post)
        mass_mailing_list = request.env['mail.mass_mailing.list'].sudo().browse(int(newsletter_id))
        data['content'] = mass_mailing_list.popup_content,
        data['redirect_url'] = mass_mailing_list.popup_redirect_url
        return data
