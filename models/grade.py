from odoo import models,fields,api
from odoo.exceptions import ValidationError

class Grade(models.Model):
    _name = 'school.grade'
    _description = 'Notes étudiant'
    _rec_name = 'student_id'

    session_id = fields.Many2one('school.grade_session', ondelete='cascade')
    student_id = fields.Many2one('school.student',string="Etudiant")
    matiere_id = fields.Many2one('school.matiere',string="Matiere")
    classe_id = fields.Many2one(
        related='student_id.classe_id',
        string="Classe",
        store=True,
        readonly=True )
    specialite_id = fields.Many2one('school.specialite',string="Speciale")
    semester = fields.Selection([
        ('S1','Semester 1'),
        ('S2','Semester 2'),
    ],
        string="Semester"
    )
    notes1 = fields.Float(string="Notes TD")
    notes2 = fields.Float(string="Notes TP")
    notes3 = fields.Float(string="Notes CONTROLE")
    coef = fields.Integer(related='matiere_id.coef',string="Coef")
    allowed_matiere_ids = fields.Many2many(
        'school.matiere', compute='_compute_allowed_matiere_ids', string='Matières possibles',
    )
    moyenne_matiere = fields.Float(string="Moyenne Matiere",compute="calcul_moy_mat",store=True)
    somme_matiere = fields.Float(string="Somme Matiere", compute="calcul_moy_mat", store=True)

    @api.depends('classe_id', 'semester')
    def _compute_allowed_matiere_ids(self):
        Matiere = self.env['school.matiere']
        Program = self.env['school.program']
        for grade in self:
            if not grade.classe_id:
                grade.allowed_matiere_ids = Matiere.search([])
                continue
            domain = [('classe_id', '=', grade.classe_id.id)]
            if grade.semester:
                domain.append(('semester', '=', grade.semester))
            matieres = Program.search(domain).volume_horaire_id.matiere_id
            grade.allowed_matiere_ids = matieres or Matiere.search([])

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if self.student_id:
            self.classe_id = self.student_id.classe_id
            self.specialite_id = self.student_id.specialite_id
        else:
            self.classe_id = False
            self.specialite_id = False

    @api.depends('matiere_id','coef','notes1','notes2','notes3')
    def calcul_moy_mat(self):
        for grade in self:
            grade.moyenne_matiere = ((((grade.notes1 + grade.notes2)/2) + (grade.notes3 * 2)) / 3)
            grade.somme_matiere = grade.moyenne_matiere * grade.matiere_id.coef





    @api.constrains('notes1','notes2','notes3')
    def check_note(self):
          for record in self:
            if record.notes1 < 0 or record.notes2 < 0 or record.notes3 < 0:
                raise ValidationError ("la note ne peut pas etre negative")
            if record.notes1 > 20 or record.notes2 > 20 or record.notes3 > 20:
                raise ValidationError ("la note ne peut pas etre au dessus de 20")

    @api.constrains('matiere_id','classe_id','semester')
    def check_matiere_in_semester(self):
        for record in self:
            if record.matiere_id and record.classe_id and record.semester:
                programs = self.env['school.program'].search([
                    ('classe_id', '=', record.classe_id.id),
                    ('semester', '=', record.semester),
                ])
                if programs and record.matiere_id not in programs.volume_horaire_id.matiere_id:
                    raise ValidationError("La matière n'est pas dans le programme de cette classe.")