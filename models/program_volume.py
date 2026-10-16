from odoo import models,fields

class Program_Volume(models.Model):
    _name = "school.program_volume"
    _description = "School Program Volume"

    program_id = fields.Many2one("school.program", string="Programme", ondelete="cascade")
    matiere_id = fields.Many2one("school.matiere", string="Matière", required=True)
    cours = fields.Integer(related="matiere_id.vol_course",string="Volume horaire cours")
    td = fields.Integer(related="matiere_id.vol_td",string="Volume horaire td ")
    tp = fields.Integer(related="matiere_id.vol_tp",string="Volume horaire tp ")


