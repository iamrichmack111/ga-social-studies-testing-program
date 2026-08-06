from __future__ import annotations
import csv, io, os, random, secrets, sqlite3, time
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

APP_NAME="Georgia Social Studies Testing Program"
APP_SLUG="ga_social_studies_testing_program"
DATA_ROOT=Path(os.environ.get("RICHMACK_GRADES_DIR",Path.home()/"KIDS-HW"/"grades")).expanduser().resolve()
GAME_DIR=DATA_ROOT/APP_SLUG
DATABASE=GAME_DIR/f"{APP_SLUG}.db"
GAME_DIR.mkdir(parents=True,exist_ok=True)

app=Flask(__name__)
app.secret_key=os.environ.get("GA_SOCIAL_SECRET",secrets.token_hex(32))
app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax")

GRADE_SCOPE={
3:"Georgia communities, geography, civics, economics, and historical figures",
4:"United States history from exploration through Reconstruction",
5:"United States history from the late 1800s through modern America",
6:"World Area Studies: Europe, Latin America, Canada, and Australia",
7:"World Area Studies: Africa, Southwest Asia, Southern and Eastern Asia",
8:"Georgia history, geography, government, civics, and economics",
}

THEMES={
"linux":{"name":"Linux Geography","topic":"geography"},
"jasmin":{"name":"Jasmin History","topic":"history"},
"aria":{"name":"Aria Civics","topic":"civics"},
"ahmeenah":{"name":"Ahmeenah Economics","topic":"economics"},
"zara":{"name":"Zara Culture","topic":"culture"},
"kaphmemeris":{"name":"Kaphmemeris Review","topic":"mixed_review"},
}

