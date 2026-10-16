from odoo import models, fields, api


class Ticket(models.Model):
    _name = 'school.ticket'
    _description = 'Ticket Support Étudiant'
    _inherit = ['mail.thread']

    name = fields.Char(string="Sujet", required=True)
    student_id = fields.Many2one('school.student', string="Étudiant", required=True)
    category = fields.Selection([
        ('admin', 'Administratif'),
        ('tech', 'Technique'),
        ('pedago', 'Pédagogique')
    ], string="Catégorie", required=True)

    matiere_id = fields.Many2one('school.matiere', string="Matière concernée")
    description = fields.Html(string="Description")
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('in_progress', 'En cours'),
        ('solved', 'Résolu')
    ], default='new')

    @api.model
    def create(self, vals):
        ticket = super(Ticket, self).create(vals)
        recipient_email = False
        destinataire_nom = ""
        if ticket.category in ['admin', 'tech']:
            group = self.env.ref('school.group_school_manager', raise_if_not_found=False)
            if group:
                admin_user = group.all_user_ids.filtered(lambda user: user.email)[:1]
                if admin_user:
                    recipient_email = admin_user.email
                    destinataire_nom = admin_user.name

        elif ticket.category == 'pedago' and ticket.matiere_id:
            prof = getattr(ticket.matiere_id, 'professeur_id', False)
            if prof and prof.email:
                recipient_email = prof.email
                destinataire_nom = prof.name

        if recipient_email:
            self.env['mail.mail'].create({
                'subject': f"NOUVEAU TICKET [{ticket.category.upper()}] : {ticket.name}",
                'body_html': f"""
                        <div style="font-family: Arial;">
                            <p>Bonjour <strong>{destinataire_nom}</strong>,</p>
                            <p>Un nouveau ticket a été ouvert par <strong>{ticket.student_id.name}</strong>.</p>
                            <p><strong>Sujet :</strong> {ticket.name}</p>
                            <hr/>
                            <p>Veuillez traiter cette demande via l'interface Odoo.</p>
                        </div>
                    """,
                'email_to': recipient_email,
            }).send()

        return ticket


    def action_solve(self):
        for rec in self:
            rec.state = 'solved'
        return True