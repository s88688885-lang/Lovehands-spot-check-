import os, csv, io, json, secrets, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app=Flask(__name__)
app.config['SECRET_KEY']=os.environ.get('SECRET_KEY') or secrets.token_hex(32)
db_url=os.environ.get('DATABASE_URL', 'sqlite:///lovehands.db')
if db_url.startswith('postgres://'): db_url='postgresql://'+db_url[len('postgres://'):]
app.config['SQLALCHEMY_DATABASE_URI']=db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SESSION_COOKIE_HTTPONLY']=True
app.config['SESSION_COOKIE_SAMESITE']='Lax'
app.config['SESSION_COOKIE_SECURE']=os.environ.get('COOKIE_SECURE','0')=='1'
app.config['PERMANENT_SESSION_LIFETIME']=datetime.timedelta(hours=8)
app.config['MAX_CONTENT_LENGTH']=2*1024*1024
if os.environ.get('RENDER'):
    app.config['SESSION_COOKIE_SECURE']=True

db=SQLAlchemy(app)
SECTIONS=[
 ('Section One – On Arrival in the Home', [
 'Does the Care Worker arrive at the agreed time?', 'Does the Care Worker wear visible identification?', 'Does the Care Worker greet the Service User appropriately and introduce themselves?', 'Does the Care Worker explain the purpose of the visit and seek permission to enter / continue?']),
 ('Section Two – Care Plan', [
 "Is the Care Worker aware of the Service User's Care Plan and its updates?", "Does the Care Worker check the Service User's previous Visit Notes upon arrival?", "Does the Care Worker seek the Service User's consent before delivering any aspect of care?", 'Does the Care Worker know what care the Service User needs?']),
 ('Section Three – Safe Working Practices', [
 'Does the Care Worker wash their hands before and after providing care and support?', 'Does the Care Worker use PPE correctly?', 'Is the Care Worker vigilant for hazards in the home?', 'Is any food handled correctly and hygienically?', 'Is the working area kept clean and tidy and is any PPE disposed of correctly?']),
 ('Section Four – Medication', ['Is the MAR completed correctly?', 'Does the Care Worker follow the 6 Rights of Medication correctly?']),
 ('Section Five – Attitude and Behaviour', [
 'Does the Care Worker communicate well with the Service User and evidence compassionate care?', 'Does the Care Worker respect the privacy of the Service User?', 'Does the Care Worker respect the dignity of the Service User?', 'Does the Care Worker allow the Service User to make their own choices?', 'Does the Care Worker work in an enabling way?']),
 ('Section Six – Recording', ['Does the Care Worker accurately record on the care records the activities that have been undertaken?', 'Does the Care Worker log out correctly if electronic monitoring is used?']),
 ('Section Seven – Service User Feedback', [
 'Do you know which Care Worker will be coming to visit you?', 'Does the Care Worker usually wear identification?', 'Does your Care Worker come on time?', 'Does the Care Worker respect your privacy and treat you with dignity?', 'Does the Care Worker usually wear gloves and plastic aprons for personal care?', 'Does the Care Worker make you feel comfortable and safe?', 'Do you feel in control of your care service? (Can you make your own choices?)', 'Do you know how to make a complaint?', 'If you have made a complaint, was it resolved?', 'Are you happy with the care you receive from Lovehands Care Services Limited?', 'Is there anything else you want to tell me about your care?'])]

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(100),unique=True,nullable=False)
    full_name=db.Column(db.String(160),nullable=False)
    password_hash=db.Column(db.String(300),nullable=False)
    role=db.Column(db.String(20),nullable=False,default='assessor')
    active=db.Column(db.Boolean,nullable=False,default=True)
    created_at=db.Column(db.DateTime,default=datetime.datetime.utcnow)