# grade -> topic -> difficulty -> list(prompt, choices, answer, standard)
BANK={
3:{
"geography":[
("Which direction is opposite east?",["West","North","South","Northeast"],"West","SS3G1"),
("What does a map key explain?",["Map symbols","Weather only","Population only","Time zones only"],"Map symbols","SS3G1"),
("Which landform is higher than surrounding land and usually has steep sides?",["Mountain","Plain","River","Island"],"Mountain","SS3G1")],
"history":[
("Why do communities preserve historic places?",["To remember important people and events","To erase old records","To stop tourism","To change geography"],"To remember important people and events","SS3H1"),
("What is a primary source?",["A record created during the time studied","A modern summary only","A fictional story","A weather chart"],"A record created during the time studied","SS3H1")],
"civics":[
("What is a responsibility of citizens?",["Obey laws","Ignore elections","Make private laws","Avoid community service"],"Obey laws","SS3CG1"),
("Why do communities have local governments?",["To provide services and make local decisions","To control other countries","To eliminate rules","To replace families"],"To provide services and make local decisions","SS3CG1")],
"economics":[
("What is a producer?",["Someone who makes goods or provides services","Someone who only buys goods","A mapmaker only","A voter only"],"Someone who makes goods or provides services","SS3E1"),
("What is a consumer?",["Someone who buys or uses goods and services","Someone who writes laws","Someone who draws maps","Someone who creates weather"],"Someone who buys or uses goods and services","SS3E1")],
"culture":[
("What is culture?",["Shared beliefs, customs, and traditions","Only government laws","Only money","Only geography"],"Shared beliefs, customs, and traditions","SS3G2")]},
4:{
"geography":[("Why were rivers important to early settlements?",["Transportation, water, and trade","They stopped farming","They removed resources","They prevented travel"],"Transportation, water, and trade","SS4G1"),
("Which region includes the Appalachian Mountains?",["Eastern United States","Central Pacific","South America","Arctic Ocean"],"Eastern United States","SS4G1")],
"history":[("What was a major reason Europeans explored the Americas?",["Trade, wealth, and new routes","To avoid all travel","To end farming","To create deserts"],"Trade, wealth, and new routes","SS4H1"),
("What document declared the colonies independent from Britain?",["Declaration of Independence","Constitution","Bill of Rights","Mayflower Compact"],"Declaration of Independence","SS4H4"),
("What was one major effect of the Civil War?",["Slavery was abolished","The colonies became British again","The Constitution ended","Westward travel stopped"],"Slavery was abolished","SS4H6")],
"civics":[("What is the purpose of the Constitution?",["Establish the framework of government","Create weather rules","Name every city","Control private beliefs"],"Establish the framework of government","SS4CG1")],
"economics":[("What is specialization?",["Focusing on a particular job or product","Producing everything alone","Avoiding trade","Using no resources"],"Focusing on a particular job or product","SS4E1")],
"culture":[("Why did different colonial regions develop different economies?",["Geography, climate, and resources differed","Everyone had identical land","Trade was illegal","No one farmed"],"Geography, climate, and resources differed","SS4G2")]},
5:{
"geography":[("How did railroads affect the United States?",["They increased movement of people and goods","They ended trade","They reduced settlement","They eliminated cities"],"They increased movement of people and goods","SS5G1")],
"history":[("What was a major cause of the Great Depression?",["Bank failures and economic collapse","The Civil War","The Louisiana Purchase","The American Revolution"],"Bank failures and economic collapse","SS5H3"),
("Why did the United States enter World War II?",["Japan attacked Pearl Harbor","The Constitution was written","The colonies rebelled","The Gold Rush began"],"Japan attacked Pearl Harbor","SS5H4"),
("What did the civil rights movement seek?",["Equal rights and an end to segregation","New colonies","Less voting","An end to public schools"],"Equal rights and an end to segregation","SS5H6")],
"civics":[("What is the role of the judicial branch?",["Interpret laws","Write laws","Command the military","Collect all taxes"],"Interpret laws","SS5CG1")],
"economics":[("What happens when demand rises while supply stays the same?",["Price often rises","Price always becomes zero","Production stops forever","Money disappears"],"Price often rises","SS5E1")],
"culture":[("How did immigration influence the United States?",["It added diverse cultures, labor, and ideas","It ended cities","It removed languages","It stopped industry"],"It added diverse cultures, labor, and ideas","SS5H1")]},
6:{
"geography":[("Which physical feature separates much of Europe from Asia?",["Ural Mountains","Nile River","Sahara Desert","Andes Mountains"],"Ural Mountains","SS6G1"),
("Which region is known for the Amazon Rainforest?",["Latin America","Europe","Canada","Australia"],"Latin America","SS6G2"),
("How does climate influence population distribution?",["People often settle where conditions support farming and work","Climate has no effect","Everyone settles in deserts","Population ignores water"],"People often settle where conditions support farming and work","SS6G3")],
"history":[("What was one effect of European colonization in Latin America?",["Cultural mixing and political control","No language change","No economic change","Total isolation"],"Cultural mixing and political control","SS6H1"),
("Why was the European Union created?",["To promote cooperation and economic integration","To end all trade","To create one world government","To eliminate borders worldwide"],"To promote cooperation and economic integration","SS6CG1")],
"civics":[("What is a parliamentary democracy?",["A system where the legislature selects the head of government","A government without elections","Rule by military only","Direct rule by a monarch"],"A system where the legislature selects the head of government","SS6CG2")],
"economics":[("Why do countries trade?",["To obtain goods and resources they do not produce efficiently","To avoid specialization","To eliminate markets","To stop currency use"],"To obtain goods and resources they do not produce efficiently","SS6E1")],
"culture":[("Why is Latin America culturally diverse?",["Indigenous, European, African, and Asian influences combined","One culture replaced all others","No migration occurred","Geography prevented contact"],"Indigenous, European, African, and Asian influences combined","SS6G4")]},
7:{
"geography":[("Which desert covers much of North Africa?",["Sahara","Gobi","Kalahari only","Mojave"],"Sahara","SS7G1"),
("Why is the Nile River important?",["It provides water, farming, and transportation","It creates monsoons in India","It divides Korea","It powers Japan only"],"It provides water, farming, and transportation","SS7G1"),
("Which climate pattern strongly affects Southern and Eastern Asia?",["Monsoons","Tundra winds only","Mediterranean snow","Atlantic hurricanes only"],"Monsoons","SS7G9")],
"history":[("What was apartheid?",["A system of racial segregation in South Africa","A trade agreement","A religion","A river project"],"A system of racial segregation in South Africa","SS7H1"),
("What was a major effect of European colonial boundaries in Africa?",["They often ignored ethnic and cultural groups","They followed every local boundary","They ended conflict","They created one language"],"They often ignored ethnic and cultural groups","SS7H1"),
("Why was India divided in 1947?",["Religious and political tensions led to India and Pakistan","China invaded","Oil was discovered","Japan required it"],"Religious and political tensions led to India and Pakistan","SS7H3")],
"civics":[("Which describes an autocratic government?",["One ruler holds most power","Citizens directly vote on every law","Power is equally divided among all people","There is no government"],"One ruler holds most power","SS7CG1")],
"economics":[("Why is oil important to Southwest Asia?",["It is a major export and source of revenue","It prevents trade","It eliminates specialization","It is the only resource used"],"It is a major export and source of revenue","SS7E4")],
"culture":[("Which religions began in Southwest Asia?",["Judaism, Christianity, and Islam","Hinduism and Buddhism only","Shinto only","Confucianism only"],"Judaism, Christianity, and Islam","SS7G8")]},
8:{
"geography":[("Which Georgia region contains the highest elevations?",["Blue Ridge","Coastal Plain","Piedmont","Valley and Ridge only"],"Blue Ridge","SS8G1"),
("Why has Atlanta become a major transportation center?",["Its location and transportation networks connect major markets","It is Georgia's only port","It borders the Atlantic Ocean","It has no highways"],"Its location and transportation networks connect major markets","SS8G1")],
"history":[("Who founded the Georgia colony in 1733?",["James Oglethorpe","George Washington","Abraham Lincoln","Hernando de Soto"],"James Oglethorpe","SS8H2"),
("What was a major effect of the cotton gin on Georgia?",["Cotton production and dependence on enslaved labor increased","Cotton farming ended","Railroads disappeared","The colony returned to Spain"],"Cotton production and dependence on enslaved labor increased","SS8H4"),
("What role did Atlanta play during the Civil War?",["It was a major railroad and supply center","It was the national capital","It remained untouched","It was a coastal naval base"],"It was a major railroad and supply center","SS8H5")],
"civics":[("What is the highest court in Georgia?",["Supreme Court of Georgia","Georgia Senate","Governor's office","County commission"],"Supreme Court of Georgia","SS8CG1"),
("What is the role of Georgia's General Assembly?",["Make state laws","Interpret all federal laws","Run local schools directly","Command foreign armies"],"Make state laws","SS8CG2")],
"economics":[("Which industry is especially important to Georgia's economy?",["Agriculture, logistics, film, and manufacturing","Whaling only","Gold mining only","Fishing only"],"Agriculture, logistics, film, and manufacturing","SS8E1")],
"culture":[("How did the civil rights movement affect Georgia?",["It challenged segregation and expanded civil rights","It restored colonial rule","It ended elections","It removed Atlanta"],"It challenged segregation and expanded civil rights","SS8H11")]},
}

