from odoo import models,fields

class Timetable(models.Model):
    _name = "school.timetable"
    _description = "Emploi du temps"
    _order = "day_of_week, start_time, id"

    program_id = fields.Many2one('school.program', string="Programme", ondelete='cascade')
    day_of_week = fields.Selection([
        ('0', 'Dimanche'),
        ('1', 'Lundi'),
        ('2', 'Mardi'),
        ('3', 'Mercredi'),
        ('4', 'Jeudi'),
    ], string="Jour", required=True)

    start_time = fields.Float(string="Heure de début", required=True)
    end_time = fields.Float(string="Heure de fin", required=True)
    classe_id = fields.Many2one('school.classes', string="Classe", required=True)
    matiere_id = fields.Many2one('school.matiere', string="Matière", required=True)
    type_cours = fields.Selection([
        ('cours', 'Cours'),
        ('td', 'TD'),
        ('tp', 'TP'),
    ], string="Type", required=True)
    teacher_id = fields.Many2one(related="matiere_id.professeur_id", string="Professeur")
    room_id = fields.Many2one('school.room', string="Room")