class Submission(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    assessor_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    assessor=db.relationship('User')
    service_user=db.Column(db.String(160),nullable=False)
    care_workers=db.Column(db.String(500),nullable=False)
    spot_date=db.Column(db.String(20),nullable=False)
    arrive=db.Column(db.String(20))
    depart=db.Column(db.String(20))
    reason=db.Column(db.String(160),nullable=False)
    outcome=db.Column(db.String(20),nullable=False)
    answers=db.Column(db.Text,nullable=False)
    actions=db.Column(db.Text,nullable=False)
    signature=db.Column(db.String(160),nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)

# Additional medication competency assessments are stored separately so existing spot checks remain unchanged.
MEDICATION_SECTIONS = [
    ('Training and Policy', [
        'Has the staff member completed the medication training set out by Love Hands Care?',
        'Has the staff member read the medication policy and signed to indicate they have done so?',
        'Does the staff member know how to access the medication policy should they need to?'
    ]),
    ('Administration of Medication', [
        'Did the staff member wash their hands or sanitize before putting on their gloves?',
        'Did the staff member ask for the client’s consent to do their medication?',
        'Has the staff member checked the MAR chart to make sure they are giving the correct medication and the correct dose at the right time?',
        'Did the staff member offer the client a drink to use to take their medication?',
        'Did the staff member observe the client taking their medication?',
        'Did the staff member record using the correct codes on the MAR chart?',
        'If the medication was not given, has the staff member recorded this correctly and raised a concern?',
        'Are there sufficient amounts of medication for the client’s needs?',
        'Is the medication stored safely?',
        'Has the staff member returned any medication to the fridge if needed?',
        'Is there any excess medication on the premises?',
        'Does the client take any PRN medication?',
        'Has the staff member recorded this correctly?',
        'Did the staff member remove their PPE in the correct way?',
        'Did the staff member wash their hands or sanitize after removing their gloves?',
        'Does the staff member know who to contact with any medication concerns?',
        'Can the staff member describe what to do if there is a medication error?',
        'Can the staff member describe what they do if they find a medication error by another care staff member?'
    ])
]
MEDICATION_OUTCOMES = [
    'Do you consider the staff member to be competent to deliver medication?',
    'Do you feel the staff member needs any extra training or to redo their training?',
    'Was the staff member able to answer the questions regarding errors?'
]

class MedicationSubmission(db.Model):
    __tablename__ = 'medication_submission'
    id=db.Column(db.Integer,primary_key=True)
    assessor_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    assessor=db.relationship('User')
    staff_name=db.Column(db.String(160),nullable=False)
    assessment_date=db.Column(db.String(20),nullable=False)
    answers=db.Column(db.Text,nullable=False)
    notes=db.Column(db.Text,nullable=False,default='')
    outcomes=db.Column(db.Text,nullable=False)
    assessor_name=db.Column(db.String(160),nullable=False)
    assessor_signature=db.Column(db.String(160),nullable=False)
    staff_signature=db.Column(db.String(160),nullable=False)
    next_assessment=db.Column(db.String(20),nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.datetime.utcnow,nullable=False)

with app.app_context(): db.create_all()

def csrf():
    if 'csrf' not in session: session['csrf']=secrets.token_urlsafe(32)
    return session['csrf']
app.jinja_env.globals['csrf_token']=csrf
app.jinja_env.globals['current_user_role']=lambda: (db.session.get(User,session['uid']).role if session.get('uid') and db.session.get(User,session['uid']) else None)
@app.before_request
def csrf_check():
    if request.method=='POST':
        if not secrets.compare_digest(request.form.get('_csrf',''),session.get('csrf','')): abort(400,description='Invalid form token. Refresh and retry.')
@app.after_request
def headers(response):
    response.headers['X-Frame-Options']='DENY'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['Cache-Control']='no-store'
    response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'self'"
    return response

def logged_in(view):
    @wraps(view)
    def decorated(*args,**kwargs):
        if not session.get('uid'): return redirect(url_for('login'))
        user=db.session.get(User,session['uid'])
        if not user or not user.active: session.clear();return redirect(url_for('login'))
        return view(*args,**kwargs)
    return decorated

def admin_only(view):
    @wraps(view)
    @logged_in
    def decorated(*args,**kwargs):
        if db.session.get(User,session['uid']).role!='admin':abort(403)
        return view(*args,**kwargs)
    return decorated

@app.route('/')
def index():
    if not User.query.filter_by(role='admin').first():return redirect(url_for('setup'))
    if not session.get('uid'):return redirect(url_for('login'))
    return redirect(url_for('dashboard') if db.session.get(User,session['uid']).role=='admin' else url_for('new_check'))

@app.route('/setup',methods=['GET','POST'])
def setup():
    if User.query.filter_by(role='admin').first():abort(404)
    token=os.environ.get('SETUP_TOKEN','')
    if not token:return render_template('setup_disabled.html'),503
    if request.method=='POST':
        if not secrets.compare_digest(request.form.get('setup_token',''),token):flash('Incorrect setup token.','error')
        elif len(request.form.get('password',''))<12:flash('Choose a password with at least 12 characters.','error')
        elif request.form.get('password')!=request.form.get('confirm'):flash('Passwords do not match.','error')
        elif not request.form.get('full_name','').strip():flash('Enter your full name.','error')
        else:
            u=User(username='admin',full_name=request.form['full_name'].strip(),role='admin',password_hash=generate_password_hash(request.form['password'],method='scrypt'))
            db.session.add(u);db.session.commit();flash('Administrator created. Please sign in.','success');return redirect(url_for('login'))
    return render_template('setup.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form.get('username','').strip().lower()
        u=User.query.filter_by(username=username,active=True).first()
        if u and check_password_hash(u.password_hash,request.form.get('password','')):
            session.clear();session.permanent=True;session['uid']=u.id;session['csrf']=secrets.token_urlsafe(32)
            return redirect(url_for('dashboard') if u.role=='admin' else url_for('new_check'))
        flash('Invalid username or password.','error')
    return render_template('login.html')

@app.route('/logout',methods=['POST'])
@logged_in
def logout():session.clear();return redirect(url_for('login'))

@app.route('/spot-check/new',methods=['GET','POST'])
@logged_in
def new_check():
    user=db.session.get(User,session['uid'])
    if request.method=='POST':
        required=['service_user','care_workers','spot_date','reason','outcome','signature']
        missing=[k for k in required if not request.form.get(k,'').strip()]
        if missing: flash('Please complete the required fields.','error')
        else:
            answers=[]
            for si,(title,questions) in enumerate(SECTIONS):
                for qi,q in enumerate(questions):
                    key=f'q_{si}_{qi}'
                    val=request.form.get(key,'')
                    if val not in ('Yes','No','N/A'):
                        flash('Please answer every question (Yes, No or N/A).','error')
                        return render_template('form.html',sections=SECTIONS,user=user)
                    answers.append({'section':title,'question':q,'answer':val,'comment':request.form.get(key+'_comment','').strip()[:3000]})
            if request.form.get('outcome') not in ('Passed','Failed'):flash('Select a valid outcome.','error')
            else:
                actions=[{'action':request.form.get(f'action_{i}','').strip()[:3000],'by':request.form.get(f'action_by_{i}','').strip()[:160]} for i in range(1,8)]
                record=Submission(assessor_id=user.id,service_user=request.form['service_user'].strip()[:160],care_workers=request.form['care_workers'].strip()[:500],spot_date=request.form['spot_date'],arrive=request.form.get('arrive'),depart=request.form.get('depart'),reason=request.form['reason'].strip()[:160],outcome=request.form['outcome'],answers=json.dumps(answers),actions=json.dumps(actions),signature=request.form['signature'].strip()[:160])
                db.session.add(record);db.session.commit();flash(f'Spot check #{record.id} submitted successfully.','success');return redirect(url_for('my_submissions'))
    return render_template('form.html',sections=SECTIONS,user=user)

@app.route('/my-submissions')
@logged_in
def my_submissions():
    records=Submission.query.filter_by(assessor_id=session['uid']).order_by(Submission.created_at.desc()).all()
    return render_template('records.html',records=records,title='My submissions',admin=False)

@app.route('/admin')
@admin_only
def dashboard():
    records=Submission.query.order_by(Submission.created_at.desc()).all()
    count=len(records)
    failed=sum(r.outcome=='Failed' for r in records)
    return render_template('dashboard.html',records=records,total=count,passed=count-failed,failed=failed,assessors=User.query.filter_by(role='assessor',active=True).count())

@app.route('/admin/users',methods=['GET','POST'])
@admin_only
def users():
    if request.method=='POST':
        username=request.form.get('username','').strip().lower()
        full_name=request.form.get('full_name','').strip()
        password=request.form.get('password','')
        role=request.form.get('role','assessor')
        if not username or not full_name or len(password)<12 or role not in ('admin','assessor'):
            flash('Provide username, full name, role and password of at least 12 characters.','error')
        elif User.query.filter_by(username=username).first():flash('Username already exists.','error')
        else:
            db.session.add(User(username=username,full_name=full_name,password_hash=generate_password_hash(password,method='scrypt'),role=role));db.session.commit();flash('User created.','success');return redirect(url_for('users'))
    return render_template('users.html',users=User.query.order_by(User.id.asc()).all())

@app.route('/admin/users/<int:user_id>/toggle',methods=['POST'])
@admin_only
def toggle_user(user_id):
    u=db.session.get(User,user_id)
    if not u:abort(404)
    if u.id==session['uid']:flash('You cannot deactivate your own account.','error')
    elif u.role=='admin' and u.active and User.query.filter_by(role='admin',active=True).count()<=1:flash('At least one active admin is required.','error')
    else:u.active=not u.active;db.session.commit();flash('Account updated.','success')
    return redirect(url_for('users'))

@app.route('/admin/users/<int:user_id>/reset',methods=['POST'])
@admin_only
def reset_user(user_id):
    u=db.session.get(User,user_id)
    if not u:abort(404)
    password=request.form.get('password','')
    if len(password)<12:flash('Password must be at least 12 characters.','error')
    else:u.password_hash=generate_password_hash(password,method='scrypt');db.session.commit();flash('Password updated.','success')
    return redirect(url_for('users'))

@app.route('/account/password',methods=['GET','POST'])
@logged_in
def change_password():
    user=db.session.get(User,session['uid'])
    if request.method=='POST':
        old=request.form.get('current','');new=request.form.get('new','')
        if not check_password_hash(user.password_hash,old):flash('Current password is incorrect.','error')
        elif len(new)<12:flash('New password must be at least 12 characters.','error')
        elif new!=request.form.get('confirm'):flash('New passwords do not match.','error')
        else:user.password_hash=generate_password_hash(new,method='scrypt');db.session.commit();flash('Password changed.','success');return redirect(url_for('index'))
    return render_template('password.html')

@app.route('/spot-check/<int:record_id>')
@logged_in
def detail(record_id):
    record=db.session.get(Submission,record_id)
    if not record:abort(404)
    u=db.session.get(User,session['uid'])
    if u.role!='admin' and record.assessor_id!=u.id:abort(403)
    return render_template('detail.html',record=record,answers=json.loads(record.answers),actions=json.loads(record.actions))

@app.route('/admin/export.csv')
@admin_only
def export_csv():
    output=io.StringIO();writer=csv.writer(output)
    writer.writerow(['ID','Submitted at UTC','Spot date','Service user','Assessor','Care worker(s)','Reason','Outcome','Arrival','Departure','Signature'])
    for r in Submission.query.order_by(Submission.id.asc()).all():
        writer.writerow([r.id,r.created_at.isoformat(),r.spot_date,r.service_user,r.assessor.full_name,r.care_workers,r.reason,r.outcome,r.arrive,r.depart,r.signature])
    return Response(output.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=lovehands-spot-check-summary.csv'})

@app.route('/health')
def health():return 'OK',200



@app.route('/medication/new',methods=['GET','POST'])
@logged_in
def new_medication():
    user=db.session.get(User,session['uid'])
    if request.method=='POST':
        required=('staff_name','assessment_date','assessor_name','assessor_signature','staff_signature','next_assessment')
        if any(not request.form.get(name,'').strip() for name in required):
            flash('Complete all required details, including names, signatures and next assessment date.','error')
        else:
            answers=[]
            for si,(section,questions) in enumerate(MEDICATION_SECTIONS):
                for qi,question in enumerate(questions):
                    val=request.form.get(f'm_{si}_{qi}','')
                    allowed=('Yes','No','N/A') if (si,qi)==(1,9) else ('Yes','No')
                    if val not in allowed:
                        flash('Please answer every medication question.','error')
                        return render_template('medication_form.html',user=user,sections=MEDICATION_SECTIONS,outcome_questions=MEDICATION_OUTCOMES)
                    answers.append({'section':section,'question':question,'answer':val})
            outcomes=[]
            for i,question in enumerate(MEDICATION_OUTCOMES):
                val=request.form.get(f'outcome_{i}','')
                if val not in ('Yes','No'):
                    flash('Complete all three competency outcome questions.','error')
                    return render_template('medication_form.html',user=user,sections=MEDICATION_SECTIONS,outcome_questions=MEDICATION_OUTCOMES)
                outcomes.append({'question':question,'answer':val,'signed':request.form.get(f'outcome_signed_{i}','').strip()[:160]})
            record=MedicationSubmission(
                assessor_id=user.id,staff_name=request.form['staff_name'].strip()[:160],
                assessment_date=request.form['assessment_date'],answers=json.dumps(answers),
                notes=request.form.get('notes','').strip()[:10000],outcomes=json.dumps(outcomes),
                assessor_name=request.form['assessor_name'].strip()[:160],
                assessor_signature=request.form['assessor_signature'].strip()[:160],
                staff_signature=request.form['staff_signature'].strip()[:160],
                next_assessment=request.form['next_assessment'])
            db.session.add(record);db.session.commit()
            flash(f'Medication competency #{record.id} submitted successfully.','success')
            return redirect(url_for('medication_records'))
    return render_template('medication_form.html',user=user,sections=MEDICATION_SECTIONS,outcome_questions=MEDICATION_OUTCOMES)

@app.route('/medication/records')
@logged_in
def medication_records():
    u=db.session.get(User,session['uid'])
    q=MedicationSubmission.query
    if u.role!='admin': q=q.filter_by(assessor_id=u.id)
    records=q.order_by(MedicationSubmission.created_at.desc()).all()
    return render_template('medication_records.html',records=records,admin=u.role=='admin')

@app.route('/medication/<int:record_id>')
@logged_in
def medication_detail(record_id):
    record=db.session.get(MedicationSubmission,record_id)
    if not record:abort(404)
    u=db.session.get(User,session['uid'])
    if u.role!='admin' and record.assessor_id!=u.id:abort(403)
    return render_template('medication_detail.html',record=record,answers=json.loads(record.answers),outcomes=json.loads(record.outcomes))

@app.route('/admin/medication-export.csv')
@admin_only
def medication_export_csv():
    output=io.StringIO();writer=csv.writer(output)
    writer.writerow(['ID','Submitted at UTC','Assessment date','Staff assessed','Assessor','Competent','Extra training','Understands errors','Next assessment'])
    for r in MedicationSubmission.query.order_by(MedicationSubmission.id.asc()).all():
        outcomes=json.loads(r.outcomes)
        writer.writerow([r.id,r.created_at.isoformat(),r.assessment_date,r.staff_name,r.assessor_name,
                         outcomes[0]['answer'],outcomes[1]['answer'],outcomes[2]['answer'],r.next_assessment])
    return Response(output.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=lovehands-medication-competency-summary.csv'})

if __name__=='__main__': app.run(debug=os.environ.get('FLASK_DEBUG')=='1')
