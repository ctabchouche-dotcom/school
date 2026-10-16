from odoo import models, fields, api

class SchoolGradeSession(models.Model):
    _name = 'school.grade_session'
    _description = 'Session de saisie des notes'

    classe_id = fields.Many2one('school.classes', string="Classe", required=True)
    matiere_id = fields.Many2one('school.matiere', string="Matière", required=True)
    semester = fields.Selection([('S1', 'S1'), ('S2', 'S2')], string="Semestre", required=True)

    # Ce champ va générer automatiquement la liste des étudiants
    line_ids = fields.One2many('school.grade', 'session_id', string="Notes des étudiants")

    def action_load_students(self):
        self.line_ids.unlink()
        students = self.env['school.student'].search([('classe_id', '=', self.classe_id.id)])
        lines = []
        for student in students:
            lines.append((0, 0, {
                'student_id': student.id,
                'matiere_id': self.matiere_id.id,
                'semester': self.semester,
            }))
        self.line_ids = lines

    moyenne_classe = fields.Float(
        string="Moyenne de la Classe",
        compute="_compute_stats",
        store=True
    )
    taux_reussite = fields.Float(
        string="Taux de Réussite (%)",
        compute="_compute_stats",
        store=True
    )


    @api.depends('line_ids.moyenne_matiere')
    def _compute_stats(self):
        for session in self:
            if session.line_ids:
                total_moyennes = sum(line.moyenne_matiere for line in session.line_ids)
                nb_etudiants = len(session.line_ids)
                session.moyenne_classe = total_moyennes / nb_etudiants
                reussis = len(session.line_ids.filtered(lambda l: l.moyenne_matiere >= 10))
                session.taux_reussite = (reussis / nb_etudiants) * 100
            else:
                session.moyenne_classe = 0.0
                session.taux_reussite = 0.0