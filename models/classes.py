from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class Classes(models.Model):
    _name = 'school.classes'
    _description = 'Classes'

    name = fields.Char(string="Nom de la classe")
    niveau = fields.Selection([
        ('L1','Licence 1'),
        ('L2','Licence 2'),
        ('L3','Licence 3'),
        ('M1','Master 1'),
        ('M2','Master 2'),
        ('Phd','Doctorat'),
    ],
        string="Niveau"
    )
    student_id = fields.One2many("school.student",'classe_id',string="Etudiants")
    matiere_id = fields.Many2many("school.matiere",string="Matiere")
    capacity = fields.Integer(string="Capacité")
    specialite_id = fields.Many2many('school.specialite',string="Specialite")
    affectation_id = fields.One2many('school.affectation','classe_id',string="Affectation")
    program_id = fields.Many2one('school.program',string="Program")
    state_classe = fields.Selection(
        [
           ('draft','brouillon'),
           ('open','ouvert'),
           ('full','complete'),
           ('close', 'cloturé')
        ],
           string="statut",
           default='draft'
        )

    def write(self, vals):
     if 'state_classe' in vals:
            allowed_transitions = {
                'draft': ['open'],
                'open': ['full'],
                'full': ['close'],
                'close': [],
            }

            for record in self:
                current_state = record.state_classe
                new_state = vals['state_classe']
                if new_state not in allowed_transitions[current_state]:
                    raise ValidationError(
                        f"Transition interdite : {current_state} → {new_state}"
                    )


     return super().write(vals)

    def action_open(self):
      self.write({'state_classe': 'open'})

    def action_full(self):
     self.write({'state_classe': 'full'})

    def action_close(self):
     self.write({'state_classe': 'close'})


    @api.constrains('student_id')
    def _check_number_student(self):
         for classe in self:
          if len(classe.student_id) > classe.capacity :
             raise ValidationError("La classe est complete")


