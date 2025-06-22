let currentStep = 1;
const totalSteps = 3;

function updateProgress() {
    const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
    document.getElementById('progressFill').style.width = `${progress}%`;
    console.log(`Progreso actualizado: ${progress}%`);
}

function showStep(step) {
    console.log(`Mostrando paso ${step}`);
    document.querySelectorAll('.form-step').forEach((s, index) => {
        const isActive = index + 1 === step;
        s.classList.toggle('active', isActive);
        console.log(`Paso ${index + 1} activo: ${isActive}`);
    });
    updateProgress();
    updateNavigation();
}

function nextStep(current) {
    console.log(`Intentando avanzar desde el paso ${current}`);
    if (validateStep(current)) {
        console.log(`Paso ${current} validado, avanzando a ${current + 1}`);
        currentStep++;
        if (currentStep > totalSteps) currentStep = totalSteps;
        showStep(currentStep);
    } else {
        console.log(`Paso ${current} no válido, no se puede avanzar`);
    }
}

function previousStep(current) {
    console.log(`Retrocediendo desde el paso ${current}`);
    currentStep--;
    if (currentStep < 1) currentStep = 1;
    showStep(currentStep);
}

function updateNavigation() {
    const prevButtons = document.querySelectorAll('.nav-button.secondary');
    const nextButtons = document.querySelectorAll('.nav-button.primary:not([type="submit"])');
    const submitButton = document.querySelector('.nav-button.primary[type="submit"]');

    prevButtons.forEach(button => {
        button.disabled = currentStep === 1;
        console.log(`Botón anterior ${button.id} deshabilitado: ${button.disabled}`);
    });
    nextButtons.forEach((button, index) => {
        if (index === currentStep - 1) {
            button.disabled = !validateStep(currentStep);
            console.log(`Botón siguiente ${button.id} deshabilitado: ${button.disabled}`);
        }
    });
    if (submitButton) {
        submitButton.disabled = !validateStep(currentStep);
        console.log(`Botón submit deshabilitado: ${submitButton.disabled}`);
    }
}

function validateStep(step) {
    let isValid = true;
    const inputs = document.querySelector(`.form-step[data-step="${step}"] .form-grid`).querySelectorAll('input, select');
    console.log(`Validando paso ${step}, encontrados ${inputs.length} inputs`);

    inputs.forEach(input => {
        const group = input.closest('.input-group');
        const errorMsg = group.querySelector('.error-message');
        group.classList.remove('error');

        if (input.type === 'number') {
            const min = parseFloat(input.min);
            const max = parseFloat(input.max);
            const value = input.value !== '' ? parseFloat(input.value) : NaN;
            if (input.required && (input.value === '' || isNaN(value) || value < min || value > max)) {
                group.classList.add('error');
                isValid = false;
                console.log(`Entrada inválida: ${input.id}, valor: ${input.value}, min: ${min}, max: ${max}`);
            }
        } else if (input.type === 'select-one' && input.required && !input.value) {
            group.classList.add('error');
            isValid = false;
            console.log(`Selección inválida: ${input.id}, valor: ${input.value}`);
        }
    });

    console.log(`Paso ${step} es ${isValid ? 'válido' : 'inválido'}`);
    return isValid;
}

document.getElementById('laptopForm').addEventListener('submit', function(e) {
    e.preventDefault();

    if (!validateStep(3)) {
        alert('Por favor, corrige los errores en el formulario antes de continuar.');
        return;
    }

    console.log('Formulario enviado');
    document.getElementById('loadingDisplay').classList.add('show');
    document.getElementById('priceDisplay').classList.remove('show');
    document.getElementById('errorDisplay').classList.remove('show');

    const formData = new FormData(this);
    const formDataObject = Object.fromEntries(formData.entries());
    console.log('Datos enviados al servidor:', formDataObject);

    fetch('/predict', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Respuesta del servidor (estado):', response.status, response.statusText);
        return response.json();
    })
    .then(data => {
        console.log('Respuesta del servidor (datos):', data);
        document.getElementById('loadingDisplay').classList.remove('show');
        if (data.error) {
            document.getElementById('errorMessage').textContent = data.error;
            document.getElementById('errorDisplay').classList.add('show');
            console.error('Error en la predicción:', data.error);
        } else {
            document.getElementById('priceAmount').textContent = `€${data.prediction.toFixed(2)}`;
            document.getElementById('priceDisplay').classList.add('show');

            const summaryContent = document.getElementById('summaryContent');
            summaryContent.innerHTML = '';
            for (let [key, value] of formData.entries()) {
                if (value) {
                    summaryContent.innerHTML += `
                        <div class="summary-item">
                            <span class="summary-label">${key.replace('_', ' ').toUpperCase()}</span>
                            <span class="summary-value">${value}</span>
                        </div>
                    `;
                }
            }
            document.getElementById('summaryCard').style.display = 'block';
            console.log('Predicción exitosa:', data.prediction);
        }
    })
    .catch(error => {
        console.error('Error en la solicitud fetch:', error.message);
        document.getElementById('loadingDisplay').classList.remove('show');
        document.getElementById('errorMessage').textContent = 'Error en la conexión. Intenta de nuevo.';
        document.getElementById('errorDisplay').classList.add('show');
    });
});

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM cargado, inicializando paso 1');
    showStep(currentStep);
    document.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('input', () => {
            console.log(`Entrada modificada: ${input.id}, valor: ${input.value}`);
            validateStep(currentStep);
            updateNavigation();
        });
        input.addEventListener('change', () => {
            console.log(`Cambio detectado: ${input.id}, valor: ${input.value}`);
            validateStep(currentStep);
            updateNavigation();
        });
    });

    document.getElementById('nextStep1').addEventListener('click', () => {
        console.log('Botón nextStep1 clicado');
        nextStep(1);
    });
    document.getElementById('prevStep2').addEventListener('click', () => {
        console.log('Botón prevStep2 clicado');
        previousStep(2);
    });
    document.getElementById('nextStep2').addEventListener('click', () => {
        console.log('Botón nextStep2 clicado');
        nextStep(2);
    });
    document.getElementById('prevStep3').addEventListener('click', () => {
        console.log('Botón prevStep3 clicado');
        previousStep(3);
    });
});