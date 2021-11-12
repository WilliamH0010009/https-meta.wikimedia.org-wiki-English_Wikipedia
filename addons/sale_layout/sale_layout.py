# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
import decimal_precision as dp

class sale_order_line(osv.osv):

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.layout_type == 'article':
                return super(sale_order_line, self)._amount_line(cr, uid, ids, field_name, arg, context)
        return res

    def invoice_line_create(self, cr, uid, ids, context=None):
        new_ids = []
        list_seq = []
        for line in self.browse(cr, uid, ids, context=context):
            if line.layout_type == 'article':
                new_ids.append(line.id)
                list_seq.append(line.sequence)
        invoice_line_ids = super(sale_order_line, self).invoice_line_create(cr, uid, new_ids, context)
        pool_inv_line = self.pool.get('account.invoice.line')
        seq = 0
        for obj_inv_line in pool_inv_line.browse(cr, uid, invoice_line_ids, context=context):
            pool_inv_line.write(cr, uid, [obj_inv_line.id], {'sequence': list_seq[seq]}, context=context)
            seq += 1
        return invoice_line_ids

    def onchange_sale_order_line_view(self, cr, uid, id, type, context={}, *args):
        temp = {
            'value': {
                'name': '',
                'product_id': False,
                'uos_id': False,
                'account_id': False,
                'price_unit': 0.0,
                'price_subtotal': 0.0,
                'quantity': 0,
                'discount': 0.0,
                'invoice_line_tax_id': False,
                'account_analytic_id': False,
                'product_uom_qty': 0.0,
            },
        }
        if type == 'line':
            temp['value']['name'] = '___'
        if type == 'break':
            temp['value']['name'] = '·····Page Break·····'
        if type == 'subtotal':
            temp['value']['name'] = 'Sub Total'
        return temp

    def create(self, cr, user, vals, context=None):
        if vals.has_key('layout_type'):
            if vals['layout_type'] == 'line':
                vals['name'] = '___'
            if vals['layout_type'] == 'break':
                vals['name'] = '·····Page Break·····'
            if vals['layout_type'] != 'article':
                vals['product_uom_qty']= 0
        return super(sale_order_line, self).create(cr, user, vals, context)

    def write(self, cr, user, ids, vals, context=None):
        if vals.has_key('layout_type'):
            if vals['layout_type'] == 'line':
                vals['name'] = '___'
            if vals['layout_type'] == 'break':
                vals['name'] = '·····Page Break·····'
        return super(sale_order_line, self).write(cr, user, ids, vals, context)

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default['layout_type'] = self.browse(cr, uid, id, context=context).layout_type
        return super(sale_order_line, self).copy(cr, uid, id, default, context)

    _order = "order_id, sequence asc"
    _description = "Sales Order line"
    _inherit = "sale.order.line"
    _columns = {
        'layout_type': fields.selection([
                ('article', 'Product'),
                ('title', 'Title'),
                ('text', 'Note'),
                ('subtotal', 'Sub Total'),
                ('line', 'Separator Line'),
                ('break', 'Page Break'),]
            ,'Layout Type', select=True, required=True),
        'sequence': fields.integer('Layout Sequence'),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Sale Price'), readonly=True, states={'draft': [('readonly', False)]}),
        'product_uom_qty': fields.float('Quantity (UoM)', digits=(16,2)),
        'product_uom': fields.many2one('product.uom', 'Product UoM'),
    }

    _defaults = {
        'layout_type': 'article',
    }

sale_order_line()

class one2many_mod2(fields.one2many):
    def get(self, cr, obj, ids, name, user=None, offset=0, context=None, values=None):
        if not values:
            values = {}
        res = {}
        for id in ids:
            res[id] = []
        ids2 = obj.pool.get(self._obj).search(cr, user, [(self._fields_id, 'in', ids), ('layout_type', '=', 'article')], limit=self._limit)
        for r in obj.pool.get(self._obj)._read_flat(cr, user, ids2, [self._fields_id], context=context, load='_classic_write'):
            res[r[self._fields_id]].append( r['id'] )
        return res


class sale_order(osv.osv):

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default['order_line'] = False
        return super(sale_order, self).copy(cr, uid, id, default, context)

    _inherit = "sale.order"
    _columns = {
        'abstract_line_ids': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)]}),
        'order_line': one2many_mod2('sale.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)]}),
    }

sale_order()


class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    def action_invoice_create(self, cr, uid, ids, journal_id=False, group=False, type='out_invoice', context=None):
        result = super(stock_picking, self).action_invoice_create(cr, uid, ids,
                 journal_id=journal_id, group=group, type=type, context=context)
        invoice_line_pool = self.pool.get('account.invoice.line')
        for picking in self.browse(cr, uid, result.keys(), context=context):
            if picking.sale_id:
                for sale_line in picking.sale_id.order_line:
                    invoice_lines = [line.id for line in sale_line.invoice_lines]
                    invoice_line_pool.write(cr, uid, invoice_lines, {'sequence': sale_line.sequence}, context=context) 
        return result
    
stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
