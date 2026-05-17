from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import whisper
import os

app = Flask(__name__)
CORS(app)

# ==================== CONFIGURACIÓN ====================
DB_USER = "root"
DB_PASS = ""          # Pon tu contraseña si tienes
DB_HOST = "localhost"
DB_NAME = "progweb2025"

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False  # Cambia a True solo para debug
)

Base = declarative_base()
Session = sessionmaker(bind=engine)

# ==================== WHISPER ====================
print("🧠 Cargando modelo Whisper...")
modelo = whisper.load_model("base")
print("✅ Whisper cargado")

# ==================== MODELO ====================
class Formulario(Base):
    __tablename__ = 'formularios_nuevo'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100))
    edad = Column(String(10))
    telefono = Column(String(15))
    direccion = Column(String(150))
    sexo = Column(String(10))
    tipo_sangre = Column(String(5))
    peso = Column(String(10))
    altura = Column(String(10))
    presion_arterial = Column(String(15))
    alergias = Column(Text)
    antecedentes = Column(Text)
    fecha_consulta = Column(String(50))
    doctor = Column(String(100))
    enfermedad = Column(Text)
    diagnostico = Column(Text)
    observaciones = Column(Text)
    medicamento = Column(Text)
    proxima_cita = Column(String(50))
    fecha_registro = Column(DateTime, default=datetime.utcnow)

# Crear tabla si no existe
Base.metadata.create_all(engine)

# ==================== SERIALIZADOR ====================
def serialize(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

# ==================== RUTAS ====================

@app.route("/")
def home():
    return "✅ Servidor Flask activo - Proyecto Voz IA"

@app.route("/api/registros", methods=["GET"])
def registros():
    db = Session()
    try:
        data = db.query(Formulario)\
                 .order_by(Formulario.id.desc())\
                 .all()
        return jsonify([serialize(r) for r in data])
    except Exception as e:
        print("❌ ERROR GET:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route("/api/guardar", methods=["POST"])
def guardar():
    db = Session()
    try:
        data = request.get_json()

        nuevo = Formulario(
            nombre=data.get('nombre') or "No especificado",
            edad=data.get('edad') or "No especificado",
            telefono=data.get('telefono') or "No especificado",
            direccion=data.get('direccion') or "No especificado",
            sexo=data.get('sexo') or "No especificado",
            tipo_sangre=data.get('tipo_sangre') or "No especificado",
            peso=data.get('peso') or "No especificado",
            altura=data.get('altura') or "No especificado",
            presion_arterial=data.get('presion_arterial') or "No especificado",
            alergias=data.get('alergias') or "No especificado",
            antecedentes=data.get('antecedentes') or "No especificado",
            fecha_consulta=data.get('fecha_consulta') or "No especificado",
            doctor=data.get('doctor') or "No especificado",
            enfermedad=data.get('enfermedad') or "No especificado",
            diagnostico=data.get('diagnostico') or "No especificado",
            observaciones=data.get('observaciones') or "No especificado",
            medicamento=data.get('medicamento') or "No especificado",
            proxima_cita=data.get('proxima_cita') or "No especificado",
            fecha_registro=datetime.utcnow()
        )

        db.add(nuevo)
        db.commit()

        return jsonify({"status": "ok", "id": nuevo.id})

    except Exception as e:
        db.rollback()
        print("❌ ERROR POST:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route("/api/editar/<int:id>", methods=["PUT"])
def editar(id):
    db = Session()
    try:
        data = request.get_json()
        reg = db.get(Formulario, id)

        if not reg:
            return jsonify({"error": "Registro no encontrado"}), 404

        for key, value in data.items():
            if hasattr(reg, key) and key != 'id':
                setattr(reg, key, value if value else "No especificado")

        db.commit()
        return jsonify({"status": "editado"})

    except Exception as e:
        db.rollback()
        print("❌ ERROR EDIT:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route("/api/eliminar/<int:id>", methods=["DELETE"])
def eliminar(id):
    db = Session()
    try:
        reg = db.query(Formulario).filter(Formulario.id == id).first()
        if not reg:
            return jsonify({"error": "Registro no encontrado"}), 404

        db.delete(reg)
        db.commit()
        return jsonify({"status": "eliminado"})

    except Exception as e:
        db.rollback()
        print("❌ ERROR DELETE:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route("/api/voz", methods=["POST"])
def voz():
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No se recibió audio"}), 400

        archivo = request.files["audio"]
        ruta = "temp_audio.wav"
        archivo.save(ruta)

        resultado = modelo.transcribe(ruta, language="es")
        texto = resultado["text"].strip()

        if os.path.exists(ruta):
            os.remove(ruta)

        return jsonify({"texto": texto})

    except Exception as e:
        print("❌ ERROR WHISPER:", e)
        return jsonify({"error": str(e)}), 500

# ==================== SERVIR FRONTEND ====================
from flask import send_from_directory
import os

# Servir archivos estáticos del frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join('dist', path)):
        return send_from_directory('dist', path)
    else:
        return send_from_directory('dist', 'index.html')
# ==================== INICIO ====================
if __name__ == "__main__":
    print("🚀 Servidor corriendo en http://127.0.0.1:5000")
    app.run(debug=True, port=5000)