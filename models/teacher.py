from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Teacher(models.Model):
    _name = 'school.teacher'
    _description = 'Professeur'

    name = fields.Char(string="Nom")
    user_id = fields.Many2one('res.users', string="Compte Utilisateur Odoo")
    email = fields.Char(string="Email")
    phone = fields.Char(string="telephone")
    specialite_id = fields.Many2one("school.specialite",string="Specialite")
    matiere_id = fields.One2many("school.matiere",'professeur_id',string="Matiere")
    affectation_id = fields.One2many('school.affectation','teacher_id', string="Affectation")
    state_prof = fields.Selection([
        ('active','actif'),
        ('inactive','inactif'),
    ] ,
        string="Etat professeur",
        default='inactive',
    )
@api.constrains('matiere_id')
def _check_nombrre_matiere_id(self):
        for record in self:
            if len(record.matiere_id) > 3:
                raise ValidationError(
                    "Vous pouvez pas ajouter d'autres matieres"
                )


