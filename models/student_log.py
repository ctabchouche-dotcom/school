from odoo import models, fields
class StudentLog(models.Model):
    _name = 'school.student.log'
    _description = 'Historique des états étudiant'
    _order = 'date desc'

    student_id = fields.Many2one(
        'school.student',
        string="Étudiant",
        required=True,
        ondelete='cascade'
    )

    old_state = fields.Char(string="Ancien état")
    new_state = fields.Char(string="Nouvel état")

    user_id = fields.Many2one(
        'res.users',
        string="Utilisateur",
        default=lambda self: self.env.user
    )

    date = fields.Datetime(
        string="Date",
        default=fields.Datetime.now
    )
