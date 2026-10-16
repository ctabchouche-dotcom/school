from odoo import models,fields

class Matiere(models.Model):
    _name = 'school.matiere'
    _description = 'Matiere'

    name = fields.Char(string="Nom")
    code = fields.Char(string="Code")
    coef = fields.Integer(string="Coef")
    semester = fields.Selection([
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
    ],
    string="Semester")
    specialite_id = fields.Many2many('school.specialite',string="Specialité")
    professeur_id = fields.Many2one("school.teacher",string="Professeur")
    classe_id = fields.Many2many("school.classes",string="Classe")
    programme_id = fields.Many2one("school.program",string="Programme")
    affectation_id = fields.One2many("school.affectation",'matiere_id',string="Affectation")
    vol_course = fields.Integer(string="volume cours")
    vol_td = fields.Integer(string="volume td ")
    vol_tp = fields.Integer(string="volume tp")