def now_text(): return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
def db():
    c=sqlite3.connect(DATABASE,timeout=30); c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); c.execute("PRAGMA journal_mode=WAL"); return c
def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL COLLATE NOCASE,age INTEGER NOT NULL,grade_level INTEGER NOT NULL,current_difficulty INTEGER NOT NULL DEFAULT 1,diagnostic_complete INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(name,age));
        CREATE TABLE IF NOT EXISTS test_sessions(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER NOT NULL,game_name TEXT NOT NULL,theme_key TEXT NOT NULL,theme_name TEXT NOT NULL,topic TEXT NOT NULL,standard_code TEXT NOT NULL,mode TEXT NOT NULL,grade_level INTEGER NOT NULL,starting_difficulty INTEGER NOT NULL,ending_difficulty INTEGER NOT NULL,questions_attempted INTEGER NOT NULL,questions_correct INTEGER NOT NULL,raw_percent REAL NOT NULL,letter_grade TEXT NOT NULL,mastery_score REAL NOT NULL,mastery_status TEXT NOT NULL,seconds REAL NOT NULL,average_seconds REAL NOT NULL,timestamp TEXT NOT NULL,federation_version TEXT NOT NULL DEFAULT '1.0',FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS test_answers(id INTEGER PRIMARY KEY AUTOINCREMENT,session_id INTEGER NOT NULL,question_number INTEGER NOT NULL,topic TEXT NOT NULL,difficulty INTEGER NOT NULL,prompt TEXT NOT NULL,expected_answer TEXT NOT NULL,submitted_answer TEXT NOT NULL,is_correct INTEGER NOT NULL,seconds REAL NOT NULL,standard_code TEXT NOT NULL,FOREIGN KEY(session_id) REFERENCES test_sessions(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        """)
        pin=os.environ.get("GA_SOCIAL_PARENT_PIN","2468")
        c.execute("INSERT INTO settings(key,value) VALUES('parent_pin_hash',?) ON CONFLICT(key) DO NOTHING",(generate_password_hash(pin),))
def letter(p): return "A" if p>=90 else "B" if p>=80 else "C" if p>=70 else "D" if p>=60 else "F"
def expected(g): return max(1,min(5,g-3))
def status(m,d,g):
    e=expected(g)
    if d<e-1:return "Building prerequisite social studies skills"
    if m<60:return "Needs targeted review"
    if d<e:return "Approaching grade-level mastery"
    if m>=90 and d>e:return "Exceeding grade-level expectations"
    return "Meeting grade-level expectations" if m>=75 else "Developing grade-level mastery"
def make_question(grade, topic, difficulty, used_prompts=None):
    used_prompts = set(used_prompts or [])

    if topic == "mixed_review":
        items = []

        for review_topic in (
            "geography",
            "history",
            "civics",
            "economics",
            "culture",
        ):
            for item in BANK[grade].get(review_topic, []):
                items.append((review_topic, item))
    else:
        items = [
            (topic, item)
            for item in (
                BANK[grade].get(topic)
                or BANK[grade]["history"]
            )
        ]

    unused_items = [
        item
        for item in items
        if item[1][0] not in used_prompts
    ]

    # Only repeat after every available question has been used.
    selection_pool = unused_items or items

    selected_topic, selected = random.choice(selection_pool)
    prompt, choices, answer, standard = selected

    shuffled_choices = choices[:]
    random.shuffle(shuffled_choices)

    return {
        "topic": selected_topic,
        "prompt": prompt,
        "choices": shuffled_choices,
        "answer": answer,
        "standard": standard,
    }
def parent_required(fn):
    @wraps(fn)
    def wrap(*a,**k):
        if not session.get("parent_authenticated"): return redirect(url_for("parent_login",next=request.path))
        return fn(*a,**k)
    return wrap

@app.route("/")
def home(): return render_template("home.html",themes=THEMES,scope=GRADE_SCOPE)
@app.route("/student",methods=["GET","POST"])
def student():
    if request.method=="POST":
        name=request.form.get("name","").strip()
        try: age=int(request.form["age"]); grade=int(request.form["grade_level"])
        except: flash("Enter a valid age and grade.","error"); return render_template("student.html")
        if not name or not(5<=age<=19) or grade not in GRADE_SCOPE:
            flash("This version supports Grades 3 through 8.","error"); return render_template("student.html")
        with db() as c:
            row=c.execute("SELECT * FROM students WHERE name=? COLLATE NOCASE AND age=?",(name,age)).fetchone()
            if row: sid=row["id"]; c.execute("UPDATE students SET grade_level=?,updated_at=? WHERE id=?",(grade,now_text(),sid))
            else:
                cur=c.execute("INSERT INTO students(name,age,grade_level,current_difficulty,diagnostic_complete,created_at,updated_at) VALUES(?,?,?,?,0,?,?)",(name,age,grade,expected(grade),now_text(),now_text())); sid=cur.lastrowid
        session.clear(); session["student_id"]=sid; return redirect(url_for("tests"))
    return render_template("student.html")
@app.route("/tests")
def tests():
    sid=session.get("student_id")
    if not sid:return redirect(url_for("student"))
    with db() as c:s=c.execute("SELECT * FROM students WHERE id=?",(sid,)).fetchone()
    return render_template("tests.html",student=s,themes=THEMES,scope=GRADE_SCOPE[s["grade_level"]])
@app.post("/start/<key>")
def start(key):
    if key not in THEMES:abort(404)
    sid=session.get("student_id")
    with db() as c:s=c.execute("SELECT * FROM students WHERE id=?",(sid,)).fetchone()
    mode="diagnostic" if not s["diagnostic_complete"] else "test"
    session["test"]={"key":key,"topic":THEMES[key]["topic"],"mode":mode,"grade":s["grade_level"],"start_diff":s["current_difficulty"],"diff":s["current_difficulty"],"total":12 if mode=="diagnostic" else 10,"current":0,"correct":0,"answers":[],"used_prompts":[],"started":time.time(),"qstarted":time.time()}
    return redirect(url_for("question"))
@app.route("/question",methods=["GET","POST"])
def question():
    t=session.get("test")
    if not t:return redirect(url_for("tests"))
    feedback=None
    if request.method=="POST":
        sub=request.form.get("answer",""); elapsed=max(.1,time.time()-t["qstarted"]); q=t["question"]; ok=sub==q["answer"]
        if ok:t["correct"]+=1
        t["answers"].append({
            "n": t["current"] + 1,
            "topic": q["topic"],
            "diff": t["diff"],
            "prompt": q["prompt"],
            "expected": q["answer"],
            "submitted": sub,
            "ok": ok,
            "seconds": round(elapsed, 2),
            "standard": q["standard"],
        })

        # Remove the answered question so the next one can be generated.
        t.pop("question", None)

        t["current"] += 1
        recent = t["answers"][-3:]
        if len(recent)==3 and all(x["ok"] for x in recent):t["diff"]=min(5,t["diff"]+1)
        elif len(recent)==3 and sum(x["ok"] for x in recent)<=1:t["diff"]=max(1,t["diff"]-1)
        if t["current"]>=t["total"]:session["test"]=t;return redirect(url_for("finish"))
        feedback="Correct!" if ok else f"Correct answer: {q['answer']}"
    # Keep the same question if the browser page is refreshed.
    if "question" not in t:
        t["question"] = make_question(
            t["grade"],
            t["topic"],
            t["diff"],
            t.get("used_prompts", []),
        )

        t.setdefault("used_prompts", []).append(
            t["question"]["prompt"]
        )

        t["qstarted"] = time.time()

    session["test"] = t

    return render_template(
        "question.html",
        test=t,
        theme=THEMES[t["key"]],
        feedback=feedback,
    )
@app.route("/finish")
def finish():
    t=session.get("test");sid=session.get("student_id")
    if t.get("saved"):return redirect(url_for("result",rid=t["saved"]))
    raw=round(t["correct"]/t["total"]*100,1);secs=round(time.time()-t["started"],1);avg=round(secs/t["total"],2)
    avgd=sum(a["diff"] for a in t["answers"])/t["total"]; mastery=round(max(0,min(100,raw*.65+(avgd/5*100)*.2+max(0,100-max(0,avg-15)*2)*.15)),1)
    with db() as c:
        s=c.execute("SELECT * FROM students WHERE id=?",(sid,)).fetchone();standards=",".join(sorted(set(a["standard"] for a in t["answers"])))
        cur=c.execute("""INSERT INTO test_sessions(student_id,game_name,theme_key,theme_name,topic,standard_code,mode,grade_level,starting_difficulty,ending_difficulty,questions_attempted,questions_correct,raw_percent,letter_grade,mastery_score,mastery_status,seconds,average_seconds,timestamp) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(sid,APP_NAME,t["key"],THEMES[t["key"]]["name"],t["topic"],standards,t["mode"],s["grade_level"],t["start_diff"],t["diff"],t["total"],t["correct"],raw,letter(raw),mastery,status(mastery,t["diff"],s["grade_level"]),secs,avg,now_text()))
        rid=cur.lastrowid
        for a in t["answers"]:c.execute("INSERT INTO test_answers(session_id,question_number,topic,difficulty,prompt,expected_answer,submitted_answer,is_correct,seconds,standard_code) VALUES(?,?,?,?,?,?,?,?,?,?)",(rid,a["n"],a["topic"],a["diff"],a["prompt"],a["expected"],a["submitted"],int(a["ok"]),a["seconds"],a["standard"]))
        c.execute("UPDATE students SET current_difficulty=?,diagnostic_complete=CASE WHEN ?='diagnostic' THEN 1 ELSE diagnostic_complete END,updated_at=? WHERE id=?",(t["diff"],t["mode"],now_text(),sid))
    t["saved"]=rid;session["test"]=t;return redirect(url_for("result",rid=rid))
@app.route("/result/<int:rid>")
def result(rid):
    with db() as c:
        r=c.execute("SELECT ts.*,s.name,s.age FROM test_sessions ts JOIN students s ON s.id=ts.student_id WHERE ts.id=?",(rid,)).fetchone()
        a=c.execute("SELECT * FROM test_answers WHERE session_id=? ORDER BY question_number",(rid,)).fetchall()
    return render_template("result.html",result=r,answers=a)
@app.route("/parent/login",methods=["GET","POST"])
def parent_login():
    if request.method=="POST":
        with db() as c:p=c.execute("SELECT value FROM settings WHERE key='parent_pin_hash'").fetchone()
        if p and check_password_hash(p["value"],request.form.get("pin","")):session["parent_authenticated"]=True;return redirect(url_for("parent"))
        flash("Incorrect PIN.","error")
    return render_template("parent_login.html")
@app.route("/parent")
@parent_required
def parent():
    with db() as c:
        summaries=c.execute("""SELECT s.id,s.name,s.age,s.grade_level,s.current_difficulty,COUNT(ts.id) tests_taken,ROUND(AVG(ts.raw_percent),1) average_score,ROUND(AVG(ts.mastery_score),1) average_mastery FROM students s LEFT JOIN test_sessions ts ON ts.student_id=s.id GROUP BY s.id ORDER BY s.name""").fetchall()
        results=c.execute("""SELECT ts.*,s.name FROM test_sessions ts JOIN students s ON s.id=ts.student_id ORDER BY ts.id DESC LIMIT 250""").fetchall()
    return render_template("parent.html",summaries=summaries,results=results)
@app.route("/parent/logout")
def logout():session.pop("parent_authenticated",None);return redirect(url_for("home"))
@app.route("/parent/export")
@parent_required
def export():
    headers=["student_name","student_age","grade_level","starting_difficulty","ending_difficulty","game_name","theme_name","topic","standard_code","mode","questions_attempted","questions_correct","raw_percent","letter_grade","mastery_score","mastery_status","seconds","average_seconds","timestamp","federation_version"]
    with db() as c:rows=c.execute("""SELECT s.name student_name,s.age student_age,ts.grade_level,ts.starting_difficulty,ts.ending_difficulty,ts.game_name,ts.theme_name,ts.topic,ts.standard_code,ts.mode,ts.questions_attempted,ts.questions_correct,ts.raw_percent,ts.letter_grade,ts.mastery_score,ts.mastery_status,ts.seconds,ts.average_seconds,ts.timestamp,ts.federation_version FROM test_sessions ts JOIN students s ON s.id=ts.student_id ORDER BY ts.id DESC""").fetchall()
    out=io.StringIO();w=csv.writer(out);w.writerow(headers)
    for r in rows:w.writerow([r[h] for h in headers])
    b=io.BytesIO(out.getvalue().encode());b.seek(0);return send_file(b,as_attachment=True,download_name="ga_social_studies_results.csv",mimetype="text/csv")
@app.route("/health")
def health():return jsonify({"ok":True,"app":APP_NAME,"database":str(DATABASE),"grades":[3,4,5,6,7,8]})
@app.route("/federation/manifest")
def manifest():return jsonify({"schema_version":"1.0","game_slug":APP_SLUG,"game_name":APP_NAME,"database_path":str(DATABASE),"students_table":"students","sessions_table":"test_sessions","answers_table":"test_answers","grades_supported":[3,4,5,6,7,8],"read_only":True})
init_db()
if __name__=="__main__":app.run(host="127.0.0.1",port=int(os.environ.get("GA_SOCIAL_PORT","5085")),debug=os.environ.get("FLASK_DEBUG")=="1")
