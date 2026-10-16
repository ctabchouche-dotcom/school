import base64
from odoo.exceptions import UserError
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import qrcode
from io import BytesIO

class Student(models.Model):
    _name = 'school.student'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Student'

    name = fields.Char(string="Nom", required=True,tracking=True)
    user_id = fields.Many2one('res.users', string="Utilisateur Odoo lié")
    age = fields.Integer(string="Âge",tracking=True)
    email = fields.Char(string="Email")
    qr_code = fields.Binary(string="QR Code",attachment=True)
    image_1920 = fields.Image("Photo de l'étudiant", max_width=1920, max_height=1920)
    active = fields.Boolean(default=True,tracking=True)
    nationality = fields.Selection(
            [
                ('ma', 'Marocain'),
                ('fr', 'Français'),
                ('dz', 'Algérien'),
                ('tn', 'Tunisien'),
            ],
            string="Nationalité",
            required=True,
            default='dz'
        )
    matricule = fields.Char(string ="Matricule")
    specialite_id = fields.Many2one('school.specialite',string ="Specialite")
    niveau = fields.Selection([
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
        ('Phd', 'Doctorat'),
    ],
        string="Niveau académique",
    )
    classe_id = fields.Many2one('school.classes',string ="Classe")
    state = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('active', 'Actif'),
            ('confirmed', 'Confirmé'),
            ('archived', 'Archivé'),
        ],
        string="Statut",
        default='draft',
        tracking=True
    )
    log_ids = fields.One2many(
        'school.student.log',
        'student_id',
        string="Historique",

    )

    @api.depends('name')
    def generate_qrcode(self):
        for rec in self:
            qr_data = f"STUDENT_ID:{rec.id}"
            qr = qrcode.QRCode(version=1, border=5, box_size=5, )
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_img = base64.b64encode(buffer.getvalue())
            rec.qr_code = qr_img

    @api.depends('name')
    def create(self, vals):
        res = super(Student, self).create(vals)
        res.generate_qrcode()
        res.invalidate_model(['qr_code'])
        res.sudo().send_qrcode()
        return res

    @api.depends('email')
    def send_qrcode(self):
        for rec in self:
            if not rec.email:
                continue

            if not rec.qr_code:
                rec.generate_qrcode()

            attachment = self.env['ir.attachment'].create({
                'name': f'Badge_{rec.name}.png',
                'type': 'binary',
                'datas': rec.qr_code,
                'res_model': 'school.student',
                'res_id': rec.id,
                'mimetype': 'image/png',
            })

            mail_values = {
                'subject': f"Votre badge numérique - {rec.name}",
                'body_html': f"""
                            <div style="font-family: Arial; text-align: center;">
                                <h3>Bonjour {rec.name},</h3>
                                <p>Veuillez trouver ci-joint votre badge QR Code pour l'appel.</p>
                            </div>
                        """,
                'email_to': rec.email,
                'attachment_ids': [(4, attachment.id)],
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()

    @api.constrains('age')
    def _check_age(self):
        for record in self:
            if record.age < 0:
                raise ValidationError(
                    "❌ L'âge ne peut pas être négatif."
                )

            if record.age < 5:
                raise ValidationError(
                    "❌ Un étudiant doit avoir au moins 5 ans."
                )

    _sql_constraints = [
       ('age_positive', 'CHECK(age >= 0)', "L'âge doit être positif."),
        ]
    is_major = fields.Boolean(
        string="Majeur",
        compute="_compute_is_major",
        store=True
    )
    is_algerian = fields.Boolean(string="Algerian",compute="_compute_is_algerian", store=True)
    @api.depends('nationality')
    def _compute_is_algerian(self):
        for record in self:
            record.is_algerian = record.nationality == 'dz'
    @api.depends('age')
    def _compute_is_major(self):
        for record in self:
            record.is_major = record.age >= 18
    @api.depends('state')
    def action_activate(self):
        for student in self:
            student.state = 'active'
    def action_archive(self):
        for student in self:
                if not student.specialite_id:
                    raise UserError(
                        "Impossible d’activer l’étudiant sans spécialité."
                    )
        student.state = 'archived'
        student.active = False

    def action_confirm(self):
            for student in self:
                old = student.state
                student.state = 'confirmed'
                self.env['school.student.log'].create({
                    'student_id': student.id,
                    'old_state': old,
                    'new_state': 'confirmed',
                })
            student.message_post(
                body=f"✅ L'inscription de <b>{student.name}</b> a été confirmée.",
                subtype_xmlid="mail.mt_note"
            )
    grade_id = fields.One2many('school.grade', 'student_id', string="Grade")
    moyenne_s1 = fields.Float(string="Moyenne semestre 1",compute="_compute_is_calcul_moyenne")
    moyenne_s2 = fields.Float(string="Moyenne semestre 2",compute="_compute_is_calcul_moyenne")
    moyenne_annuel = fields.Float(string="Moyenne annuelle",compute="_compute_is_calcul_moyenne")
    @api.depends('grade_id')
    def _compute_is_calcul_moyenne(self):
        for student in self:
            totalS1 = coefS1 = 0
            totalS2 = coefS2 = 0
            for grade in student.grade_id:
                if grade.semester == "S1":
                  totalS1 += grade.somme_matiere
                  coefS1 += grade.matiere_id.coef
                elif grade.semester == "S2":
                  totalS2 += grade.somme_matiere
                  coefS2 += grade.matiere_id.coef
            student.moyenne_s1 = totalS1 / coefS1 if coefS1 != 0 else 0
            student.moyenne_s2 = totalS2 / coefS2 if coefS2 != 0 else 0
            if student.moyenne_s1 != 0 and student.moyenne_s2 != 0:
               student.moyenne_annuel = (student.moyenne_s1 + student.moyenne_s2) / 2
            else:
              student.moyenne_annuel = 0
