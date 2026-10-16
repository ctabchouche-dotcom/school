import base64
from odoo import http, fields
from odoo.http import request
from datetime import datetime
import json


class Portal(http.Controller):

    @http.route(['/my/absences'], type='http', auth="user", website=True)
    def portal_my_absences(self, **kw):
        student = request.env['school.student'].search([('user_id', '=', request.uid)], limit=1)

        if not student:
            return "Erreur : Aucun profil étudiant n'est lié à votre compte utilisateur."


        absences = request.env['school.absence'].search([
            ('student_id', '=', student.id)
        ], order="date_absence desc")


        return request.render("school.portal_absences_template", {
            'student': student,
            'absences': absences,
            'page_name': 'absences',
        })

    @http.route(['/my/grade'], type='http', auth="user", website=True)
    def portal_my_grade(self, **kw):
        student = request.env['school.student'].search([('user_id', '=', request.uid)], limit=1)

        if not student:
            return "Erreur : Aucun profil étudiant n'est lié à votre compte utilisateur."

        grade = request.env['school.grade'].search([
            ('student_id', '=', student.id)], )

        return request.render("school.portal_grade_template", {
            'student': student,
            'grade': grade,
            'page_name': 'bulletin'
        })

    @http.route(['/my/school/dashboard'], type='http', auth="user", website=True)
    def portal_school_dashboard(self, **kw):
        student = request.env['school.student'].search([('user_id', '=', request.uid)], limit=1)
        if not student:
            return request.render("website.403")

        abs_count = request.env['school.absence'].search_count(
            [('student_id', '=', student.id), ('is_justified', '=', False)])
        abs_valide_count = request.env['school.absence'].search_count(
            [('student_id', '=', student.id), ('is_justified', '=', True)])

        timetable = request.env['school.timetable'].search([('classe_id', '=', student.classe_id.id)],
                                                           order='day_of_week, start_time')
        program = timetable[:1].program_id or student.classe_id.program_id

        return request.render("school.portal_dashboard_template", {
            'student': student,
            'abs_count': abs_count,
            'abs_valide_count': abs_valide_count,
            'timetable': timetable,
            'program': program,
        })

    @http.route(['/my/badge'], type='http', auth="user", website=True)
    def portal_my_student_badge(self, **kw):
        student = request.env['school.student'].sudo().search([('user_id', '=', request.env.user.id)], limit=1)
        if not student:
            return request.not_found()

        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'school.action_report_student_badge', [student.id]
        )

        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename=Mon_Badge_Etudiant.pdf;')
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/my/absence/justify/<int:absence_id>'], type='http', auth="user", website=True)
    def justify_absence(self, absence_id, **kw):
        student = request.env['school.student'].search([('user_id', '=', request.uid)], limit=1)
        absence = request.env['school.absence'].browse(absence_id)

        if absence.exists() and absence.student_id.id == student.id:
            file = kw.get('attachment')
            if file:
                file_content = base64.b64encode(file.read())

                absence.sudo().write({
                    'justification_file': file_content,
                    'justification_filename': file.filename,
                    'state': 'pending',
                })

        return request.redirect('/my/absences?message=success')

    @http.route(['/my/reclamation'], type='http', auth="user", website=True)
    def ticket_reclamation(self, **kw):
        student = request.env['school.student'].search([('user_id', '=', request.uid)], limit=1)
        tickets = request.env['school.ticket'].search([(
            'student_id', '=', student.id)])
        return request.render("school.portal_reclamation_template", {
               'ticket': tickets,
               'page_name': 'reclamation',
            })
    @http.route(['/my/reclamation/new'], type='http', auth="user", website=True)
    def reclamation_new(self, **kw):
        matiere = request.env['school.matiere'].search([])
        tickets = request.env['school.ticket'].search([])
        return request.render("school.portal_new_reclamation_template", {
            'matiere': matiere,
            'ticket': tickets,
            'page_name': 'nouvelle_reclamation',
        })

    @http.route(['/api/students', '/api/students/'], type='http', auth='user', methods=['GET'], csrf=False)
    def get_students_api(self):
        if not request.env.user.has_group('school.group_school_manager'):
            return request.make_response(
                json.dumps({'status': 'error', 'message': 'Accès refusé'}),
                headers=[('Content-Type', 'application/json')],
                status=403,
            )
        students = request.env['school.student'].search([])
        data = [{'id': s.id, 'name': s.name, 'class': s.classe_id.name} for s in students]
        return request.make_response(
            json.dumps({'result': {'data': data}}),
            headers=[('Content-Type', 'application/json')],
        )
    @http.route(['/my/ticket/save'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def ticket_save(self, **kw):
        student = request.env['school.student'].search([('user_id', '=', request.uid)], limit=1)

        if not student:
            return "Erreur : Profil étudiant non trouvé."

        vals = {
            'name': kw.get('name'),
            'category': kw.get('category'),
            'description': kw.get('description'),
            'student_id': student.id,
            'state': 'new',
        }

        if kw.get('matiere_id'):
            vals['matiere_id'] = int(kw.get('matiere_id'))

        request.env['school.ticket'].sudo().create(vals)

        return request.redirect('/my/reclamation')

class TeacherPortal(http.Controller):
    @http.route(['/my/teacher/dashboard'], type='http', auth="user", website=True)
    def teacher_dashboard(self, **kw):
        user = request.env.user
        teacher = request.env['school.teacher'].search([('user_id', '=', user.id)], limit=1)

        if not teacher:
            return request.render("school.portal_error", {'message': "Profil professeur non trouvé."})

        today_index = (datetime.today().weekday() + 1) % 7
        today_str = str(today_index)

        sessions = request.env['school.timetable'].search([
            ('teacher_id', '=', teacher.id),
            ('day_of_week', '=', today_str)
        ], order='start_time asc')

        return request.render("school.teacher_dashboard_template", {
            'teacher': teacher,
            'sessions': sessions,
            'today_label':
                dict(request.env['school.timetable'].fields_get(allfields=['day_of_week'])['day_of_week']['selection'])[
                    today_str]
        })

    @http.route(['/my/teacher/session/<int:session_id>'], type='http', auth="user", website=True)
    def teacher_session_call(self, session_id, **kw):
        session = request.env['school.timetable'].browse(session_id)

        if session.teacher_id.user_id.id != request.env.user.id:
            return request.redirect('/my/teacher/dashboard')

        students = request.env['school.student'].search([
            ('classe_id', '=', session.classe_id.id),
            ('state', '=', 'active')
        ])

        return request.render("school.teacher_attendance_template", {
            'session': session,
            'students': students,
        })

    @http.route(['/my/teacher/session/validate'], type='json', auth="user", csrf=False)
    def validate_attendance(self, session_id, present_student_ids):
        session = request.env['school.timetable'].browse(session_id)

        all_students = request.env['school.student'].search([('classe_id', '=', session.classe_id.id)])

        absent_students = all_students.filtered(lambda s: s.id not in present_student_ids)

        created_absences = 0

        for student in absent_students:
            existing = request.env['school.absence'].search([
                ('student_id', '=', student.id),
                ('matiere_id', '=', session.matiere_id.id),
                ('date_absence', '=', fields.Date.today())
            ])

            if not existing:
                request.env['school.absence'].sudo().create({
                    'student_id': student.id,
                    'matiere_id': session.matiere_id.id,
                    'date_absence': fields.Date.today(),
                    'state': 'draft',
                    'is_justified': False
                })
                created_absences += 1

        return {'status': 'success',
                'absences_created': created_absences
                }


class StudentApi(http.Controller):

    @http.route('/api/create_student', type='http', auth='user', methods=['POST'], csrf=False)
    def create_student_api(self, **kw):
        if not request.env.user.has_group('school.group_school_manager'):
            return self.response({'status': 'error', 'message': 'Accès refusé'}, status=403)
        try:
            name = kw.get('name')
            age = kw.get('age', 0)
            email = kw.get('email')
            matricule = kw.get('matricule')
            nationality = kw.get('nationality', 'dz')

            classe_id = int(kw.get('classe_id')) if kw.get('classe_id') else False
            spec_id = int(kw.get('specialite_id')) if kw.get('specialite_id') else False

            if not name:
                return self.response({'status': 'error', 'message': 'Le nom est requis'})

            new_student = request.env['school.student'].create({
                'name': name,
                'age': int(age),
                'email': email,
                'matricule': matricule,
                'nationality': nationality,
                'classe_id': classe_id,
                'specialite_id': spec_id,
                'state': 'draft',
            })

            new_student.generate_qrcode()

            return self.response({
                'status': 'success',
                'id': new_student.id,
                'qr_generated': bool(new_student.qr_code),
                'message': f'Étudiant {name} créé avec succès'
            })

        except Exception as e:
            # Si Odoo renvoie une erreur (ex: âge < 5 ans), on la capture ici
            return self.response({'status': 'error', 'message': str(e)})

    def response(self, data, status=200):
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')],
            status=status,
        )


