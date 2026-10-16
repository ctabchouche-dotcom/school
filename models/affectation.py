from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SchoolAffectation(models.Model):
    _name = 'school.affectation'
    _description = 'Affectation Professeur / Matière / Classe'

    teacher_id = fields.Many2one('school.teacher', required=True)
    matiere_id = fields.Many2one('school.matiere', required=True)
    classe_id = fields.Many2one('school.classes', required=True)
    semester = fields.Selection([
        ('S1', 'semester 1'),
        ('S2', 'semester 2'),
    ],
        string="Semester"
    )

    _sql_constraints = [
        (
            'unique_affectation',
            'unique(teacher_id, class_id, matiere_id, semester)',
            'Cette affectation existe déjà.'
        )
    ]
