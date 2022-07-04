from odoo import api, models, fields, _
from datetime import datetime
from datetime import date


class FleetState(models.Model):
    _inherit = "fleet.vehicle.state"

    color = fields.Char()


class FleetManageField(models.Model):
    _inherit = "fleet.vehicle"

    color = fields.Char(related='state_id.color')
    button_show = fields.Boolean(default=False)
    booleans = fields.Selection([
        ('pool_id', 'Pool'),
        ('non_pool', 'Non Pool'),
        ('non_pool_other', 'Non Pool Other')], default='pool_id', string="Fleet Type")

    analytical_account_id = fields.Many2one('account.analytic.account', string="Analytical Account")
    product_id = fields.Many2one('product.product', string="Product")
    branch_id = fields.Many2one('res.branch', string="Branch", tracking=True,
                                default=lambda self: self.env.user.branch_id)
    odometer = fields.Integer(compute='_get_odometer', inverse='_set_odometer', string='Current Meter Reading',
                              help='Odometer measure of the vehicle at the moment of this log')
    time_in = fields.Datetime('Time In', compute="_get_earliest_date")
    fleet_age = fields.Integer('Fleet Age')

    account_asset_id = fields.Many2one('account.asset', string="Fixed Assets", domain="[('asset_show', '=', False)]")

    @api.onchange('account_asset_id', 'fleet_age')
    def _onchange_asset(self):
        if self.account_asset_id:
            self.account_asset_id.vehicle_id = self._origin.id
            self.account_asset_id.asset_show = True
            dayss = (self.account_asset_id.acquisition_date - date.today())
            print(dayss)
            self.fleet_age = dayss.days
            print(self.account_asset_id)
        else:
            print(self.account_asset_id)
            self.account_asset_id.vehicle_id = ''
            self.account_asset_id.asset_show = False

    @api.onchange('model_id','model_year')
    def _onchange_model(self):
        if self.model_id:
            self.model_year = self.model_id.model_year

    def _get_earliest_date(self):
        # dates = []
        # for rec in self:
        #     record = self.env['rental.progress'].search([('vehicle_no', '=', rec.id)])
        #     print(record)
        #     for r in record:
        #         if r:
        #             dates.append(r.time_in)
        #             print(dates)
        # print(dates)
        # l = dates.sort()
        # # print(l)
        self.time_in = datetime.today()

    # @api.model
    # def create(self, vals):
    #     res = super(FleetManageField, self).create(vals)
    #     # print(res)
    #     result = self.env['account.analytic.account'].create(
    #         {'name': res['license_plate'],
    #          'fleet_vehicle_id': res.id,
    #          })
    #     res.analytical_account_id = result.id
    #     result = self.env['product.product'].create(
    #         {'name': res['license_plate'],
    #          'fleet_vehicle_id': res.id,
    #          'branch_ids': res['branch_id'],
    #          'type': 'service',
    #          'invoice_policy': 'order',
    #          'purchase_method': 'purchase',
    #          })
    #     res.product_id = result.id
    #     result.product_tmpl_id.write({'fleet_vehicle_id': res.id})
    #     return res

    def _get_odometer(self):
        FleetVehicalOdometer = self.env['fleet.vehicle.odometer']
        for record in self:
            vehicle_odometer = FleetVehicalOdometer.search([('vehicle_id', '=', record.id)], limit=1,
                                                           order='value desc')
            if vehicle_odometer:
                record.odometer = vehicle_odometer.value
            else:
                record.odometer = 0

    def _set_odometer(self):
        for record in self:
            if record.odometer:
                date = fields.Date.context_today(record)
                data = {'value': record.odometer, 'date': date, 'vehicle_id': record.id}
                self.env['fleet.vehicle.odometer'].create(data)

    po_counter = fields.Integer(string='PO', compute='get_po_counter')

    def get_po_counter(self):
        for rec in self:
            count = self.env['purchase.order'].search_count([('fleet_vehicle_id', '=', rec.id)])
            rec.po_counter = count
    #
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
    #         'fleet_vehicle_id': self.id,
    #     }
    #     record = self.env['purchase.order'].create(po)
    #     self.button_show = True

    def get_purchase_orders(self):
        return {
            'name': _('Requests for Quotation'),
            'domain': [('fleet_vehicle_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'purchase.order',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }


class AnalyticalAccountVehicle(models.Model):
    _inherit = "account.analytic.account"

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")


class FleetContractField(models.Model):
    _inherit = "fleet.vehicle.log.contract"

    partner_id = fields.Many2one('res.partner', string="Customer", tracking=True,
                                 domain=[('partner_type', '=', 'is_customer')])


class FleetOdometerField(models.Model):
    _inherit = "fleet.vehicle.odometer"

    value = fields.Integer('Odometer Value', group_operator="max")
    driven = fields.Integer(string="Driven", tracking=True)


class FleetModelField(models.Model):
    _inherit = "fleet.vehicle.model"

    model_year = fields.Selection(selection=[(f'{i}', i) for i in range(1900, 3000)], string='Model Year')

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s : %s: %s' % (rec.brand_id.name, rec.name, rec.model_year)))
        return res

