from odoo import api, models, fields, _


class PurchaseCars(models.Model):
    _name = "po.cars"
    _description = "Po Cars"
    _rec_name = 'number'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    model_id = fields.Many2one('fleet.vehicle.model', string="Model", tracking=True)
    branch_id = fields.Many2one('res.branch', string="Branch", tracking=True, required=True)
    number = fields.Char(string='Number', required=True, copy=False, readonly=True, default='New')
    analytical_account_id = fields.Many2one('account.analytic.account', string="Analytical Account")
    product_id = fields.Many2one('product.product', string="Product")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", tracking=True, copy=False)
    button_show = fields.Boolean(default=False)
    button_po_show = fields.Boolean(default=False)
    stage_id = fields.Selection([
        ('purchase', 'PURCHASED'),
        ('not_purchase', 'NOT PURCHASED')], default='not_purchase', string="Stage ID")


    @api.model
    def create(self, values):
        values['number'] = self.env['ir.sequence'].next_by_code('po.cars') or _('New')
        res = self.env['fleet.vehicle'].create(
            {'model_id': values['model_id'],
             'branch_id': values['branch_id'],
             'active': False,
             })
        print(res)
        values['vehicle_id'] = res.id
        v = self.env['fleet.vehicle.model'].browse([values['model_id']])
        resul = self.env['account.analytic.account'].create(
            {'name': str(v.name)+ str(v.brand_id.name) + str(values['number']),
             'fleet_vehicle_id': res.id,
             })
        values['analytical_account_id'] = resul.id
        resu = self.env['product.product'].create(
            {'name': str(v.name)+ str(v.brand_id.name) + str(values['number']),
             'fleet_vehicle_id': res.id,
             'branch_ids': res['branch_id'],
             'type': 'service',
             'invoice_policy': 'order',
             'purchase_method': 'purchase',
             })
        values['product_id'] = resu.id
        resu.product_tmpl_id.write({'fleet_vehicle_id': res.id})
        res.update({
            'analytical_account_id': resul.id,
            'product_id': resu.id
        })
        return super(PurchaseCars, self).create(values)

    def action_register(self):
        return {
            'name': _('Register'),
            'res_model': 'register.wizard',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
                'default_analytical_account_id': self.analytical_account_id.id,
                'default_product_id': self.product_id.id,
                'default_vehicle_id': self.vehicle_id.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    # def action_create_po(self):
    #     active_user = self.env.user
    #     r = self.env['account.analytic.tag'].search([('branch_id', '=', self.branch_id.id)])
    #     line_vals = []
    #     line_vals.append((0, 0, {
    #         'product_id': self.product_id.id,
    #         'name': self.product_id.name,
    #         'account_analytic_id': self.analytical_account_id.id,
    #         'product_qty': 1.0,
    #         'price_unit': 0,
    #         'analytic_tag_ids': r,
    #     }))
    #     po = {
    #         'order_line': line_vals,
    #         'partner_id': active_user.id,
    #         'picking_type_id': '1',
    #         'branch_id': self.branch_id.id,
    #         'fleet_vehicle_id': self.vehicle_id.id,
    #     }
    #     record = self.env['purchase.order'].create(po)
    #     self.button_po_show = True
