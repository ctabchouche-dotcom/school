from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta
import random


class Program(models.Model):
    _name = 'school.program'
    _description = 'Program'

    name = fields.Char(string="Nom du Programme", required=True)
    classe_id = fields.Many2many('school.classes', string="Classes")
    semester = fields.Selection([
        ('S1', 'Semestre 1'),
        ('S2', 'Semestre 2'),
    ], string="Semestre")


    volume_horaire_id = fields.One2many("school.program_volume", "program_id", string="Horaire")

    def action_generate_timetable(self):
        timetable_obj = self.env['school.timetable']
        start_hour = 8.5
        end_hour = 16.0
        slot_duration = 1.0
        pause_start = 11.5
        pause_end = 13.0

        for current_classe in self.classe_id:
            existing = timetable_obj.search([('program_id', '=', self.id), ('classe_id', '=', current_classe.id)],
                                            limit=1)
            if existing:
                raise ValidationError(f"L'emploi du temps pour {current_classe.name} existe déjà.")

            all_sessions = []
            for vol in self.volume_horaire_id:
                affectation = self.env['school.affectation'].search([
                    ('matiere_id', '=', vol.matiere_id.id),
                    ('classe_id', '=', current_classe.id),
                    ('semester', '=', self.semester)
                ], limit=1)
                prof_id = affectation.teacher_id.id if affectation else False

                for c_type, hours in [('cours', vol.cours), ('td', vol.td), ('tp', vol.tp)]:
                    for _ in range(int(hours / slot_duration)):
                        all_sessions.append({
                            'matiere_id': vol.matiere_id.id,
                            'type': c_type,
                            'prof_id': prof_id
                        })

            random.shuffle(all_sessions)

            days = ['0', '1', '2', '3', '4']
            curr_day_idx = 0
            curr_time = start_hour

            for session in all_sessions:
                conflit = True
                selected_room = False

                while conflit:
                    if curr_time >= pause_start and curr_time < pause_end:
                        curr_time = pause_end

                    if curr_time + slot_duration > end_hour:
                        curr_time = start_hour
                        curr_day_idx += 1

                    if curr_day_idx >= len(days):
                        raise ValidationError(f"Plus de place pour la classe {current_classe.name}")

                    req_room_type = 'labo' if session['type'] == 'tp' else 'amphi' if session['type'] == 'cours' else 'salle'
                    if session['prof_id']:
                        t_busy = timetable_obj.search([
                            ('teacher_id', '=', session['prof_id']),
                            ('day_of_week', '=', days[curr_day_idx]),
                            ('start_time', '=', curr_time)
                        ], limit=1)
                        if t_busy:
                            curr_time += slot_duration
                            continue

                    rooms = self.env['school.room'].search([('room_type', '=', req_room_type)])
                    for r in rooms:
                        r_busy = timetable_obj.search([
                            ('room_id', '=', r.id),
                            ('day_of_week', '=', days[curr_day_idx]),
                            ('start_time', '=', curr_time)
                        ], limit=1)
                        if not r_busy:
                            selected_room = r
                            break

                    if not selected_room:
                        curr_time += slot_duration
                    else:
                        conflit = False

                timetable_obj.create({
                    'program_id': self.id,
                    'classe_id': current_classe.id,
                    'day_of_week': days[curr_day_idx],
                    'start_time': curr_time,
                    'end_time': curr_time + slot_duration,
                    'matiere_id': session['matiere_id'],
                    'type_cours': session['type'],
                    'teacher_id': session['prof_id'],
                    'room_id': selected_room.id if selected_room else False,
                })
                curr_time += slot_duration

    def action_reset_timetable(self):
        for record in self:
            slots = self.env['school.timetable'].search([('program_id', '=', record.id)])
            slots.unlink()