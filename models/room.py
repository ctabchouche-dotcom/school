from odoo import models, fields

class Room(models.Model):
    _name = 'school.room'
    _description = 'Salle'

    name = fields.Char(required=True)
    room_type = fields.Selection([
        ('amphi','amphi'),
        ('salle','salle'),
        ('labo','labo')
    ],required=True)