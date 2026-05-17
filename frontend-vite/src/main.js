// @ts-nocheck
// ==================== VARIABLES GLOBALES ====================
let datosFinales = {};
let statusEl = null;
let startBtn = null;
let idEditando = null;

// ==================== HABLAR ====================
function hablar(texto) {
  return new Promise(resolve => {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = "es-MX";

    if (statusEl) {
      statusEl.innerText = "🗣️ HABLANDO...";
      statusEl.className = "status speaking";
    }

    u.onend = () => setTimeout(resolve, 800);
    window.speechSynthesis.speak(u);
  });
}

// ==================== ESCUCHAR CON WHISPER ====================
async function escucharCampo() {
  if (!statusEl) return "";

  statusEl.innerText = "🎤 ESCUCHANDO... (habla ahora)";
  statusEl.className = "status listening";

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    let chunks = [];

    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.start();

    await new Promise(r => setTimeout(r, 6000)); // 6 segundos

    mediaRecorder.stop();
    await new Promise(resolve => { mediaRecorder.onstop = resolve; });

    const audioBlob = new Blob(chunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append("audio", audioBlob, "voz.wav");

    statusEl.innerText = "🧠 Procesando con Whisper...";

    const res = await fetch("http://127.0.0.1:5000/api/voz", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    stream.getTracks().forEach(track => track.stop());

    return data.texto?.trim() || "";

  } catch (error) {
    console.error("❌ Error en voz:", error);
    return "";
  }
}

// ==================== PREGUNTAR ====================
async function preguntar(id, pregunta) {
  let ok = false;
  while (!ok) {
    await hablar(pregunta);
    await new Promise(r => setTimeout(r, 800));

    let respuesta = await escucharCampo();

    if (!respuesta) {
      await hablar("No te entendí, intenta de nuevo");
      continue;
    }

    const label = document.getElementById('labelEntendido');
    const confirmBox = document.getElementById('confirmZone');

    if (label) label.innerText = `¿Es correcto?: "${respuesta}"`;
    if (confirmBox) confirmBox.style.display = 'block';

    const esCorrecto = await new Promise(resolve => {
      document.getElementById('btnSi').onclick = () => resolve(true);
      document.getElementById('btnNo').onclick = () => resolve(false);
    });

    if (confirmBox) confirmBox.style.display = 'none';

    if (esCorrecto) {
      datosFinales[id] = respuesta;
      const valorEl = document.getElementById(`v-${id}`);
      if (valorEl) valorEl.innerText = respuesta;
      ok = true;
    } else {
      await hablar("Repitamos el dato");
    }
  }
}

// ==================== INICIAR ====================
async function iniciar() {
  datosFinales = {};

  const flujo = [
    {id: 'nombre', q: 'Nombre completo del paciente'},
    {id: 'edad', q: '¿Qué edad tiene?'},
    {id: 'telefono', q: 'Número de teléfono'},
    {id: 'direccion', q: 'Dirección del paciente'},
    {id: 'sexo', q: 'Sexo del paciente'},
    {id: 'tipo_sangre', q: 'Tipo de sangre'},
    {id: 'peso', q: 'Peso aproximado'},
    {id: 'altura', q: 'Altura'},
    {id: 'presion_arterial', q: 'Presión arterial'},
    {id: 'alergias', q: '¿Tiene alergias importantes?'},
    {id: 'antecedentes', q: 'Antecedentes médicos relevantes'},
    {id: 'fecha_consulta', q: 'Fecha de hoy'},
    {id: 'doctor', q: 'Nombre del doctor'},
    {id: 'enfermedad', q: 'Describa los síntomas principales'},
    {id: 'diagnostico', q: '¿Cuál es el diagnóstico?'},
    {id: 'observaciones', q: 'Observaciones adicionales'},
    {id: 'medicamento', q: 'Medicamento recetado'},
    {id: 'proxima_cita', q: 'Próxima cita'}
  ];

  for (let f of flujo) {
    await preguntar(f.id, f.q);
  }

  await hablar("Guardando información del paciente");

  try {
    await fetch('http://127.0.0.1:5000/api/guardar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datosFinales)
    });

    await hablar("Datos guardados correctamente");
    cargarTabla();
  } catch (e) {
    await hablar("Error al guardar los datos");
  }
}

// ==================== CARGAR TABLA ====================
async function cargarTabla() {
  try {
    const res = await fetch('http://127.0.0.1:5000/api/registros');
    const lista = await res.json();

    const tbody = document.getElementById('tablaBody');
    if (tbody) {
      tbody.innerHTML = lista.map(r => `
        <tr>
          <td>${r.nombre || ''}</td>
          <td>${r.edad || ''}</td>
          <td>${r.telefono || ''}</td>
          <td>${r.doctor || ''}</td>
          <td>${r.fecha_consulta || ''}</td>
          <td>
            <button onclick="editar(${r.id})">✏️</button>
            <button onclick="eliminar(${r.id})">🗑️</button>
          </td>
        </tr>
      `).join('');
    }
  } catch (error) {
    console.error("Error al cargar tabla:", error);
  }
}

// ==================== INIT ====================
window.addEventListener('DOMContentLoaded', () => {
  statusEl = document.getElementById('status');
  startBtn = document.getElementById('startBtn');

  if (startBtn) startBtn.addEventListener('click', iniciar);

  cargarTabla();
});

// Exponer funciones para los botones onclick
window.editar = editar;
window.guardarEdicion = guardarEdicion;
window.cerrarModal = cerrarModal;
window.eliminar = eliminar;
window.exportarPDF = exportarPDF;