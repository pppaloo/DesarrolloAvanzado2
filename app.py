from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = "clave_secreta_123"

DATABASE = "empleados.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nombre_completo TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            cargo TEXT NOT NULL,
            salario REAL,
            departamento TEXT,
            fecha_ingreso TEXT,
            telefono TEXT,
            email TEXT,
            usuario_id INTEGER,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def verificar_usuario(username, password):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM usuarios WHERE username = '" + username + "' AND password = '" + hash_password(password) + "'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    return user

def registrar_usuario(username, password, nombre_completo):
    try:
        conn = get_db()
        cursor = conn.cursor()
        hashed = hash_password(password)
        cursor.execute(
            "INSERT INTO usuarios (username, password, nombre_completo) VALUES (?, ?, ?)",
            (username, hashed, nombre_completo)
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("lista_empleados"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user = verificar_usuario(username, password)
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["nombre"] = user["nombre_completo"]
            flash("Inicio de sesion exitoso", "success")
            return redirect(url_for("lista_empleados"))
        else:
            flash("Usuario o contrasena incorrectos", "danger")
    
    return render_template("login.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        nombre = request.form["nombre_completo"]
        
        if len(password) < 4:
            flash("La contrasena debe tener al menos 4 caracteres", "warning")
            return redirect(url_for("registro"))
        
        if registrar_usuario(username, password, nombre):
            flash("Usuario registrado correctamente. Ahora puede iniciar sesion.", "success")
            return redirect(url_for("login"))
        else:
            flash("Error al registrar usuario. El nombre de usuario ya existe.", "danger")
    
    return render_template("registro.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesion cerrada correctamente", "info")
    return redirect(url_for("login"))

@app.route("/empleados")
def lista_empleados():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM empleados WHERE usuario_id = ?", (session["user_id"],))
    empleados = cursor.fetchall()
    conn.close()
    
    return render_template("lista_empleados.html", empleados=empleados)

@app.route("/empleados/nuevo", methods=["GET", "POST"])
def nuevo_empleado():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        cargo = request.form["cargo"]
        salario = request.form["salario"]
        departamento = request.form["departamento"]
        fecha_ingreso = request.form["fecha_ingreso"]
        telefono = request.form["telefono"]
        email = request.form["email"]
        
        try:
            salario_float = float(salario)
        except:
            salario_float = 0.0
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO empleados 
            (nombre, apellido, cargo, salario, departamento, fecha_ingreso, telefono, email, usuario_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (nombre, apellido, cargo, salario_float, departamento, fecha_ingreso, telefono, email, session["user_id"])
        )
        conn.commit()
        conn.close()
        
        flash("Empleado registrado exitosamente", "success")
        return redirect(url_for("lista_empleados"))
    
    return render_template("form_empleado.html", empleado=None, titulo="Nuevo Empleado")

@app.route("/empleados/editar/<int:id>", methods=["GET", "POST"])
def editar_empleado(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        cargo = request.form["cargo"]
        salario = request.form["salario"]
        departamento = request.form["departamento"]
        fecha_ingreso = request.form["fecha_ingreso"]
        telefono = request.form["telefono"]
        email = request.form["email"]
        
        try:
            salario_float = float(salario)
        except:
            salario_float = 0.0
        
        cursor.execute(
            """UPDATE empleados 
            SET nombre=?, apellido=?, cargo=?, salario=?, departamento=?, 
            fecha_ingreso=?, telefono=?, email=?
            WHERE id=? AND usuario_id=?""",
            (nombre, apellido, cargo, salario_float, departamento, 
             fecha_ingreso, telefono, email, id, session["user_id"])
        )
        conn.commit()
        conn.close()
        
        flash("Empleado actualizado correctamente", "success")
        return redirect(url_for("lista_empleados"))
    
    cursor.execute("SELECT * FROM empleados WHERE id=? AND usuario_id=?", (id, session["user_id"]))
    empleado = cursor.fetchone()
    conn.close()
    
    if not empleado:
        flash("Empleado no encontrado", "danger")
        return redirect(url_for("lista_empleados"))
    
    return render_template("form_empleado.html", empleado=empleado, titulo="Editar Empleado")

@app.route("/empleados/eliminar/<int:id>")
def eliminar_empleado(id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM empleados WHERE id=? AND usuario_id=?", (id, session["user_id"]))
    conn.commit()
    conn.close()
    
    flash("Empleado eliminado correctamente", "success")
    return redirect(url_for("lista_empleados"))

@app.route("/buscar")
def buscar_empleados():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    termino = request.args.get("q", "")
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM empleados WHERE usuario_id = " + str(session["user_id"])
    if termino:
        query += " AND (nombre LIKE '%" + termino + "%' OR apellido LIKE '%" + termino + "%' OR cargo LIKE '%" + termino + "%')"
    
    cursor.execute(query)
    empleados = cursor.fetchall()
    conn.close()
    
    return render_template("lista_empleados.html", empleados=empleados)

@app.route("/perfil")
def perfil():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id=?", (session["user_id"],))
    usuario = cursor.fetchone()
    conn.close()
    
    return render_template("perfil.html", usuario=usuario)

@app.route("/estadisticas")
def estadisticas():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM empleados WHERE usuario_id=?", (session["user_id"],))
    total = cursor.fetchone()["total"]
    
    cursor.execute("SELECT AVG(salario) as promedio FROM empleados WHERE usuario_id=?", (session["user_id"],))
    promedio = cursor.fetchone()["promedio"]
    
    cursor.execute("SELECT departamento, COUNT(*) as cantidad FROM empleados WHERE usuario_id=? GROUP BY departamento", (session["user_id"],))
    por_departamento = cursor.fetchall()
    
    cursor.execute("SELECT cargo, COUNT(*) as cantidad FROM empleados WHERE usuario_id=? GROUP BY cargo", (session["user_id"],))
    por_cargo = cursor.fetchall()
    
    conn.close()
    
    return render_template("estadisticas.html", 
                         total=total, 
                         promedio=promedio,
                         por_departamento=por_departamento,
                         por_cargo=por_cargo)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
