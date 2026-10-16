from odoo import models, fields, api
import random


class Absence(models.Model):
    _name = 'school.absence'
    _description = 'Gestion des Absences'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    student_id = fields.Many2one('school.student', string="Étudiant", required=True)
    matiere_id = fields.Many2one('school.matiere', string="Matière", required=True)
    date_absence = fields.Date(string="Date", default=fields.Date.today)
    is_justified = fields.Boolean(string="Justifiée ?", default=False)
    justification_file = fields.Binary(string="Justificatif (PDF)")
    justification_filename = fields.Char()

    state = fields.Selection([
        ('draft', 'En attente'),
        ('valid', 'Acceptée'),
        ('pending','En attente de validation'),
        ('refused','Refusé')
    ], string="État", default='draft')

    def action_draft(self):
        for record in self:
            record.state = 'draft'

    def action_validate(self):
        for rec in self:
            rec.state = 'valid'

    def action_set_pending(self):
        for record in self:
            record.state = 'pending'

    def action_refuse(self):
        for rec in self:
            rec.state = 'refused'

    @api.model
    def create(self, vals):
        res = super(Absence, self).create(vals)
        student = res.student_id
        matiere = res.matiere_id
        count = self.search_count([
            ('student_id', '=', student.id),
            ('matiere_id', '=', matiere.id),
            ('is_justified', '=', False)
        ])

        if count > 5:
            student.write({
                'active': False,
                'state': 'archived'
            })
            subject = f"ALERTE : Exclusion définitive - {student.name}"
            message = f"Vous avez atteint {count} absences en {matiere.name}. Vous êtes désormais EXCLU."
            color = "#e74c3c"


        else:
            subject = f"Avertissement d'absence n°{count} - {student.name}"
            restant = 5 - count
            message = f"Vous avez été marqué absent en {matiere.name} le {res.date_absence}. Attention, il ne vous reste que {restant} absence(s) autorisée(s) avant l'exclusion."
            color = "#f39c12"

        if student.email:
            template_body = f"""
                <div style="font-family: sans-serif; border: 2px solid {color}; padding: 20px; border-radius: 10px;">
                    <h2 style="color: {color};">{subject}</h2>
                    <p>Bonjour <strong>{student.name}</strong>,</p>
                    <p>{message}</p>
                    <p>Matière : <strong>{matiere.name}</strong><br/>
                       Date : <strong>{res.date_absence}</strong></p>
                    <hr/>
                    <p style="font-size: 12px; color: #7f8c8d;">Ceci est un message automatique du système de gestion scolaire.</p>
                </div>
                """

            self.env['mail.mail'].create({
                'subject': subject,
                'body_html': template_body,
                'email_to': student.email,
            }).send()

        return res