from odoo import models, fields

class Specialite(models.Model):
    _name = 'school.specialite'
    _description = 'Specialite'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string="Nom de la specialite", required=True)
    students_id = fields.One2many("school.student", 'specialite_id', string="Etudiants")
    matiere_id = fields.Many2many("school.matiere",string="Matiere")
    active = fields.Boolean(default=True)
    student_count = fields.Integer(string="Nombre d'étudiants", compute='_compute_student_count')

    def _compute_student_count(self):
        for rec in self:
            rec.student_count = self.env['school.student'].search_count([
                ('specialite_id', '=', rec.id)
            ])

    def action_view_students(self):
        return {
            'name': 'Étudiants en ' + self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'school.student',
            'view_mode': 'list,form',
            'domain': [('specialite_id', '=', self.id)],
            'context': {'default_specialite_id': self.id},
        }